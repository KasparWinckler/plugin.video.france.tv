from plugin_zen import PLUGIN
from urllib.parse import urlencode
import requests


def request(url, params={"platform": "apps"}):
    return requests.get(url, params=params).json()


def get_list(url, name="items"):
    return request(url).get(name) or []


@PLUGIN.register_folder("directs")
def directs():
    contents = get_list("https://api-mobile.yatta.francetv.fr/generic/directs")
    contents = [
        content.get("channel") or content.get("partner") or content
        for content in contents
    ]
    add_contents(contents)


@PLUGIN.register_folder("categories")
def categories():
    contents = get_list(
        "http://api-front.yatta.francetv.fr/standard/publish/categories", "result"
    )
    add_contents(contents)


@PLUGIN.register_folder("collection")
def collection(id):
    contents = get_list(
        f"https://api-mobile.yatta.francetv.fr/generic/collections/{id}"
    )
    add_contents(contents)


@PLUGIN.register_folder("url")
def url(url):
    contents = get_list(url, "collections")
    add_contents(contents, url)


@PLUGIN.register_folder("url_item")
def url_item(url, label):
    contents = get_list(url, "collections")
    contents = [content for content in contents if content.get("label") == label]
    contents = contents[0].get("items") or []
    add_contents(contents)


def add_contents(contents, url=None):
    for content in contents:
        label = content.get("label")
        si_id = content.get("si_id")
        type = content.get("type")
        if url:
            item = PLUGIN.add_item_by_mode("", "url_item", url, label)
        elif si_id:
            item = PLUGIN.add_item_by_mode("", "play", si_id)
        elif type == "article":
            continue
        elif type == "collection":
            item = PLUGIN.add_item_by_mode("", "collection", str(id))
        elif type == "channel":
            item = PLUGIN.add_item_by_mode(
                "",
                "url",
                "https://api-mobile.yatta.francetv.fr/apps/channels/"
                + content["channel_url"],
            )
        elif type in ["categorie", "sous_categorie"]:
            item = PLUGIN.add_item_by_mode(
                "",
                "url",
                "https://api-mobile.yatta.francetv.fr/apps/categories/"
                + content["url_complete"],
            )
        elif type in ["event", "program"]:
            item = PLUGIN.add_item_by_mode(
                "",
                "url",
                "https://api-mobile.yatta.francetv.fr/apps/program/"
                + (content.get("program_path") or content.get("url_complete")),
            )
        else:
            print(json.dumps(content, indent=2))
            quit()
        item.setLabel(content.get("label") or content.get("title") or "")


def update_item(item, meta):
    item.setLabel(meta.get("label", ""))

    arts = {"carre": "thumb", "background_16x9": "fanart"}
    art = {}
    for image in meta.get("images", []):
        type = arts.get(image.get("type", ""))
        if type:
            art[type] = list(image.get("urls", {}).values())[-1]
    item.setArt(art)


@PLUGIN.register_folder("")
def directs():
    PLUGIN.add_item_by_mode("Directs", "directs")
    PLUGIN.add_item_by_mode("Replay", "categories")


@PLUGIN.register_playable("play")
def play(item, si_id):
    os = "ios" if PLUGIN.xbmcplugin("getSetting", "prefer_hls") == "true" else "android"

    data = request(
        "https://player.webservices.francetelevisions.fr/v1/videos/" + si_id,
        params={"country_code": "FR", "os": os},
    )

    video = data["video"]
    token = video["token"]
    url = video["url"]
    path = request(token, params={"url": url})["url"]

    headers = urlencode(
        {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.46 Mobile Safari/537.36"
        }
    )
    path = "|".join((path, headers))
    item.setPath(path)
    item.setProperty("inputstream", "inputstream.adaptive")
    # item.setProperty("inputstream.adaptive.common_headers", headers)
    item.setProperty("inputstream.adaptive.manifest_headers", headers)
    item.setProperty("inputstream.adaptive.stream_headers", headers)
    if ".mpd" in url:
        item.setMimeType("application/dash+xml")
    else:
        item.setMimeType("application/vnd.apple.mpegurl")
        license_key = "|".join(("https://simulcast-b.ftven.fr/keys/hls.key", headers))
        item.setProperty("inputstream.adaptive.license_key", license_key)

    meta = data.get("meta", {})
    image_url = meta.get("image_url", "")
    item.setArt({"fanart": image_url, "thumb": image_url})
    item.setLabel(meta.get("title", ""))
    tag = item.getVideoInfoTag()
    tag.setFirstAired(meta.get("broadcasted_at", ""))
    tag.setPlot(meta.get("description", ""))


PLUGIN.run()
