; Inno Setup Script pour ChatBot RAG - Aristote Dispatcher
; Nécessite Inno Setup 6.0 ou supérieur
; Télécharger: https://jrsoftware.org/isdl.php

#define MyAppName "ChatBot RAG - Aristote"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "DRASI"
#define MyAppURL "https://github.com/drasi"
#define MyAppExeName "ChatBotRAG.exe"

[Setup]
; Identifiant unique de l'application (générer un nouveau GUID pour votre app)
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\ChatBotRAG
DefaultGroupName={#MyAppName}
; Demande les privilèges admin uniquement si nécessaire
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=installer_output
OutputBaseFilename=ChatBotRAG_Setup_{#MyAppVersion}
; Icône de l'installateur (décommenter si vous avez une icône)
; SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Afficher la licence
; LicenseFile=LICENSE.txt
; Page de bienvenue
DisableWelcomePage=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
french.WelcomeLabel1=Bienvenue dans l'assistant d'installation de [name]
french.WelcomeLabel2=Cet assistant va installer [name/ver] sur votre ordinateur.%n%nCette application nécessite:%n- Python 3.9 ou supérieur%n- Une connexion Internet (pour télécharger les dépendances)%n- Ollama (sera installé si absent)%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Application principale
Source: "dist\ChatBotRAG.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Setup.exe"; DestDir: "{app}"; Flags: ignoreversion

; Code source Python (nécessaire pour Streamlit)
Source: "app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "launcher.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup_environment.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

; Fichier de configuration template
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

; Créer les dossiers vides
; Note: Les dossiers data/ et chroma_db/ seront créés au premier lancement

[Dirs]
Name: "{app}\data"
Name: "{app}\chroma_db"

[Icons]
; Menu Démarrer
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Lancer ChatBot RAG"
Name: "{group}\Configurer l'environnement"; Filename: "{app}\Setup.exe"; Comment: "Réinstaller les dépendances"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Bureau
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "Lancer ChatBot RAG"

[Run]
; Proposer de configurer l'environnement après l'installation
Filename: "{app}\Setup.exe"; Description: "Configurer l'environnement Python (recommandé)"; Flags: nowait postinstall skipifsilent
; Proposer de lancer l'application
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent unchecked

[Code]
var
  PythonPage: TInputOptionWizardPage;
  PythonInstalled: Boolean;

// Vérifie si Python est installé
function IsPythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
  if not Result then
    Result := Exec('python3', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
  if not Result then
    Result := Exec('py', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

// Initialisation
procedure InitializeWizard;
begin
  PythonInstalled := IsPythonInstalled;

  // Crée une page personnalisée si Python n'est pas installé
  if not PythonInstalled then
  begin
    PythonPage := CreateInputOptionPage(wpWelcome,
      'Python requis',
      'Python 3.9 ou supérieur est nécessaire',
      'Python n''a pas été détecté sur votre système. ' +
      'Veuillez installer Python avant de continuer.' + #13#10 + #13#10 +
      'Télécharger Python: https://www.python.org/downloads/' + #13#10 + #13#10 +
      'Assurez-vous de cocher "Add Python to PATH" lors de l''installation.',
      True, False);
    PythonPage.Add('J''ai installé Python et je souhaite continuer');
  end;
end;

// Vérification avant installation
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  // Si on est sur la page Python personnalisée
  if (not PythonInstalled) and (CurPageID = PythonPage.ID) then
  begin
    // Revérifier si Python est maintenant installé
    if IsPythonInstalled then
    begin
      PythonInstalled := True;
      Result := True;
    end
    else if PythonPage.Values[0] then
    begin
      // L'utilisateur a coché qu'il a installé Python
      if IsPythonInstalled then
      begin
        PythonInstalled := True;
        Result := True;
      end
      else
      begin
        MsgBox('Python n''est toujours pas détecté.' + #13#10 + #13#10 +
               'Veuillez installer Python et vous assurer qu''il est ajouté au PATH.' + #13#10 +
               'Vous devrez peut-être redémarrer l''installateur après avoir installé Python.',
               mbError, MB_OK);
        Result := False;
      end;
    end
    else
    begin
      MsgBox('Veuillez installer Python avant de continuer.', mbInformation, MB_OK);
      Result := False;
    end;
  end;
end;

// Message de bienvenue personnalisé
function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  S: String;
begin
  S := '';
  S := S + 'L''installation va:' + NewLine;
  S := S + NewLine;
  S := S + Space + '1. Copier les fichiers de l''application' + NewLine;
  S := S + Space + '2. Créer les raccourcis demandés' + NewLine;
  S := S + Space + '3. Proposer de configurer l''environnement Python' + NewLine;
  S := S + NewLine;

  if MemoDirInfo <> '' then
    S := S + MemoDirInfo + NewLine + NewLine;

  if MemoGroupInfo <> '' then
    S := S + MemoGroupInfo + NewLine + NewLine;

  if MemoTasksInfo <> '' then
    S := S + MemoTasksInfo + NewLine + NewLine;

  S := S + 'Note: La configuration de l''environnement téléchargera' + NewLine;
  S := S + 'les dépendances Python (~500 MB).' + NewLine;

  Result := S;
end;

// Nettoyage à la désinstallation
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Demande si l'utilisateur veut supprimer les données
    if MsgBox('Voulez-vous également supprimer les données de l''application ' +
              '(documents uploadés, base de données vectorielle)?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{app}\data'), True, True, True);
      DelTree(ExpandConstant('{app}\chroma_db'), True, True, True);
      DelTree(ExpandConstant('{app}\venv'), True, True, True);
      DelTree(ExpandConstant('{app}\.env'), False, True, False);
    end;
  end;
end;
