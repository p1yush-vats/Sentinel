; SENTINEL Desktop App — Inno Setup Installer Script
; Updated for PyInstaller single-file output
;
; Prerequisites:
;   1. Build SENTINEL.exe first:   build.bat
;   2. Open this file in Inno Setup Compiler
;   3. Press F9 to compile the installer
;
; Output: desktop-app\dist\installer\SENTINEL-Setup.exe

#define MyAppName      "SENTINEL"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "SENTINEL"
#define MyAppExeName   "SENTINEL.exe"
#define MyAppIcon      "assets\iso\sentinel.ico"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=SENTINEL-Setup
SetupIconFile={#MyAppIcon}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible
DisableWelcomePage=no
DisableDirPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"
Name: "startmenuicon"; Description: "Create a &Start Menu shortcut"; GroupDescription: "Additional icons:"
Name: "startupicon"; Description: "Start SENTINEL with &Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "dist\SENTINEL.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\.env"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists('dist\.env')

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch SENTINEL now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\.env"

[Code]
procedure CreateDefaultEnv(EnvPath: String);
var
  Lines: TArrayOfString;
begin
  if FileExists(EnvPath) then Exit;

  SetArrayLength(Lines, 9);
  Lines[0] := 'API_BASE_URL=https://sentinel-ny7w.onrender.com';
  Lines[1] := 'PORTAL_URL=https://sentinel-self.vercel.app/';
  Lines[2] := 'WORK_MINUTES_PER_HOUR=50';
  Lines[3] := 'BREAK_MINUTES_PER_HOUR=10';
  Lines[4] := 'LUNCH_DURATION_MINUTES=30';
  Lines[5] := 'DAILY_WORK_TARGET_MINUTES=400';
  Lines[6] := 'SYNC_INTERVAL_SECONDS=60';
  Lines[7] := 'THEME=dark';
  Lines[8] := 'LOG_LEVEL=INFO';

  SaveStringsToFile(EnvPath, Lines, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    CreateDefaultEnv(ExpandConstant('{app}\.env'));
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
end;
