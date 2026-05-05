; SMMM TAKİP — Inno Setup Kurulum Scripti
; Inno Setup 6 gereklidir: https://jrsoftware.org/isinfo.php

; Sürüm BUILD_KURULUM.bat'tan /DMyAppVersion=X.Y.Z şeklinde geçilir
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#define MyAppName      "SMMM Takip"
#define MyAppPublisher "SMMM"
#define MyAppExeName   "SMMM_Takip.exe"
#define MyAppURL       ""

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=no
LicenseFile=
OutputDir=..\installer_output
OutputBaseFilename=SMMTakip_Kurulum_v{#MyAppVersion}
SetupIconFile=smmm_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=yes
DisableProgramGroupPage=no
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=SMMM Beyanname ve Cari Takip Sistemi
VersionInfoProductName={#MyAppName}
ShowLanguageDialog=no
LanguageDetectionMethod=none

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Messages]
; Türkçe özel mesajlar
BeveledLabel=SMMM Takip Sistemi

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek seçenekler:"
Name: "quicklaunchicon"; Description: "Görev çubuğuna kısayol oluştur"; GroupDescription: "Ek seçenekler:"; OnlyBelowVersion: 6.1

[Files]
; PyInstaller çıktısı — dist\SMMM_Takip klasörünün tüm içeriği
Source: "..\dist\SMMM_Takip\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; data klasörü boş olarak kurulsun (kullanıcı verisi olmadan)
; (zaten PyInstaller dist içinde data/ klasörü yok ama yine de garantiye alalım)

[Dirs]
; Uygulama veri klasörü kurulumda oluşturulsun (boş)
Name: "{app}\data"

[Icons]
; Başlat Menüsü
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} Kaldır"; Filename: "{uninstallexe}"

; Masaüstü kısayolu (görev seçildiyse)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Hızlı başlatma (eski Windows)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Kurulum bittikten sonra programı başlatma seçeneği
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Kaldırırken data klasörünü sorarak sil
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\__pycache__"

; ──────────────────────────────────────────────────────────────
;  KURULUM SIRASINDA KULLANICI ADI SAYFASI
; ──────────────────────────────────────────────────────────────
[Code]
var
  KullaniciAdiPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Bu sihirbaz SMMM Takip Sistemini bilgisayarınıza kuracaktır.' + #13#10 + #13#10 +
    'Devam etmeden önce tüm diğer uygulamaları kapatmanız önerilir.' + #13#10 + #13#10 +
    'Devam etmek için İleri düğmesine tıklayın, kurulumu iptal etmek için Çıkış düğmesine tıklayın.';

  KullaniciAdiPage := CreateInputQueryPage(wpWelcome,
    'Lisans Aktivasyonu',
    'Kullanıcı adınızı girin',
    'Yöneticiniz tarafından size tanımlanan kullanıcı adını girin.' + #13#10 +
    'Bu bilgi her açılışta lisansınızı doğrulamak için kullanılacaktır.');
  KullaniciAdiPage.Add('Kullanıcı Adı:', False);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = KullaniciAdiPage.ID then
  begin
    if Trim(KullaniciAdiPage.Values[0]) = '' then
    begin
      MsgBox('Lütfen kullanıcı adınızı girin.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir, ConfigFile, Username: string;
begin
  if CurStep = ssPostInstall then
  begin
    Username  := Trim(KullaniciAdiPage.Values[0]);
    ConfigDir := ExpandConstant('{app}');
    ConfigFile := ConfigDir + '\config.ini';
    SaveStringToFile(ConfigFile,
      '[Uygulama]' + #13#10 +
      'kullanici_adi=' + Username + #13#10,
      False);
  end;
end;
