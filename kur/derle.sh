#!/bin/sh
# Kurulum dosyasını derler: KesitStudyosu_Kurulum.exe (makensis gerekir)
cd "$(dirname "$0")"
V=$(python3 -c "import json;print(json.load(open('../app/version.json'))['version'])")
makensis -V2 -DVERSION="$V" -DSRC="$(cd .. && pwd)" kurulum.nsi && mv -f KesitStudyosu_Kurulum.exe ../KesitStudyosu_Kurulum.exe
