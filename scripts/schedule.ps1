# Planifie les collectes Job Hunter sous Windows avec le Planificateur de tâches, en lançant
# Claude Code en mode non interactif (`claude -p`) dans ce dépôt aux heures de config/kit.yml.
#
# Usage (PowerShell) :
#   powershell -ExecutionPolicy Bypass -File scripts\schedule.ps1 install 08:00 13:00 19:00
#   powershell -ExecutionPolicy Bypass -File scripts\schedule.ps1 list
#   powershell -ExecutionPolicy Bypass -File scripts\schedule.ps1 remove
# Option : $env:JH_CHROME = "1" ajoute --chrome (sources navigateur, à tester d'abord à la main).

param([Parameter(Position = 0)][string]$Action = "help",
      [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Times)

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Prefix = "JobHunter-" + ([System.BitConverter]::ToString(
    [System.Security.Cryptography.MD5]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Root))
  ).Replace("-", "").Substring(0, 8))
$Prompt = "Lance une collecte Job Hunter."

function Out-Json($obj) { $obj | ConvertTo-Json -Compress }

switch ($Action) {
  "list" {
    $tasks = @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -like "$Prefix-*" } |
               ForEach-Object { $_.TaskName })
    Out-Json @{ ok = $true; count = $tasks.Count; entries = $tasks }
  }
  "remove" {
    Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -like "$Prefix-*" } |
      ForEach-Object { Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false }
    Out-Json @{ ok = $true; message = "Collectes planifiées supprimées." }
  }
  "install" {
    if (-not $Times -or $Times.Count -eq 0) { Out-Json @{ ok = $false; error = "no_times"; message = "indique au moins une heure, ex. 08:00" }; exit 1 }
    $claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
    if (-not $claude) { Out-Json @{ ok = $false; error = "no_claude"; message = "commande claude introuvable : installe Claude Code en ligne de commande." }; exit 1 }
    Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -like "$Prefix-*" } |
      ForEach-Object { Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false }
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "data\runs\work") | Out-Null
    $extra = ""
    if ($env:JH_CHROME -eq "1") { $extra = " --chrome" }
    $log = Join-Path $Root "data\runs\work\schedule.log"
    foreach ($t in $Times) {
      if ($t -notmatch '^([01][0-9]|2[0-3]):[0-5][0-9]$') { Out-Json @{ ok = $false; error = "bad_time"; message = "heure invalide : $t" }; exit 1 }
      $arg = "/c cd /d `"$Root`" && `"$claude`" -p `"$Prompt`" --permission-mode acceptEdits$extra >> `"$log`" 2>&1"
      $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $arg -WorkingDirectory $Root
      $trigger = New-ScheduledTaskTrigger -Daily -At $t
      $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
      Register-ScheduledTask -TaskName "$Prefix-$($t.Replace(':',''))" -Action $action -Trigger $trigger -Settings $settings | Out-Null
    }
    Out-Json @{ ok = $true; times = ($Times -join " "); claude = $claude; chrome = ($extra -ne ""); log = "data\runs\work\schedule.log" }
  }
  default { Get-Content $PSCommandPath -TotalCount 9 }
}
