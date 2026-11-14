"""記事の URL から、リンクカード用の情報（OGP）を集める。

usage: python tools/linkcard.py <url> [<url> ...]   → JSON の並びを標準出力へ

画像は保存しない。サイトが共有用に出している画像（og:image）の URL を書くだけ。
開けなかったときは {"url", "error", "status"} を返す。
"""
import json
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) myradio-linkcard/1.0"


class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.icons = []
        self.title = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key and "content" in a and key not in self.meta:
                self.meta[key] = a["content"].strip()
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if "icon" in rel and a.get("href"):
                self.icons.append((rel, a["href"]))
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and self.title is None and data.strip():
            self.title = data.strip()


def card(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            final = r.geturl()
            raw = r.read(2_000_000)
            charset = r.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as e:
        return {"url": url, "error": "HTTPError", "status": e.code}
    except Exception as e:  # noqa: BLE001
        return {"url": url, "error": type(e).__name__}
    p = Meta()
    p.feed(raw.decode(charset, errors="replace"))
    m = p.meta
    icon = None
    for rel, href in sorted(p.icons, key=lambda x: 0 if "apple-touch" in x[0] else 1):
        icon = urljoin(final, href)
        break
    if icon is None:
        u = urlparse(final)
        icon = f"{u.scheme}://{u.netloc}/favicon.ico"
    image = m.get("og:image") or m.get("twitter:image")
    return {
        "url": url,
        "title": m.get("og:title") or m.get("twitter:title") or p.title,
        "site": m.get("og:site_name") or urlparse(final).netloc,
        "description": m.get("og:description") or m.get("description") or m.get("twitter:description"),
        "image": urljoin(final, image) if image else None,
        "icon": icon,
    }


if __name__ == "__main__":
    print(json.dumps([card(u) for u in sys.argv[1:]], ensure_ascii=False, indent=1))
