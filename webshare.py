import re

import requests
import xmltodict
from hashlib import sha1
from passlib.hash import md5_crypt


class WebshareAPIError(Exception):
    pass


class WebshareAPI:
    def __init__(self):
        self._prog = re.compile(r"webshare\.cz/#?/?file/([^/]+)")

        self._base_url = "https://webshare.cz/api"

        self._wst = ""

    @property
    def token(self):
        if self._wst == "":
            return None

        return self._wst

    @token.setter
    def token(self, value):
        if value is None:
            value = ""

        self._wst = value

    def _get_ident(self, url):
        mobj = self._prog.search(url)

        if mobj:
            return mobj.group(1)

        return None

    def _post_data(self, endpoint, data=None):
        if data is None:
            data = {"wst": self._wst}
        else:
            data.update({"wst": self._wst})

        try:
            resp = requests.post(f"{self._base_url}/{endpoint}/", data, timeout=4)
        except requests.exceptions.RequestException as e:
            raise WebshareAPIError(e)

        xml_resp = xmltodict.parse(resp.text)["response"]

        status = xml_resp["status"]
        if status != "OK":
            message = xml_resp["message"]
            raise WebshareAPIError(f"webshare.cz returned {status} - {message}")

        return xml_resp

    def _get_user_salt(self, username):
        ret = self._post_data("salt", {"username_or_email": username})
        return ret["salt"]

    def _get_file_salt(self, ident):
        ret = self._post_data("file_password_salt", {"ident": ident})
        return ret["salt"]

    def _hash_password(self, password, salt):
        md5 = md5_crypt.using(salt=salt).hash(password)
        return sha1(md5.encode()).hexdigest()

    def login(self, username, password):
        if self._wst != "":
            return

        salt = self._get_user_salt(username)

        data = {
            "username_or_email": username,
            "password": self._hash_password(password, salt),
            "keep_logged_in": 1,
        }

        ret = self._post_data("login", data)

        self._wst = ret["token"]

    def logout(self):
        if self._wst == "":
            return

        self._post_data("logout")
        self._wst = ""

    def get_file_link(self, url, password=None):
        ident = self._get_ident(url)
        if ident is None:
            raise WebshareAPIError("not a webshare.cz URL")

        data = {"ident": ident}
        if password is not None:
            salt = self._get_file_salt(ident)
            data.update({"password": self._hash_password(password, salt)})

        ret = self._post_data("file_link", data)

        return ret["link"]

    def get_file_info(self, url, password=None):
        ident = self._get_ident(url)
        if ident is None:
            raise WebshareAPIError("not a webshare.cz URL")

        data = {"ident": ident}
        if password is not None:
            salt = self._get_file_salt(ident)
            data.update({"password": self._hash_password(password, salt)})

        ret = self._post_data("file_info", data)

        return {
            "name": ret["name"],
            "desc": ret["description"],
            "type": ret["type"],
            "size": int(ret["size"]),
        }
