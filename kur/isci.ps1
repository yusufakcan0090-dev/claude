# Kesit Stüdyosu kurulum işçisi: her şeyi sırayla kurar, durumu dosyaya yazar (arayüz okur)
param([string]$Root, [string]$Status)
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
function W($t) { Add-Content -LiteralPath $Status -Value $t -Encoding UTF8 }
function Step($n, $p) { W "STEP|$n"; W "PCT|$p" }
function Fail($m) { W "FAIL|$m"; exit 1 }
Set-Location -LiteralPath $Root

# 1) Ekran kartı
Step 1 3
$gpu = ''
try { $gpu = ((Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join ' | ') } catch {}
$vendor = 'yok'
if ($gpu -match 'NVIDIA') { $vendor = 'nvidia' } elseif ($gpu -match 'AMD|Radeon') { $vendor = 'amd' } elseif ($gpu -match 'Intel') { $vendor = 'intel' }
W "GPU|$gpu|$vendor"
W "LOG|Ekran kartı: $gpu"

# 2) Python
Step 2 8
$py = $null
foreach ($v in '3.12', '3.11', '3.13') {
  try { & py "-$v" -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { $py = @('py', "-$v"); break } } catch {}
}
$local = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
if (-not $py -and (Test-Path $local)) { $py = @($local) }
if (-not $py) {
  W "LOG|Python indiriliyor (~25 MB)..."
  $exe = Join-Path $env:TEMP 'python-3.12.8-amd64.exe'
  try { Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe' -OutFile $exe -UseBasicParsing } catch { Fail "Python indirilemedi: $($_.Exception.Message)" }
  W "LOG|Python kuruluyor..."
  Start-Process -FilePath $exe -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0' -Wait
  if (Test-Path $local) { $py = @($local) } else { Fail 'Python kurulamadı. python.org adresinden Python 3.12 kurup tekrar dene.' }
}
W "LOG|Python hazır"

# 3) Sanal ortam ve paketler
Step 3 15
$vpy = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $vpy)) {
  W "LOG|Sanal ortam oluşturuluyor..."
  $a = @(); if ($py.Count -gt 1) { $a += $py[1..($py.Count - 1)] }
  & $py[0] @a -m venv (Join-Path $Root '.venv') 2>&1 | ForEach-Object { W "LOG|$_" }
  if (-not (Test-Path $vpy)) { Fail 'Sanal ortam oluşturulamadı.' }
}
& $vpy -m pip install --upgrade pip --disable-pip-version-check -q 2>&1 | Out-Null
$n = 0
& $vpy -m pip install -r (Join-Path $Root 'requirements.txt') --disable-pip-version-check 2>&1 | ForEach-Object {
  $l = "$_"; W "LOG|$l"
  if ($l -match '^(Collecting|Downloading|Installing)') { $n++; W ("PCT|" + [Math]::Min(55, 15 + $n)) }
}
if ($LASTEXITCODE -ne 0) { Fail 'Paketler kurulamadı. İnternet bağlantını kontrol edip tekrar dene.' }

# 4) Ekran kartına göre ek dosyalar
Step 4 58
if ($vendor -eq 'nvidia') {
  W "LOG|NVIDIA bulundu: hızlı altyazı dosyaları kuruluyor (büyük, biraz sürer)..."
  & $vpy -m pip install -r (Join-Path $Root 'requirements-nvidia.txt') --disable-pip-version-check 2>&1 | ForEach-Object { W "LOG|$_" }
} else {
  W "LOG|NVIDIA yok: altyazı işlemciyle, dışa aktarma $vendor ekran kartıyla yapılacak. Ek dosya gerekmiyor."
}

# 5-6) FFmpeg ve altyazı modeli
Step 5 72
$env:PYTHONIOENCODING = 'utf-8'
& $vpy (Join-Path $Root 'kurulum.py') --gpu $vendor 2>&1 | ForEach-Object {
  $l = "$_"; W "LOG|$l"

  if ($l -match '3/3') { W "STEP|6"; W "PCT|88" }
}

# 7) Kısayol
Step 7 97
try {
  $s = (New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Kesit Stüdyosu.lnk')
  $s.TargetPath = Join-Path $Root '.venv\Scripts\pythonw.exe'
  $s.Arguments = '"' + (Join-Path $Root 'app\main.py') + '"'
  $s.WorkingDirectory = $Root
  $s.IconLocation = Join-Path $Root 'app\ui\icon.ico'
  $s.Save()
  W "LOG|Masaüstüne kısayol eklendi"
} catch { W "LOG|Kısayol eklenemedi: $($_.Exception.Message)" }
W "PCT|100"
W "DONE"
