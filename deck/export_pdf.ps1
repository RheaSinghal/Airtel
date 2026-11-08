# Renders Kernel_TIET.pptx to Kernel_TIET.pdf through PowerPoint itself (ppSaveAsPDF = 32).
# Usage (repo root):  powershell -NoProfile -ExecutionPolicy Bypass -File deck\export_pdf.ps1
$root = Split-Path -Parent $PSScriptRoot
$pptx = Join-Path $root "Kernel_TIET.pptx"
$pdf = Join-Path $root "Kernel_TIET.pdf"
$app = New-Object -ComObject PowerPoint.Application
try {
    $deck = $app.Presentations.Open($pptx, $true, $false, $false)  # read-only, untitled=false, no window
    $deck.SaveAs($pdf, 32)
    $deck.Close()
    Write-Output "exported $pdf"
} finally {
    $app.Quit()
}
