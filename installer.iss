; ============================================================================
;  X-Print Voice Changer  -  Inno Setup Installer Script
;  Kompilieren mit Inno Setup 6.x  (https://jrsoftware.org/isinfo.php)
; ============================================================================

#define MyAppName        "X-Print Voice Changer"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "X-Print"
#define MyAppURL         "https://x-print.ch"
#define MyAppExeName     "XPrint-VoiceChanger.exe"
#define VBCableURL       "https://vb-audio.com/Cable/"

[Setup]
; Eindeutige AppId -- NICHT aendern, sonst fuehlt sich Windows bei Updates ueberrascht
AppId={{F3A6B2E1-9C44-4E5B-A2D1-7F8C12340ABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\X-Print\Voice Changer
DefaultGroupName=X-Print
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=XPrint-VoiceChanger-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; Optional:
; SetupIconFile=icon.ico
; WizardImageFile=wizard.bmp
; WizardSmallImageFile=wizard-small.bmp

DisableProgramGroupPage=yes
DisableDirPage=no
ShowLanguageDialog=auto

[Languages]
Name: "german";  MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";     Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Schnellstart-Verknuepfung"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\XPrint-VoiceChanger.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md";                    DestDir: "{app}"; Flags: ignoreversion isreadme
; Falls ein Icon vorhanden ist, mitliefern:
; Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}";                   Filename: "{app}\{#MyAppExeName}"
Name: "{group}\README";                         Filename: "{app}\README.md"
Name: "{group}\VB-CABLE Download";              Filename: "{#VBCableURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";             Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

; ============================================================================
;  Pascal-Code: VB-CABLE-Erkennung + Download-Hinweis
; ============================================================================
[Code]

function IsVBCableInstalled(): Boolean;
begin
  Result :=
    RegKeyExists(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\VB-CABLE_is1') or
    RegKeyExists(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\VB-CABLE_is1') or
    RegKeyExists(HKLM, 'SOFTWARE\VB-Audio\CABLE') or
    RegKeyExists(HKLM, 'SOFTWARE\WOW6432Node\VB-Audio\CABLE');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  Msg: String;
begin
  if CurStep = ssPostInstall then
  begin
    if not IsVBCableInstalled() then
    begin
      Msg := 'VB-CABLE (Virtual Audio Cable) wurde nicht gefunden.' + #13#10 + #13#10 +
             'Dieser kostenlose Treiber wird benoetigt, um die verzerrte Stimme '     + #13#10 +
             'an Discord (oder andere Apps) weiterzuleiten.' + #13#10 + #13#10 +
             'Moechtest du die Download-Seite jetzt oeffnen?';
      if MsgBox(Msg, mbConfirmation, MB_YESNO) = IDYES then
      begin
        ShellExec('open', '{#VBCableURL}', '', '', SW_SHOW, ewNoWait, ResultCode);
      end;
    end;
  end;
end;
