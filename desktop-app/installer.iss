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
; Disable antivirus warning prompt
DisableWelcomePage=no
DisableDirPage=no
; Show "Run as Administrator" prompt if needed (pynput needs it)
; Users can also right-click → Run as administrator manually

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Create a &desktop shortcut";     GroupDescription: "Additional icons:"
Name: "startmenuicon";  Description: "Create a &Start Menu shortcut";  GroupDescription: "Additional icons:"
Name: "startupicon";    Description: "Start SENTINEL with &Windows";   GroupDescription: "Startup:"; Flags: unchecked

[Files]
; The single-file exe (PyInstaller output)
Source: "dist\SENTINEL.exe"; DestDir: "{app}"; Flags: ignoreversion

; .env config (users can edit this after install)
; If .env doesn't exist yet, create a default one via [INI] section below
Source: "dist\.env"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists('dist\.env')

[Icons]
; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}";
  Filename: "{app}\{#MyAppExeName}";
  IconFilename: "{app}\{#MyAppExeName}";
  Tasks: desktopicon

; Start Menu shortcut
Name: "{group}\{#MyAppName}";
  Filename: "{app}\{#MyAppExeName}";
  IconFilename: "{app}\{#MyAppExeName}";
  Tasks: startmenuicon

; Startup shortcut
Name: "{userstartup}\{#MyAppName}";
  Filename: "{app}\{#MyAppExeName}";
  Tasks: startupicon

; Uninstaller in Start Menu
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[INI]
; Create a default .env if one wasn't bundled
; Edit API_BASE_URL to point at your production server
Filename: "{app}\.env"; Section: ""; Key: "API_BASE_URL";              String: "https://sentinel-ny7w.onrender.com"; Flags: createkeyifdoesntexist
Filename: "{app}\.env"; Section: ""; Key: "PORTAL_URL";                String: "https://sentinel-self.vercel.app/";  Flags: createkeyifdoesntexist
Filename: "{app}\.env"; Section: ""; Key: "WORK_MINUTES_PER_HOUR";     String: "50";    Flags: createkeyifdoesntexist
Filename: "{app}\.env"; Section: ""; Key: "BREAK_MINUTES_PER_HOUR";    String: "10";    Flags: createkeyifdoesntexist
Filename: "{app}\.env"; Section: ""; Key: "LUNCH_DURATION_MINUTES";    String: "30";    Flags: createkeyifdoesntexist
Filename: "{app}\.env"; Section: ""; Key: "DAILY_WORK_TARGET_MINUTES"; String: "400";   Flags: createkeyifdoesntexist
Filename: "{app}\.env"; Section: ""; Key: "SYNC_INTERVAL_SECONDS";     String: "60";    Flags: createkeyifdoesntexist
Filename: "{app}\.env"; Section: ""; Key: "THEME";                     String: "dark";  Flags: createkeyifdoesntexist
Filename: "{app}\.env"; Section: ""; Key: "LOG_LEVEL";                 String: "INFO";  Flags: createkeyifdoesntexist

[Run]
; Offer to launch after install
Filename: "{app}\{#MyAppExeName}";
  Description: "Launch SENTINEL now";
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the .env on uninstall (contains API keys — clean up properly)
Type: files; Name: "{app}\.env"
; Optional: remove local database on uninstall (comment out to keep user data)
; Type: filesandordirs; Name: "{userappdata}\.sentinel"

[Code]
// Check if .NET or VC++ redistributable is needed (pynput hooks need MSVC runtime)
// This is usually already present on Windows 10/11 but check anyway.
function InitializeSetup(): Boolean;
begin
  Result := True;
  // You could add version checks here if needed
end;
