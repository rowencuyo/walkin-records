; Inno Setup Script for International Student Services
; This script takes the PyInstaller output and creates a professional Windows installer.

[Setup]
; App Metadata
AppName=International Student Services
AppVersion=1.0.0
AppPublisher=International Student Services
AppPublisherURL=https://example.com
AppSupportURL=https://example.com
AppUpdatesURL=https://example.com

; Installation Settings
DefaultDirName={autopf}\International Student Services
DefaultGroupName=International Student Services
DisableProgramGroupPage=yes

; Output Settings (Where the Setup.exe goes)
OutputDir=dist
OutputBaseFilename=ISS_Setup_v1.0.0
SetupIconFile=assets\icons\iss.ico
Compression=lzma
SolidCompression=yes

; Admin privileges required because we install to Program Files
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; IMPORTANT: This points to the folder PyInstaller generated.
; The asterisk (*) means "grab everything inside this folder".
Source: "dist\ISS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu icon
Name: "{group}\International Student Services"; Filename: "{app}\ISS.exe"; IconFilename: "{app}\ISS.exe"
; Desktop Shortcut (tied to the task checkbox)
Name: "{autodesktop}\International Student Services"; Filename: "{app}\ISS.exe"; Tasks: desktopicon; IconFilename: "{app}\ISS.exe"

[Run]
; Option to launch app after install finishes
Filename: "{app}\ISS.exe"; Description: "{cm:LaunchProgram,International Student Services}"; Flags: nowait postinstall skipifsilent
