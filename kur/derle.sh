#!/bin/sh
# Kurulum dosyasını derler: BEK_Kurulum.exe (eski link için KesitStudyosu_Kurulum.exe kopyası da) (makensis gerekir)
cd "$(dirname "$0")"
V=$(python3 -c "import json;print(json.load(open('../app/version.json'))['version'])")
makensis -V2 -DVERSION="$V" -DSRC="$(cd .. && pwd)" kurulum.nsi && mv -f BEK_Kurulum.exe ../BEK_Kurulum.exe && cp -f ../BEK_Kurulum.exe ../KesitStudyosu_Kurulum.exe
