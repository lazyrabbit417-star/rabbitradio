"""台本の話題に、Steam のストアにある公式の動画（トレーラー・プレイ動画）を付ける。

usage: python tools/trailer.py episodes/2026-11-06-ja.json

- 話題に "steam": <アプリID> があれば、Steam のストアからそのゲームの動画を探し、
  "videos": [{"hls", "poster", "name"}, ...] を書く（最大 3 本。目立つもの = highlight を先に）
- 動画は保存しない。Steam が配信している動画の URL を書くだけ（リンクカードの画像と同じ考え方）
- プレーヤーは、その話題のあいだ、左の枠の上に大きく、音なしで順に流し、最後まで行ったら最初に戻る
- 動画がないゲームは、いつもの枠のまま
"""
import json
import os
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36"


def movies(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=jp&l=japanese"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
        d = json.loads(r.read().decode("utf-8")).get(str(appid), {})
    return (d.get("data") or {}).get("movies") or [] if d.get("success") else []


def main():
    path = os.path.abspath(sys.argv[1])
    ep = json.load(open(path, encoding="utf-8"))
    for n in ep["news"]:
        app = n.get("steam")
        if not app:
            continue
        ms = [m for m in movies(app) if m.get("hls_h264")]
        time.sleep(0.4)
        n.pop("video", None)
        if not ms:
            n.pop("videos", None)
            print(f"  -    {n['label']}（動画なし）")
            continue
        ms = sorted(ms, key=lambda m: not m.get("highlight"))[:3]
        n["videos"] = [{"hls": m["hls_h264"], "poster": m.get("thumbnail"), "name": m.get("name")} for m in ms]
        print(f"  ok   {n['label']}  ← " + " / ".join(m.get("name") or "?" for m in ms))
    json.dump(ep, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
