import sys
import re
import os
import subprocess

import requests
from unidecode import unidecode


class SledovaniTV:
    def __init__(self, args):
        self.arg = " ".join(args)

        self.playlist = {}
        self.pvr = {}

        self.player = "mpv"
        self.phpsessid = ""

    def download_playlist(self):
        r = requests.get(
            "https://sledovanitv.cz/api/playlist",
            params={"PHPSESSID": self.phpsessid},
        )

        for i in r.json()["channels"]:
            if i["locked"] == "none":
                self.playlist.update({unidecode(i["name"]): i["url"]})

    def download_pvr(self):
        r = requests.get(
            "https://sledovanitv.cz/api/get-pvr",
            params={"PHPSESSID": self.phpsessid},
        )

        for i in r.json()["records"]:
            self.pvr.update({i["id"]: i["title"]})

    def get_pvr_record(self, rid):
        r = requests.get(
            "https://sledovanitv.cz/api/record-timeshift",
            params={"PHPSESSID": self.phpsessid, "recordId": rid},
        )

        return r.json()["url"]

    def find_channels(self):
        data = []
        for c in self.playlist:
            mobj = re.search(self.arg, c, re.IGNORECASE)

            if mobj:
                data.append(c)

        return data

    def select_number(self, size):
        sel = input("Výběr: ")

        try:
            sel = int(sel)
        except ValueError:
            print("Pouze čísla!")
            return self.select_number(size)

        if sel < 0 or sel > size:
            print("Mimo rozsah!")
            return self.select_number(size)
        else:
            return sel

    def run(self):
        if "--pvr" in self.arg:
            self.download_pvr()

            pvr = list(self.pvr)

            for i, k in enumerate(pvr):
                print(f"{i+1}) {self.pvr[k]}")
            print("0) Konec")

            c = self.select_number(len(pvr))

            if c == 0:
                sys.exit(1)

            url = self.get_pvr_record(pvr[c - 1])

            subprocess.run([self.player, url])

            sys.exit(0)

        self.download_playlist()

        ret = self.find_channels()

        size = len(ret)
        if size == 0:
            print("Kanál nebyl nalezen!")
            sys.exit(1)

        elif size == 1:
            subprocess.run([self.player, self.playlist[ret[0]]])
        else:
            print("Nalezeno více kanálů:")
            for i, k in enumerate(ret):
                print(f"{i+1}) {k}")
            print("0) Konec")

            c = self.select_number(size)

            if c == 0:
                sys.exit(1)

            subprocess.run([self.player, self.playlist[ret[c - 1]]])


if __name__ == "__main__":
    s = SledovaniTV(sys.argv[1:])
    s.run()
