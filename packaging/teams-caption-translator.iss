#define MyAppName "Teams Caption Translator"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "Teams Caption Translator"
#define MyAppExeName "TeamsCaptionTranslator.exe"

[Setup]
AppId={{6D1DAE4E-6E2A-4B3B-9A07-9D9D0B1E8F52}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Teams Caption Translator
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\installer
OutputBaseFilename=TeamsCaptionTranslatorSetup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "..\dist\TeamsCaptionTranslator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
