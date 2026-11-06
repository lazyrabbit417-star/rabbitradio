"""台本（episodes/<日付>-<言語>.json）を COEIROINK で読み上げて、1 本の mp3 にする。

usage: python tools/voice.py episodes/2026-11-06-ja.json [--speaker リリンちゃん] [--style 0] [--speed 1.0]

- COEIROINK v2 を起動しておく（エンジンは http://127.0.0.1:50032 で待っている）
- 声は audio/<日付>-<言語>.mp3 に書く（git には入れない。tools/publish.sh が gh-pages に載せる）
- 台本の seconds・lines_timed・segments・made_at を、できた声に合わせて書き直す
- episodes.json の、その日の題と長さも書き直す
ffmpeg が要る（wav → mp3）。
"""
import argparse
import datetime
import io
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import wave

ENGINE = os.environ.get("COEIROINK_URL", "http://127.0.0.1:50032")
LEAD, TAIL = 0.6, 0.8          # 頭と終わりの無音（秒）
GAP_LINE, GAP_PART = 0.25, 0.8  # 文と文、パートとパートのあいだ


def api(path, body=None, raw=False):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(ENGINE + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = r.read()
    return out if raw else json.loads(out.decode("utf-8"))


def find_speaker(name, style):
    speakers = api("/v1/speakers")
    for s in speakers:
        if name in s["speakerName"]:
            styles = s["styles"]
            st = next((x for x in styles if str(x["styleId"]) == str(style) or x["styleName"] == str(style)), None)
            if st is None and style is None:
                st = styles[0]
            if st is None:
                sys.exit(f"スタイル {style} が見つかりません。ある: " + ", ".join(f'{x["styleName"]}({x["styleId"]})' for x in styles))
            return s["speakerUuid"], st["styleId"], f'{s["speakerName"]}（{st["styleName"]}）'
    sys.exit(f"声 {name} が COEIROINK に入っていません。ある: " + ", ".join(s["speakerName"] for s in speakers))


def synth(text, uuid, style_id, speed):
    prosody = api("/v1/estimate_prosody", {"text": text})
    body = {
        "speakerUuid": uuid, "styleId": style_id, "text": text,
        "prosodyDetail": prosody["detail"],
        "speedScale": speed, "volumeScale": 1.0, "pitchScale": 0.0, "intonationScale": 1.0,
        "prePhonemeLength": 0.05, "postPhonemeLength": 0.05, "outputSamplingRate": 44100,
    }
    with wave.open(io.BytesIO(api("/v1/synthesis", body, raw=True))) as w:
        return w.getparams(), w.readframes(w.getnframes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--speaker", default="リリンちゃん")
    ap.add_argument("--style", default=None, help="スタイルの番号か名前（なければ最初のスタイル）")
    ap.add_argument("--speed", type=float, default=1.0)
    a = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.abspath(a.episode)
    ep = json.load(open(path, encoding="utf-8"))
    name = os.path.splitext(os.path.basename(path))[0]            # 2026-11-06-ja
    station = json.load(open(os.path.join(root, "station.json"), encoding="utf-8"))
    adir = os.path.join(root, station.get("audio", {}).get("dir", "audio"))
    os.makedirs(adir, exist_ok=True)

    uuid, style_id, label = find_speaker(a.speaker, a.style)
    print(f"声: {label}")

    # パート：0 = オープニング、1..N = ニュース、N+1 = 締め
    parts = [("opening", None, ep["opening"])]
    parts += [("news", i, n["lines"]) for i, n in enumerate(ep["news"])]
    parts.append(("closing", None, ep["closing"]))

    params, rate, width, chans = None, None, None, None
    pcm = bytearray()
    timed, segments = [], []

    def silence(sec):
        pcm.extend(b"\x00" * (int(rate * sec) * width * chans))

    def now():
        return len(pcm) / (rate * width * chans)

    total = sum(len(p[2]) for p in parts)
    k = 0
    for pi, (kind, idx, lines) in enumerate(parts):
        for li, line in enumerate(lines):
            p, frames = synth(line["say"], uuid, style_id, a.speed)
            if params is None:
                params, rate, width, chans = p, p.framerate, p.sampwidth, p.nchannels
                silence(LEAD)
            elif li == 0:
                silence(GAP_PART)
            else:
                silence(GAP_LINE)
            if li == 0:
                seg_start = now()
            start = now()
            pcm.extend(frames)
            timed.append({"start": round(start, 3), "end": round(now(), 3), "show": line["show"], "part": pi})
            k += 1
            print(f"  {k}/{total}  {now():6.2f}s  {line['show']}")
        segments.append({"kind": kind, "index": idx, "start": round(seg_start, 3), "end": None})
    silence(TAIL)
    seconds = round(now(), 2)
    for i, s in enumerate(segments):  # 次のパートの頭まで、最後は声の終わりまで
        s["end"] = segments[i + 1]["start"] if i + 1 < len(segments) else round(now(), 3)

    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "all.wav")
        with wave.open(wav, "wb") as w:
            w.setparams(params)
            w.writeframes(bytes(pcm))
        mp3 = os.path.join(adir, name + ".mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-ar", "44100", "-b:a", "80k", mp3], check=True)
    print(f"音声: {os.path.relpath(mp3, root)}  {seconds} 秒  {os.path.getsize(mp3) // 1024} KB")

    ep["seconds"] = seconds
    ep["lines_timed"] = timed
    ep["segments"] = segments
    ep["made_at"] = datetime.datetime.now().replace(microsecond=0).isoformat()
    json.dump(ep, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # episodes.json：新しい順。その日の、その言語の題と長さ
    lst_path = os.path.join(root, station.get("episodes", "episodes.json"))
    lst = json.load(open(lst_path, encoding="utf-8")) if os.path.exists(lst_path) else []
    key = ep.get("id") or ep["date"]          # a second episode that day has "id": "<date>-2"
    entry = next((e for e in lst if (e.get("id") or e["date"]) == key), None)
    if entry is None:
        entry = {"date": ep["date"], **({"id": ep["id"]} if ep.get("id") else {})}
        lst.append(entry)
    entry[ep["lang"]] = {"title": ep["title"], "seconds": seconds}
    lst.sort(key=lambda e: (e["date"], int((e.get("id") or "")[11:] or 1)), reverse=True)
    json.dump(lst, open(lst_path, "w", encoding="utf-8"), ensure_ascii=False)
    print("台本と episodes.json を更新しました")


if __name__ == "__main__":
    main()
