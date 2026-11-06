#!/bin/bash
# Windows（Git Bash）で tools/publish.sh を動かすための入口。
# Windows では python3 がストアの案内になっていて動かないので、python を python3 として使う。
# 台本の JSON を UTF-8 で読むように PYTHONUTF8=1、共有カードの日本語フォントは Windows に入っている Noto Sans JP。
# usage: bash tools/publish-win.sh
python3() { python "$@"; }
export -f python3
export PYTHONUTF8=1
export SHARE_PYTHON=${SHARE_PYTHON:-python}
export SHARE_FONT=${SHARE_FONT:-C:/Windows/Fonts/NotoSansJP-VF.ttf}
exec bash "$(dirname "$0")/publish.sh" "$@"
