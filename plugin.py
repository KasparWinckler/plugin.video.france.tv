from plugin_zen import PLUGIN
import requests
import urllib


def request(url, params={"platform": "apps"}):
    return requests.get(url, params=params).json()


@PLUGIN.mode_folder("")
def home():
    PLUGIN.add_item("directs").setLabel("Directs")
    PLUGIN.add_item("replay").setLabel("Replay")


@PLUGIN.mode_folder("categorie")
def categorie(path):
    collections("https://api-mobile.yatta.francetv.fr/apps/categories/" + path)


@PLUGIN.mode_folder("replay")
def categories():
    add_contents(
        request("http://api-front.yatta.francetv.fr/standard/publish/categories").get(
            "result", []
        )
    )


@PLUGIN.mode_folder("channel")
def channel(path):
    collections("https://api-mobile.yatta.francetv.fr/apps/channels/" + path)


@PLUGIN.mode_folder("collection")
def collection(id):
    add_contents(
        request(f"https://api-mobile.yatta.francetv.fr/generic/collections/{id}").get(
            "items", []
        )
    )


@PLUGIN.mode_folder("collections")
def collections(url):
    add_contents(request(url).get("collections", []), url)


@PLUGIN.mode_folder("collections_items")
def collections_items(url, label):
    add_contents(
        [
            collection
            for collection in request(url).get("collections", [])
            if collection.get("label") == label
        ][0].get("items", [])
    )


@PLUGIN.mode_folder("directs")
def directs():
    add_contents(
        [
            direct.get("channel") or direct.get("partner") or direct
            for direct in request(
                "https://api-mobile.yatta.francetv.fr/generic/directs"
            ).get("items", [])
        ]
    )


@PLUGIN.mode_folder("program")
def program(path):
    collections("https://api-mobile.yatta.francetv.fr/apps/program/" + path)


@PLUGIN.mode_playable("play")
def play(item, si_id):
    video = (
        request(
            "https://player.webservices.francetelevisions.fr/v1/videos/" + si_id,
            params={
                "country_code": "FR",
                "os": "ios"
                if PLUGIN.xbmcplugin("getSetting", "prefer_hls").lower() == "true"
                else "androidtv",
            },
        ).get("video")
        or {}
    )
    path = request(video["token"], params={"url": video["url"]})["url"]

    headers = urllib.parse.urlencode(
        {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.46 Mobile Safari/537.36"
        }
    )
    path = "|".join((path, headers))
    item.setContentLookup(False)
    item.setPath(path)
    item.setProperty("inputstream", "inputstream.adaptive")
    item.setProperty("inputstream.adaptive.manifest_headers", headers)
    item.setProperty("inputstream.adaptive.stream_headers", headers)
    if ".mpd" in path:
        item.setMimeType("application/dash+xml")
    else:
        item.setMimeType("application/vnd.apple.mpegurl")
        license_key = "|".join(("https://simulcast-b.ftven.fr/keys/hls.key", headers))
        item.setProperty("inputstream.adaptive.license_key", license_key)


def add_contents(contents, url=None):
    for content in contents:
        si_id = content.get("si_id")
        type = content.get("type")
        if url:
            item = PLUGIN.add_item("collections_items", url, content["label"])
        elif si_id:
            item = PLUGIN.add_item("play", si_id)
        elif type == "article":
            continue
        elif type in ["categorie", "sous_categorie"]:
            item = PLUGIN.add_item("categorie", content["url_complete"])
        elif type == "channel":
            item = PLUGIN.add_item("channel", content["channel_url"])
        elif type == "collection":
            item = PLUGIN.add_item("collection", content["id"])
        elif type in ["event", "program"]:
            item = PLUGIN.add_item(
                "program",
                content.get("program_path") or content.get("url_complete"),
            )
        else:
            continue

        item.setLabel(content.get("label") or content.get("title") or "")
        arts = {"carre": "thumb"}
        art = {}
        for image in content.get("images", []):
            type = arts.get(image.get("type", ""))
            if type:
                art[type] = list(image.get("urls", {}).values())[-1]
        item.setArt(art)


PLUGIN.xbmcplugin("setContent", "videos")
PLUGIN.run()
