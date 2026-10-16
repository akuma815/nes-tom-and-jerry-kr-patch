param([string]$Source, [string]$Output)
$ErrorActionPreference = 'Stop'
function Get-BytesHash([byte[]]$Data) {
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($Data))).Replace('-', '').ToLowerInvariant() }
    finally { $algorithm.Dispose() }
}
try {
    if (-not $Source) { $Source = Read-Host 'Path to unmodified Tom & Jerry (Japan).nes' }
    $Source = $Source.Trim('"')
    $sourcePath = (Resolve-Path -LiteralPath $Source).ProviderPath
    if (-not $Output) { $Output = Join-Path ([IO.Path]::GetDirectoryName($sourcePath)) ([IO.Path]::GetFileNameWithoutExtension($sourcePath) + '_KR_v1.0.nes') }
    $outputPath = [IO.Path]::GetFullPath($Output)
    if ($sourcePath -eq $outputPath) { throw 'Output must differ from the original ROM.' }
    $profile = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'release.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    [byte[]]$sourceBytes = [IO.File]::ReadAllBytes($sourcePath)
    if ($sourceBytes.Length -ne $profile.source.size -or (Get-BytesHash $sourceBytes) -ne $profile.source.sha256) {
        throw 'Unsupported source. Use the unmodified headered Tom & Jerry (Japan).nes matching the README SHA-256.'
    }
    [byte[]]$patch = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot $profile.patch.path))
    if ((Get-BytesHash $patch) -ne $profile.patch.sha256) { throw 'Patch checksum mismatch. Extract a fresh release ZIP.' }
    if ($patch.Length -lt 8 -or [Text.Encoding]::ASCII.GetString($patch, 0, 5) -ne 'PATCH') { throw 'Invalid IPS header.' }
    [byte[]]$result = $sourceBytes.Clone()
    $pos = 5
    while ($true) {
        if ($pos + 3 -gt $patch.Length) { throw 'Missing IPS terminator.' }
        if ([Text.Encoding]::ASCII.GetString($patch, $pos, 3) -eq 'EOF') { break }
        if ($pos + 5 -gt $patch.Length) { throw 'Truncated IPS record.' }
        $offset = [int]$patch[$pos] * 65536 + [int]$patch[$pos + 1] * 256 + [int]$patch[$pos + 2]
        $length = [int]$patch[$pos + 3] * 256 + [int]$patch[$pos + 4]
        $pos += 5
        if ($length -gt 0) {
            if ($pos + $length -gt $patch.Length -or $offset + $length -gt $result.Length) { throw 'IPS payload outside supported bounds.' }
            [Array]::Copy($patch, $pos, $result, $offset, $length)
            $pos += $length
        } else {
            if ($pos + 3 -gt $patch.Length) { throw 'Truncated IPS RLE.' }
            $length = [int]$patch[$pos] * 256 + [int]$patch[$pos + 1]
            if ($length -eq 0 -or $offset + $length -gt $result.Length) { throw 'IPS RLE outside supported bounds.' }
            for ($i = 0; $i -lt $length; $i++) { $result[$offset + $i] = $patch[$pos + 2] }
            $pos += 3
        }
    }
    if ($pos + 3 -ne $patch.Length) { throw 'Unexpected IPS trailer.' }
    if ($result.Length -ne $profile.target.size -or (Get-BytesHash $result) -ne $profile.target.sha256) { throw 'Patched ROM verification failed.' }
    if (Test-Path -LiteralPath $outputPath) {
        if ((Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $profile.target.sha256) { throw 'Output already exists with different content; choose a new path.' }
    } else { [IO.File]::WriteAllBytes($outputPath, $result) }
    Write-Host ('Patch v1.0 applied and verified: ' + $outputPath)
    Write-Host ('SHA-256: ' + $profile.target.sha256)
    exit 0
} catch { Write-Host ('ERROR: ' + $_.Exception.Message); exit 1 }
