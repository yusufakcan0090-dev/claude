; Kesit Stüdyosu — tek dosya kurulum (makensis ile derlenir)
Unicode true
!include "MUI2.nsh"
!ifndef VERSION
  !define VERSION "1.0.0"
!endif
!ifndef SRC
  !define SRC ".."
!endif
Name "B.E.K"
OutFile "KesitStudyosu_Kurulum.exe"
InstallDir "$LOCALAPPDATA\KesitStudyosu"
InstallDirRegKey HKCU "Software\KesitStudyosu" "Klasor"
RequestExecutionLevel user
SetCompressor /SOLID lzma
BrandingText "B.E.K ${VERSION}"
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "B.E.K"
VIAddVersionKey "FileDescription" "B.E.K Kurulum"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "CompanyName" "Animeci"
VIAddVersionKey "LegalCopyright" "Animeci"

!define MUI_ICON "${SRC}\app\ui\icon.ico"
!define MUI_UNICON "${SRC}\app\ui\icon.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "B.E.K'e hoş geldin"
!define MUI_WELCOMEPAGE_TEXT "Kick ve YouTube yayınlarından en iyi anları bulan, Türkçe altyazı ekleyen, video kalitesini yapay zekâ ile artıran program.$\r$\n$\r$\nİleri'ye bas, gerisini program halleder. Kurulum, ekran kartını bulup gerekli her şeyi (Python, FFmpeg, altyazı modeli) kendisi indirir; internet hızına göre 10-30 dakika sürer."
!define MUI_FINISHPAGE_TITLE "Dosyalar hazır"
!define MUI_FINISHPAGE_TEXT "Şimdi kurulum penceresi açılacak ve kalan her şeyi kendisi indirip kuracak.$\r$\n$\r$\nBitince masaüstündeki 'B.E.K' simgesiyle programı açarsın."
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Kurulumu şimdi başlat"
!define MUI_FINISHPAGE_RUN_FUNCTION BaslatKurulum

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Turkish"

Function BaslatKurulum
  Exec '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "$INSTDIR\kur\arayuz.ps1"'
FunctionEnd

Section "B.E.K" SecMain
  SetOutPath "$INSTDIR"
  File /r /x "__pycache__" /x "*.pyc" "${SRC}\app"
  File /r "${SRC}\kur"
  File "${SRC}\requirements.txt"
  File /nonfatal "${SRC}\requirements-nvidia.txt"
  File /nonfatal "${SRC}\kurulum.py"
  File /nonfatal "${SRC}\KUR.bat"
  File /nonfatal "${SRC}\OKU_BENI.txt"
  WriteRegStr HKCU "Software\KesitStudyosu" "Klasor" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Kaldir.exe"
  ; Program Ekle/Kaldır listesine ekle
  !define UNKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\KesitStudyosu"
  WriteRegStr HKCU "${UNKEY}" "DisplayName" "B.E.K"
  WriteRegStr HKCU "${UNKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNKEY}" "Publisher" "Animeci"
  WriteRegStr HKCU "${UNKEY}" "DisplayIcon" "$INSTDIR\app\ui\icon.ico"
  WriteRegStr HKCU "${UNKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNKEY}" "UninstallString" '"$INSTDIR\Kaldir.exe"'
  WriteRegDWORD HKCU "${UNKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNKEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\Kesit Stüdyosu.lnk"
  Delete "$DESKTOP\Kesit Studyosu.lnk"
  Delete "$DESKTOP\B.E.K.lnk"
  Delete "$SMPROGRAMS\B.E.K.lnk"
  Delete "$SMPROGRAMS\Kesit Stüdyosu.lnk"
  RMDir /r "$INSTDIR\app"
  RMDir /r "$INSTDIR\kur"
  RMDir /r "$INSTDIR\.venv"
  RMDir /r "$INSTDIR\bin"
  Delete "$INSTDIR\*.txt"
  Delete "$INSTDIR\*.py"
  Delete "$INSTDIR\*.bat"
  MessageBox MB_YESNO "Projelerin, ayarların ve indirdiğin videolar da silinsin mi?$\r$\n(Hayır dersen 'veri' klasörü kalır.)" IDNO +2
  RMDir /r "$INSTDIR\veri"
  Delete "$INSTDIR\Kaldir.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\KesitStudyosu"
  DeleteRegKey HKCU "Software\KesitStudyosu"
SectionEnd
