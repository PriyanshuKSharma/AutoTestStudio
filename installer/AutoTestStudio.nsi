; ============================================================================
;  AutoTest Studio — NSIS Installer Script
;  Produces: AutoTestStudio_Setup_v1.1.0.exe
;
;  Requirements:
;    - NSIS 3.x  (https://nsis.sourceforge.io)
;    - PyInstaller output at ..\dist\AutoTestStudio\
;
;  Build:
;    makensis installer\AutoTestStudio.nsi
; ============================================================================

Unicode True

; ── Compiler flags ───────────────────────────────────────────────────────────
!define APP_NAME        "AutoTest Studio"
!define APP_EXE         "AutoTestStudio.exe"
!define APP_VERSION     "1.1.0"
!define APP_PUBLISHER   "AutoTest Studio"
!define APP_URL         "https://github.com/your-org/autoteststudio"
!define INSTALL_DIR     "$PROGRAMFILES64\AutoTest Studio"
!define UNINSTALL_KEY   "Software\Microsoft\Windows\CurrentVersion\Uninstall\AutoTestStudio"
!define DIST_DIR        "..\dist\AutoTestStudio"

; ── General ──────────────────────────────────────────────────────────────────
Name              "${APP_NAME} ${APP_VERSION}"
OutFile           "..\AutoTestStudio_Setup_v${APP_VERSION}.exe"
InstallDir        "${INSTALL_DIR}"
InstallDirRegKey  HKLM "${UNINSTALL_KEY}" "InstallLocation"
RequestExecutionLevel admin
SetCompressor     /SOLID lzma
ShowInstDetails   show
ShowUnInstDetails show

; ── Modern UI ─────────────────────────────────────────────────────────────────
!include "MUI2.nsh"
!include "FileFunc.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON   "..\assets\icon.ico"
!define MUI_UNICON "..\assets\icon.ico"

; Welcome page
!define MUI_WELCOMEPAGE_TITLE    "Welcome to AutoTest Studio Setup"
!define MUI_WELCOMEPAGE_TEXT     "This wizard will install AutoTest Studio ${APP_VERSION} on your computer.$\r$\n$\r$\nAutoTest Studio is a Python-based CAN bus test automation platform — a desktop alternative to Vector CANoe with CAPL-style scripting, live signal monitoring, fault injection, and SQLite-backed test reporting.$\r$\n$\r$\nClick Next to continue."
!insertmacro MUI_PAGE_WELCOME

; License page
!insertmacro MUI_PAGE_LICENSE "..\LICENSE.txt"

; Install directory page
!insertmacro MUI_PAGE_DIRECTORY

; Components page
!insertmacro MUI_PAGE_COMPONENTS

; Install files page
!insertmacro MUI_PAGE_INSTFILES

; Finish page
!define MUI_FINISHPAGE_RUN         "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT    "Launch AutoTest Studio"
!define MUI_FINISHPAGE_SHOWREADME  "$INSTDIR\README.md"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "View README"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ── Version info embedded in setup exe ───────────────────────────────────────
VIProductVersion  "0.1.0.0"
VIAddVersionKey   "ProductName"      "${APP_NAME}"
VIAddVersionKey   "ProductVersion"   "${APP_VERSION}"
VIAddVersionKey   "CompanyName"      "${APP_PUBLISHER}"
VIAddVersionKey   "FileDescription"  "${APP_NAME} Setup"
VIAddVersionKey   "FileVersion"      "${APP_VERSION}"
VIAddVersionKey   "LegalCopyright"   ""

; ── Components ────────────────────────────────────────────────────────────────
Section "Core Application" SEC_CORE
    SectionIn RO     ; required — cannot be deselected
    SetOutPath "$INSTDIR"

    ; Copy everything from PyInstaller dist folder
    File /r "${DIST_DIR}\*.*"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Registry — Add/Remove Programs entry
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayName"          "${APP_NAME}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayVersion"       "${APP_VERSION}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "Publisher"            "${APP_PUBLISHER}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "URLInfoAbout"         "${APP_URL}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "InstallLocation"      "$INSTDIR"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "UninstallString"      "$INSTDIR\Uninstall.exe"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayIcon"          "$INSTDIR\${APP_EXE}"
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify"             1
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair"             1

    ; Compute and store install size (KB)
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "EstimatedSize" "$0"
SectionEnd

Section "Desktop Shortcut" SEC_DESKTOP
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXE}" "" \
        "$INSTDIR\${APP_EXE}" 0 \
        SW_SHOWNORMAL "" "${APP_NAME}"
SectionEnd

Section "Start Menu Shortcut" SEC_STARTMENU
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXE}" "" \
        "$INSTDIR\${APP_EXE}" 0 \
        SW_SHOWNORMAL "" "${APP_NAME}"
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" \
        "$INSTDIR\Uninstall.exe"
SectionEnd

; ── Component descriptions ───────────────────────────────────────────────────
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_CORE}      "AutoTest Studio application files. Required."
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DESKTOP}   "Add a shortcut to your Desktop."
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_STARTMENU} "Add AutoTest Studio to the Start Menu."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ── Uninstaller ───────────────────────────────────────────────────────────────
Section "Uninstall"
    ; Remove all installed files
    RMDir /r "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"

    ; Remove registry entries
    DeleteRegKey HKLM "${UNINSTALL_KEY}"
SectionEnd
