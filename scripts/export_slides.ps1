$ErrorActionPreference = "Stop"
$src = "c:\pangan\reports\PanganLaba_Presentasi.pptx"
$outdir = "c:\pangan\temp\deck_slides"
if (Test-Path $outdir) { Remove-Item -Recurse -Force $outdir }
New-Item -ItemType Directory -Path $outdir | Out-Null
$ppt = New-Object -ComObject PowerPoint.Application
try {
  $pres = $ppt.Presentations.Open($src, $true, $false, $false)  # ReadOnly, Untitled, WithWindow
  $i = 1
  foreach ($s in $pres.Slides) {
    $f = Join-Path $outdir ("slide{0:D2}.png" -f $i)
    $s.Export($f, "PNG", 1333, 750)
    $i++
  }
  $pres.Close()
  "EXPORT_OK $($i-1)"
} finally {
  $ppt.Quit()
}
