[Setup]
; Información básica que verá el usuario
AppName=Sistema Área de Alimentos
AppVersion=1.0
AppPublisher=Municipalidad de Fighiera

; IMPORTANTE: Instala en AppData del usuario para evitar problemas de permisos en Windows
DefaultDirName={userappdata}\SistemaAlimentos
PrivilegesRequired=lowest

; Carpeta donde se guardará tu instalador final y cómo se llamará
OutputDir=.\InstaladorFinal
OutputBaseFilename=Instalar_SistemaAlimentos_v1

; Compresión máxima para que el instalador pese poco
Compression=lzma
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
; Copia el ejecutable, la carpeta _internal, la carpeta data_export, imágenes y todo lo necesario
Source: "dist\SistemaAlimentos\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs


; Copia todos los archivos y subcarpetas de dependencias
Source: "dist\SistemaAlimentos\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Acceso directo en el menú de inicio
Name: "{autoprograms}\Sistema Área de Alimentos"; Filename: "{app}\SistemaAlimentos.exe"
; Acceso directo en el escritorio<
Name: "{autodesktop}\Sistema Área de Alimentos"; Filename: "{app}\SistemaAlimentos.exe"; Tasks: desktopicon

[Run]
; Casilla opcional al final de la instalación para abrir el sistema de inmediato
Filename: "{app}\SistemaAlimentos.exe"; Description: "Abrir Sistema Área de Alimentos ahora"; Flags: nowait postinstall skipifsilent