# Renders each slide to deck/build/slide-N.png through PowerPoint (for visual QA).
$root = Split-Path -Parent $PSScriptRoot
$pptx = Join-Path $root "Kernel_TIET.pptx"
$out = Join-Path $PSScriptRoot "build"
$app = New-Object -ComObject PowerPoint.Application
try {
    $deck = $app.Presentations.Open($pptx, $true, $false, $false)
    foreach ($s in $deck.Slides) { $s.Export((Join-Path $out ("slide-" + $s.SlideIndex + ".png")), "PNG", 1600, 900) }
    $deck.Close()
} finally { $app.Quit() }
