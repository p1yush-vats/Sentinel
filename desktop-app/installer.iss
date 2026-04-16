; SENTINEL Desktop App - Inno Setup Installer Script
; Save as: desktop-app\installer.iss
; Build with: Open in Inno Setup Compiler and press F9

#define MyAppName "SENTINEL"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "SENTINEL"
#define MyAppExeName "SENTINEL.exe"
#define MyAppIcon "assets\iso\sentinel.ico"
#define BuildDir "dist\main.dist"

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

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
Name: "startmenuicon"; Description: "Create a Start Menu shortcut"; GroupDescription: "Additional icons:"

[Files]
; Main executable and all compiled dependencies
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon

; Uninstaller in Start Menu
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Offer to launch app after install
Filename: "{app}\{#MyAppExeName}"; Description: "Launch SENTINEL now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up local data folder on uninstall (optional - comment out to keep user data)
; Type: filesandordirs; Name: "{userdocs}\.sentinel"
