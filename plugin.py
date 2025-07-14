from plugin_zen import PLUGIN
from urllib.parse import urlencode
import requests


def request(url, params={"platform": "apps"}):
    return requests.get(url, params=params).json()


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
    directs = request("https://api-mobile.yatta.francetv.fr/generic/directs").get(
        "items", []
    )
    for direct in directs:
        channel = direct.get("channel") or direct.get("partner") or {}
        si_id = channel.get("si_id")
        if si_id:
            item = PLUGIN.add_item_by_mode("", "play", si_id)
            update_item(item, channel)


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
