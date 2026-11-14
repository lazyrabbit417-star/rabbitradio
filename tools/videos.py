"""台本の話題に、動画を付ける（Steam の公式の動画と、YouTube の動画）。

usage: python tools/videos.py episodes/2026-11-08-ja.json

話題ごとに、次の順で動画を探し、"videos": [...] を書く（最大 3 本）。
- "steam": <アプリID> があれば、Steam のストアにあるそのゲームの動画（トレーラー・プレイ動画）
    → {"hls", "poster", "name"}
- "youtube": [...] があれば、その YouTube の動画。動画の ID か URL を並べる。途中から流すときは
    {"id": "...", "start": 秒}
- どちらもなく、リンク先が BOOTH の商品なら、ショップが商品ページに載せている YouTube の動画
    （商品ページの動画の欄、なければ説明文の YouTube のリンク）
    → {"youtube", "start", "poster", "name"}

YouTube の動画は、埋めこみが許されているかを YouTube の oEmbed で確かめ、許されていないものは使わない。
導入・設定の説明の動画（タイトルに「導入」「設定」「使い方」など）は、ほかに動画がないときだけ使う。
動画は保存しない。Steam が配信している動画の URL と、YouTube の動画の ID を書くだけ（リンクカードの画像と同じ考え方）。
プレーヤーは、その話題のあいだ、左の枠の上に大きく、音なしで流す（YouTube の動画は YouTube のプレーヤーで）。
動画が見つからない話題は、いつもの枠のまま。
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36"
YT_ID = r"(?:youtube\.com/(?:watch\?(?:[^\"'\s<>]*?&)?v=|shorts/|embed/|live/)|youtu\.be/)([\w-]{11})"
MAX = 3
GUIDE = re.compile(r"導入|設定|使い方|ガイド|解説|チュートリアル|tutorial|setup|install|how to", re.I)


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def steam_videos(appid):
    d = get_json(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=jp&l=japanese").get(str(appid), {})
    ms = [m for m in ((d.get("data") or {}).get("movies") or []) if m.get("hls_h264")] if d.get("success") else []
    # Japanese ones first (by their names), then the ones the store puts forward (highlight)
    jp = lambda m: bool(re.search(r"japanese|日本語|\bJP\b|_JP|JP_|[ぁ-んァ-ヶ]", m.get("name") or "", re.I))
    ms = sorted(ms, key=lambda m: (not jp(m), not m.get("highlight")))[:MAX]
    return [{"hls": m["hls_h264"], "poster": m.get("thumbnail"), "name": m.get("name")} for m in ms]


def booth_item(n):
    for u in (n.get("url"), (n.get("link") or {}).get("url")):
        m = re.search(r"booth\.pm/(?:[a-z]{2}/)?items/(\d+)", u or "")
        if m:
            return m.group(1)
    return None


def booth_youtube(item):
    """the YouTube videos the shop put on the item page: its video section first, then links in the description"""
    d = get_json(f"https://booth.pm/ja/items/{item}.json")
    ids = []
    for text in [" ".join(d.get("embeds") or []), d.get("description") or ""]:
        for i in re.findall(YT_ID, text):
            if i not in ids:
                ids.append(i)
    return ids


def as_entry(x):
    if isinstance(x, dict):
        i, start = x.get("id") or "", int(x.get("start") or 0)
    else:
        i, start = str(x), 0
    m = re.search(YT_ID, i)
    i = m.group(1) if m else i
    if not start:
        t = re.search(r"[?&]t=(\d+)", str(x))
        start = int(t.group(1)) if t else 0
    return i, start


def youtube_video(i, start):
    """checked with YouTube's oEmbed: None when it is gone, private, or may not be embedded (401)"""
    url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(f"https://www.youtube.com/watch?v={i}")
    try:
        d = get_json(url)
    except urllib.error.HTTPError as e:
        print(f"         YouTube {i}: 使えない（{e.code}）")
        return None
    return {"youtube": i, "start": start, "poster": f"https://i.ytimg.com/vi/{i}/hqdefault.jpg", "name": d.get("title")}


def main():
    path = os.path.abspath(sys.argv[1])
    ep = json.load(open(path, encoding="utf-8"))
    for n in ep["news"]:
        n.pop("video", None)
        vids, where = [], ""
        if n.get("steam"):
            vids, where = steam_videos(n["steam"]), "Steam"
            time.sleep(0.4)
        if not vids:
            wanted = [as_entry(x) for x in (n.get("youtube") or [])]
            where = "YouTube"
            if not wanted and booth_item(n):
                wanted = [(i, 0) for i in booth_youtube(booth_item(n))]
                where = "BOOTH の商品ページ → YouTube"
                time.sleep(0.3)
            for i, start in wanted:
                v = youtube_video(i, start)
                time.sleep(0.2)
                if v:
                    vids.append(v)
            # how-to videos (setup in Unity and the like) say little on screen: only when there is nothing else
            shows = [v for v in vids if not GUIDE.search(v.get("name") or "")]
            vids = (shows or vids)[:MAX]
        if vids:
            n["videos"] = vids
            print(f"  ok   {n['label']}  ← {where}: " + " / ".join(v.get("name") or "?" for v in vids))
        else:
            n.pop("videos", None)
            print(f"  -    {n['label']}（動画なし）")
    json.dump(ep, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
