import os
import sys
import json
import time
import sqlite3
import subprocess
import requests


class Spotlight:
    def __init__(self, args):
        self.args = args

        self.conf_dir = os.path.join(
            os.path.expanduser("~"), ".local", "share", "spotlight"
        )
        self.conf_db = os.path.join(self.conf_dir, "spotlight.db")

        if not os.path.exists(self.conf_dir):
            print("Creating config dir")
            os.makedirs(self.conf_dir)

        self.con = sqlite3.connect(self.conf_db)
        self.cur = self.con.cursor()

        self.cur.execute("CREATE TABLE IF NOT EXISTS spotlight(name)")
        self.con.commit()

    def get_picture(self):
        print("Getting picture")
        resp = requests.get(
            "https://arc.msn.com/v3/Delivery/Placement",
            params={
                "pid": "209567",
                "fmt": "json",
                "cdm": "1",
                "lc": "en,en-US",
                "ctry": "US",
            },
            headers={"User-Agent": "WindowsShellClient/0"},
            timeout=4,
        )

        data = resp.json()["batchrsp"]["items"][0]["item"]
        item = json.loads(data)

        picture = item["ad"]["image_fullscreen_001_landscape"]["u"]
        title = item["ad"]["title_text"]["tx"]

        return title, picture

    def set_plasma_wallpaper(self, picture_path):
        subprocess.run(["plasma-apply-wallpaperimage", picture_path])

    def delete_previous(self):
        res = self.cur.execute("SELECT name FROM spotlight")
        for i in res.fetchall():
            print("Deleting", i[0])
            picture_path = os.path.join(self.conf_dir, i[0])
            if os.path.exists(picture_path):
                os.remove(picture_path)

        print("Flushing database")
        self.cur.execute("DELETE FROM spotlight")
        self.con.commit()

    def main(self):
        if "--keep" in self.args:
            print("Parameter --keep active")
        else:
            self.delete_previous()

        title, picture = self.get_picture()

        name = str(time.time()).split(".")[0] + "-" + title + ".jpg"

        resp = requests.get(picture)

        picture_path = os.path.join(self.conf_dir, name)

        with open(picture_path, "wb") as f:
            f.write(resp.content)

        self.cur.execute("INSERT INTO spotlight VALUES(?)", (name,))
        self.con.commit()
        self.con.close()

        self.set_plasma_wallpaper(picture_path)


if __name__ == "__main__":
    s = Spotlight(sys.argv[1:])
    s.main()
