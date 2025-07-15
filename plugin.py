from plugin_zen import PLUGIN
import requests
import urllib


def request(url, params={"platform": "apps"}):
    return requests.get(url, params=params).json()


@PLUGIN.register_folder("")
def directs():
    contents = request("https://api-mobile.yatta.francetv.fr/generic/directs").get(
        "items", []
    )
    contents = [
        content.get("channel") or content.get("partner") or content
        for content in contents
    ]
    for content in contents:
        si_id = content.get("si_id")
        if si_id:
            item = PLUGIN.add_item_by_mode("", "play", si_id)
            update_item(item, content)


def update_item(item, metadata):
    item.setLabel(metadata.get("label") or metadata.get("title") or "")
    arts = {"carre": "thumb"}
    art = {}
    for image in metadata.get("images", []):
        type = arts.get(image.get("type", ""))
        if type:
            art[type] = list(image.get("urls", {}).values())[-1]
    item.setArt(art)


@PLUGIN.register_playable("play")
def play(item, si_id):
    os = (
        "ios"
        if PLUGIN.xbmcplugin("getSetting", "prefer_hls") == "true"
        else "androidtv"
    )

    data = request(
        "https://player.webservices.francetelevisions.fr/v1/videos/" + si_id,
        params={"country_code": "FR", "os": os},
    )

    video = data["video"]
    token = video["token"]
    url = video["url"]
    path = request(token, params={"url": url})["url"]

    headers = urllib.parse.urlencode(
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

    item.setLabel(data.get("meta", {}).get("title", ""))


PLUGIN.run()
