<h1 align="center">らびっとらじお</h1>

<p align="center"><b>Steam・PCの、かわいい女の子が出てくるアニメ調のゲームを、ニュース・新作紹介・じっくり紹介でお届けします。</b></p>

<p align="center">
  <a href="https://lazyrabbit417-star.github.io/rabbitradio/"><img src="https://img.shields.io/badge/%E2%96%B6%20ON%20AIR-%E3%82%89%E3%81%B3%E3%81%A3%E3%81%A8%E3%82%89%E3%81%98%E3%81%8A-ffd028?style=for-the-badge&labelColor=ff4468" alt="らびっとらじおを見る"></a>
</p>

キャラクターがゲームのニュースを読む、HTMLのラジオ番組です。再生に合わせて、スライド・字幕・キャラ・記事やストアのリンクカードが動きます。

- 番組を見る：<https://lazyrabbit417-star.github.io/rabbitradio/>
- ジャンルは問いません（アクション、ローグライク、シミュレーション、RPG、ノベル……）。アニメ調のかわいい女の子が出てくるゲームが中心です
- **全年齢向けのタイトルだけ**を扱います。成人向け（Steam の「成人向けの性的なコンテンツ」などの表示があるもの、18歳以上の年齢確認があるもの）は取り上げません
- 台本は `episodes/` に文字で残っています

## 番組の作り方

1. **台本を書く**：`episodes/<日付>-ja.json`。話題ごとに見出し・要点・話す文・出典。新作紹介は `"corner": "pickup"`、1本を掘り下げるときは `"corner": "focus"` を付ける。形は [docs/formats.md](docs/formats.md)
2. **リンクカード**：`python tools/linkcard.py <記事やストアのURL> ...`
3. **声を吹き込む**：COEIROINK を起動して `python tools/voice.py episodes/<日付>-ja.json`
4. **手元で見る**：`python tools/serve.py 8766` を動かして <http://127.0.0.1:8766/> を開く
5. **放送する**：`main` にコミットして push し、`bash tools/publish-win.sh` を実行（Windows の Git Bash で）

同じ日に2本目を出すときは、`<日付>-2` の名前で置きます（[docs/formats.md](docs/formats.md)）。音声は `main` にはコミットしません。

## クレジット・ライセンス

- 声：COEIROINK:リリンちゃん
- キャラ：[myradio](https://github.com/monoradio102/myradio) のお手本のキャラ（AIで生成したキャラクター。公序良俗に反しない使い方なら自由に使えます）
- プレーヤー（`index.html`、`tools/`）：[myradio](https://github.com/monoradio102/myradio) をもとにしています。MIT License
- 台本（`episodes/`、`episodes.json`）：CC0
- 天気：Open-Meteo（CC BY 4.0）
- ゲームの画像は、記事やストアのサイトが共有用に公開している画像（OGP）を、そのサイトから直接表示しています
