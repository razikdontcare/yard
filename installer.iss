; Yard Installer Script for Inno Setup
; This script creates an installer for the Yard YouTube Downloader

#define MyAppName "Yard"
#define MyAppVersion "1.0.3"
#define MyAppPublisher "Razik"
#define MyAppURL "https://github.com/razikdontcare/yard"
#define MyAppExeName "yard.exe"

[Setup]
; App identification
AppId={{8B3C4E5D-9A2F-4B1C-8E7D-6F5A4C3B2E1D}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output settings
OutputDir=installer
OutputBaseFilename=yard-setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes

; Windows Vista or later required
MinVersion=6.1

; Installer UI
WizardStyle=modern
; SetupIconFile requires .ico format - comment out if you don't have icon.ico
; SetupIconFile=src\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Directory selection
DisableDirPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application files from flet build output
Source: "build\flutter\build\windows\x64\runner\Release\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\{#MyAppName}"

[Code]
// Check if app is running during installation
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Check if the app is running
  if CheckForMutexes('Global\YardAppMutex') then
  begin
    // App is running - ask user to close it
    MsgBox('Yard is currently running. Please close it before continuing.', mbError, MB_OK);
    Result := False;
  end
  else
  begin
    // App is not running - proceed with installation
    Result := True;
  end;
end;

// Silent uninstall of previous version
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
  UninstallString: String;
begin
  Result := '';
  
  // Check if a previous version is installed
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1', 'UninstallString', UninstallString) or
     RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1', 'UninstallString', UninstallString) then
  begin
    // Silent uninstall
    Exec(RemoveQuotes(UninstallString), '/VERYSILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
