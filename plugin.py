from plugin_zen import PLUGIN
from urllib.parse import urlencode
import requests


def request(url, params={}):
    return requests.get(url, params=params).json()


@PLUGIN.register_folder("")
def directs():
    directs = request(
        "https://api-mobile.yatta.francetv.fr/generic/directs",
        params={"platform": "apps"},
    ).get("items", [])
    for direct in directs:
        channel = direct.get("channel") or direct.get("partner") or {}
        si_id = channel.get("si_id")
        if si_id:
            item = PLUGIN.add_item_by_mode("", "play", si_id)
            item.setLabel(channel.get("label", ""))
            art = {}
            for image in channel.get("images", []):
                if image.get("type") == "carre":
                    urls = image.get("urls", {})
                    if urls:
                        art["thumb"] = list(urls.values())[-1]
            item.setArt(art)


@PLUGIN.register_playable("play")
def play(item, si_id):
    data = request(
        "https://player.webservices.francetelevisions.fr/v1/videos/" + si_id,
        params={"country_code": "FR", "os": "android"},
    )

    meta = data["meta"]
    item.setArt({"fanart": meta["image_url"]})
    item.setArt({"thumb": meta["image_url"]})
    item.setLabel(meta["title"])
    tag = item.getVideoInfoTag()
    tag.setFirstAired(meta["broadcasted_at"])
    tag.setPlot(meta["description"])

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


PLUGIN.run()
