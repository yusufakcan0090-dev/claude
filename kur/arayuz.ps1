# Kesit Stüdyosu kurulum arayüzü
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$Root = Split-Path -Parent $PSScriptRoot
$Status = Join-Path $env:TEMP ('ks_kurulum_' + [guid]::NewGuid().ToString('N') + '.txt')
Set-Content -LiteralPath $Status -Value '' -Encoding UTF8

$bg = [Drawing.Color]::FromArgb(28, 28, 28); $panel = [Drawing.Color]::FromArgb(38, 38, 38)
$blue = [Drawing.Color]::FromArgb(45, 140, 235); $fg = [Drawing.Color]::FromArgb(230, 230, 230); $mut = [Drawing.Color]::FromArgb(140, 140, 140)
$f = New-Object Windows.Forms.Form
$f.Text = 'Kesit Stüdyosu - Kurulum'; $f.Size = New-Object Drawing.Size(620, 520); $f.StartPosition = 'CenterScreen'
$f.FormBorderStyle = 'FixedSingle'; $f.MaximizeBox = $false; $f.BackColor = $bg; $f.ForeColor = $fg
$ico = Join-Path $Root 'app\ui\icon.ico'; if (Test-Path $ico) { $f.Icon = New-Object Drawing.Icon($ico) }
function L($t, $x, $y, $w, $h, $size, $bold, $col) { $l = New-Object Windows.Forms.Label; $l.Text = $t; $l.Location = New-Object Drawing.Point($x, $y); $l.Size = New-Object Drawing.Size($w, $h); $l.Font = New-Object Drawing.Font('Segoe UI', $size, $(if ($bold) { [Drawing.FontStyle]::Bold } else { [Drawing.FontStyle]::Regular })); $l.ForeColor = $col; $l.BackColor = [Drawing.Color]::Transparent; $f.Controls.Add($l); $l }
L 'Kesit Stüdyosu' 28 20 540 40 20 $true $fg | Out-Null
L 'Her şey otomatik kuruluyor. Bilgisayarına göre ayarlanıyor, sen bir şey yapma.' 30 62 560 22 10 $false $mut | Out-Null
$gpuL = L 'Ekran kartı aranıyor...' 30 88 560 22 10 $false $blue
$names = 'Ekran kartı tespiti', 'Python', 'Program paketleri', 'Ekran kartına özel dosyalar', 'FFmpeg (video motoru)', 'Türkçe altyazı modeli', 'Masaüstü kısayolu'
$rows = @()
for ($i = 0; $i -lt $names.Count; $i++) { $rows += (L ('○   ' + $names[$i]) 40 (124 + $i * 30) 520 26 11 $false $mut) }
$bar = New-Object Windows.Forms.ProgressBar; $bar.Location = New-Object Drawing.Point(30, 346); $bar.Size = New-Object Drawing.Size(545, 14); $bar.Style = 'Continuous'; $f.Controls.Add($bar)
$logL = L '' 30 366 545 38 9 $false $mut
$btn = New-Object Windows.Forms.Button; $btn.Text = 'Kuruluyor...'; $btn.Enabled = $false; $btn.Location = New-Object Drawing.Point(395, 420); $btn.Size = New-Object Drawing.Size(180, 40)
$btn.FlatStyle = 'Flat'; $btn.FlatAppearance.BorderSize = 0; $btn.BackColor = $blue; $btn.ForeColor = [Drawing.Color]::White; $btn.Font = New-Object Drawing.Font('Segoe UI', 11, [Drawing.FontStyle]::Bold); $f.Controls.Add($btn)
$state = @{ pos = 0; cur = 0; done = $false; failed = $false }
function SetStep($n) {
  for ($i = 0; $i -lt $rows.Count; $i++) {
    if ($i + 1 -lt $n) { $rows[$i].Text = '✓   ' + $names[$i]; $rows[$i].ForeColor = [Drawing.Color]::FromArgb(74, 196, 96) }
    elseif ($i + 1 -eq $n) { $rows[$i].Text = '●   ' + $names[$i] + '...'; $rows[$i].ForeColor = $fg }
  }
}
$timer = New-Object Windows.Forms.Timer; $timer.Interval = 300
$timer.Add_Tick({
  try { $all = Get-Content -LiteralPath $Status -Encoding UTF8 } catch { return }
  if (-not $all) { return }
  $all = @($all)
  for ($k = $state.pos; $k -lt $all.Count; $k++) {
    $p = $all[$k] -split '\|', 2
    switch ($p[0]) {
      'STEP' { $state.cur = [int]$p[1]; SetStep $state.cur }
      'PCT' { $bar.Value = [Math]::Min(100, [int]$p[1]) }
      'LOG' { $t = $p[1]; if ($t.Length -gt 140) { $t = $t.Substring(0, 140) + '…' }; $logL.Text = $t }
      'GPU' { $g = $p[1] -split '\|'; $v = $g[-1]; $nm = ($g[0..($g.Count - 2)] -join ', '); $gpuL.Text = 'Ekran kartı: ' + $(if ($nm) { $nm } else { 'bulunamadı' }) + $(switch ($v) { 'nvidia' { '  →  hızlı altyazı (NVIDIA)' } 'amd' { '  →  AMD ile dışa aktarma' } 'intel' { '  →  Intel ile dışa aktarma' } default { '' } }) }
      'DONE' { $state.done = $true; SetStep 99; $bar.Value = 100; $logL.Text = 'Kurulum tamam! Masaüstünde "Kesit Stüdyosu" simgesi var.'; $btn.Text = 'Programı Aç'; $btn.Enabled = $true; $timer.Stop() }
      'FAIL' { $state.failed = $true; $logL.ForeColor = [Drawing.Color]::FromArgb(255, 120, 90); $logL.Text = 'HATA: ' + $p[1]; $btn.Text = 'Tekrar Dene'; $btn.Enabled = $true; $btn.BackColor = [Drawing.Color]::FromArgb(90, 90, 90); $timer.Stop() }
    }
  }
  $state.pos = $all.Count
})
$start = {
  Set-Content -LiteralPath $Status -Value '' -Encoding UTF8; $state.pos = 0; $state.failed = $false
  $btn.Enabled = $false; $btn.Text = 'Kuruluyor...'; $btn.BackColor = $blue; $logL.ForeColor = $mut
  Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"' + (Join-Path $PSScriptRoot 'isci.ps1') + '"'), '-Root', ('"' + $Root + '"'), '-Status', ('"' + $Status + '"'))
  $timer.Start()
}
$btn.Add_Click({
  if ($state.done) { Start-Process -FilePath (Join-Path $Root '.venv\Scripts\pythonw.exe') -ArgumentList ('"' + (Join-Path $Root 'app\main.py') + '"') -WorkingDirectory $Root; $f.Close() }
  elseif ($state.failed) { & $start }
})
$f.Add_Shown({ & $start })
[void]$f.ShowDialog()
