Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$condition = [System.Windows.Automation.PropertyCondition]::new(
    [System.Windows.Automation.AutomationElement]::NameProperty,
    "富山ゼミ"
)
$teams = $root.FindFirst([System.Windows.Automation.TreeScope]::Children, $condition)
if (-not $teams) {
    $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
    for ($i = 0; $i -lt $windows.Count; $i++) {
        $name = $windows.Item($i).Current.Name
        if ($name -like "*Teams*" -or $name -like "*富山*") {
            $teams = $windows.Item($i)
            break
        }
    }
}
if (-not $teams) {
    Write-Output "NO_TEAMS_WINDOW"
    exit 0
}

$elements = $teams.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
for ($i = 0; $i -lt $elements.Count; $i++) {
    $name = $elements.Item($i).Current.Name
    if ($name -and $name.Trim().Length -gt 0) {
        Write-Output $name
    }
}
