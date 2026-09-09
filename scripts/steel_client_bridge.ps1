[CmdletBinding()]
param(
    [ValidateSet('verify', 'codex', 'claude')]
    [string]$Mode = 'verify',
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ClientArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectId = 'rss7-ai-media'
$SecretName = 'steel-mcp-token'
$SteelUrl = 'https://steel-browser-mcp-518404402696.us-central1.run.app/mcp/'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Verifier = Join-Path $PSScriptRoot 'verify_steel_client.py'

function Resolve-Executable([string[]]$Names) {
    foreach ($name in $Names) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

function Resolve-Codex {
    $root = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin'
    if (-not (Test-Path $root)) { return $null }
    $found = Get-ChildItem $root -Recurse -Filter codex.exe -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($found) { return $found.FullName }
    return $null
}

$gcloud = Resolve-Executable @('gcloud.cmd', 'gcloud.exe')
if (-not $gcloud) { throw 'gcloud is required but was not found.' }

$token = (& $gcloud secrets versions access latest `
    --secret=$SecretName `
    --project=$ProjectId 2>$null | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
    throw 'Steel MCP token could not be read from Secret Manager.'
}

$oldUrl = [Environment]::GetEnvironmentVariable('STEEL_BROWSER_MCP_URL', 'Process')
$oldToken = [Environment]::GetEnvironmentVariable('STEEL_BROWSER_MCP_TOKEN', 'Process')
$env:STEEL_BROWSER_MCP_URL = $SteelUrl
$env:STEEL_BROWSER_MCP_TOKEN = $token

try {
    & python $Verifier
    if ($LASTEXITCODE -ne 0) { throw 'Direct Steel MCP verification failed.' }

    $codex = Resolve-Codex
    $claude = Resolve-Executable @('claude.exe', 'claude')
    if ($codex -and $Mode -in @('verify', 'codex')) {
        & $codex mcp get steel-browser *> $null
        if ($LASTEXITCODE -ne 0) {
            & $codex mcp add steel-browser --url $SteelUrl `
                --bearer-token-env-var STEEL_BROWSER_MCP_TOKEN
            if ($LASTEXITCODE -ne 0) { throw 'Codex Steel MCP registration failed.' }
        }
        Write-Output '[PASS] Codex Steel MCP configuration is present'
    }

    if ($claude -and $Mode -in @('verify', 'claude')) {
        Push-Location $RepoRoot
        try {
            $claudeOutput = (& $claude mcp get steel-browser 2>&1 | Out-String)
            if ($LASTEXITCODE -ne 0 -or $claudeOutput -notmatch 'Connected') {
                throw 'Claude Code did not report Steel MCP as connected.'
            }
            Write-Output '[PASS] Claude Code Steel MCP health check'
        }
        finally { Pop-Location }
    }

    if ($Mode -eq 'codex') {
        if (-not $codex) { throw 'Codex CLI was not found.' }
        & $codex @ClientArgs
    }
    elseif ($Mode -eq 'claude') {
        if (-not $claude) { throw 'Claude Code CLI was not found.' }
        Push-Location $RepoRoot
        try { & $claude @ClientArgs }
        finally { Pop-Location }
    }
    else {
        Write-Output '[PASS] Steel client bridge verification complete'
    }
}
finally {
    if ($null -eq $oldUrl) { Remove-Item Env:STEEL_BROWSER_MCP_URL -ErrorAction SilentlyContinue }
    else { $env:STEEL_BROWSER_MCP_URL = $oldUrl }

    if ($null -eq $oldToken) { Remove-Item Env:STEEL_BROWSER_MCP_TOKEN -ErrorAction SilentlyContinue }
    else { $env:STEEL_BROWSER_MCP_TOKEN = $oldToken }

    $token = $null
}
