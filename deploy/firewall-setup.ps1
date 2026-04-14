# Desktop firewall setup — run as Administrator on the desktop
# Opens ports for LAN access from ultrabook
#
# Usage (PowerShell as Admin):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\firewall-setup.ps1

$rules = @(
    @{ Name = "Ollama LAN";  Port = 11434; Desc = "Ollama LLM inference API" },
    @{ Name = "Qdrant REST"; Port = 6333;  Desc = "Qdrant vector store REST API" },
    @{ Name = "Qdrant gRPC"; Port = 6334;  Desc = "Qdrant vector store gRPC" },
    @{ Name = "n8n";         Port = 5678;  Desc = "n8n orchestration dashboard" },
    @{ Name = "Gitea Web";   Port = 3000;  Desc = "Gitea git web UI" },
    @{ Name = "Gitea SSH";   Port = 2222;  Desc = "Gitea git SSH" }
)

Write-Host "=== Opening firewall ports for LLM orchestration ===" -ForegroundColor Cyan
Write-Host ""

foreach ($rule in $rules) {
    $existing = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "  [SKIP] $($rule.Name) (port $($rule.Port)) — already exists" -ForegroundColor Yellow
    } else {
        New-NetFirewallRule `
            -DisplayName $rule.Name `
            -Direction Inbound `
            -Protocol TCP `
            -LocalPort $rule.Port `
            -Action Allow `
            -Description $rule.Desc `
            -Profile Private | Out-Null
        Write-Host "  [OK]   $($rule.Name) (port $($rule.Port)) — opened" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== Done. Ports open on Private network profile. ===" -ForegroundColor Cyan
Write-Host "Verify from ultrabook: bash verify.sh $(hostname)" -ForegroundColor Gray
