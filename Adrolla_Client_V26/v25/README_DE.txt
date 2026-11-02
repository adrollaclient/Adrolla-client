ADROLLA CLIENT V25
==================

START
1. Diesen Ordner vollständig entpacken.
2. START_ADROLLA.bat doppelklicken. Beim ersten Start wird bei Bedarf Python installiert – das dauert einige Minuten.

VORAUSSETZUNGEN
- Windows 10 oder Windows 11
- Python 3 mit Tkinter: Fehlt Python, installiert START_ADROLLA.bat beim ersten Start automatisch die neueste Version von python.org (nur für deinen Benutzer, ohne Admin-Rechte; Internet nötig)
- Pillow und minecraft-launcher-lib werden beim Start automatisch installiert
- Für Modrinth-Suche und Downloads ist eine Internetverbindung nötig.

FUNKTIONEN
- Bis zu 10 Profile mit eigener Minecraft-Version, eigenem Mod-Loader und eigenem Ordner (Mods, Texture Packs, Welten)
- Mod-Loader Fabric, Quilt, Forge und NeoForge werden beim Spielstart automatisch installiert
- PvP, SMP, BedWars, Survival, SkyWars und eigene Setups als getrennte Profile verwalten
- Vorlagen wie PvP und SMP über den linken Menüpunkt „Vorlagen“ als Profile hinzufügen
- Minecraft-Versionen von 26.3 bis zu älteren Java-Releases auswählen und direkt starten
- Mods (.jar) und Texture Packs (.zip) im Minecraft-Ordner verwalten
- Mods direkt in der Profilübersicht für das jeweilige Profil öffnen und hinzufügen
- Die ausgewählte Minecraft-Java-Version direkt aus Adrolla starten
- Modrinth-Katalog mit Icons, Sortierung und „Mehr laden“: passende Version zu Minecraft und Loader, Pflicht-Abhängigkeiten automatisch, Prüfsummen-Kontrolle (SHA-512/SHA-1), Download in die Bibliothek und ins Profil
- Oben rechts Online- oder Offline-Modus wählen
- Im Offline-Modus Minecraft ohne Microsoft-Anmeldung mit lokalem Spielerprofil starten; Multiplayer und Chat sind dabei deaktiviert
- Unten links über das Profil-Symbol Microsoft-Accounts anmelden, abmelden, hinzufügen oder wechseln
- Oberfläche, Sprache und Fenstermodus anpassen

HINWEISE
- Einstellungen und Profile werden in config.json gespeichert.
- Zum Verwalten lokaler Profile und Mods ist keine Adrolla-Client-ID nötig.
- Die Microsoft-Anmeldung nutzt standardmäßig die Minecraft-Java-Anmeldung und braucht keine eigene App-Client-ID. Firefox öffnet die Microsoft-Anmeldung; anschließend die vollständige Rücksprung-URL aus der Adressleiste in Adrolla einfügen.
- Für eine eigene Microsoft-App-Client-ID ist zusätzlich die Redirect-URI `http://localhost:53682` unter „Mobile und Desktopanwendungen“ sowie der Public Client Flow erforderlich.
- Microsoft-Konten bleiben angemeldet: Das Erneuerungstoken wird mit Windows DPAPI verschlüsselt gespeichert und beim nächsten Start erneuert.
- Online-Multiplayer ist nach erfolgreicher Microsoft-Anmeldung mit einer Minecraft-Java-Lizenz verfügbar.
- Der Schalter Online/Offline oben rechts steuert beim direkten Start, ob Multiplayer und Chat in Minecraft aktiviert sind.
- Beim ersten Start einer Version lädt Adrolla die Minecraft-Dateien herunter; dafür ist Internet erforderlich.
- Jedes Profil liegt unter `%APPDATA%\Adrolla Client\Profiles\<Profilname>`; Minecraft-Dateien (Versionen, Bibliotheken) bleiben gemeinsam in `%APPDATA%\.minecraft`.
- Die Adrolla-Bibliothek liegt unter `%APPDATA%\Adrolla Client\Mod Library` und ordnet Downloads nach Minecraft-Version.
- Vorhandene Spielmodus-Presets werden beim ersten Start einmalig in Profile umgewandelt; gespeicherte Mods werden den jeweiligen Profilen zugeordnet.
- Forge und NeoForge brauchen für die Installation ein installiertes Java im PATH.
- Mods, die vor V19 in `%APPDATA%\.minecraft\mods` lagen, werden nicht mehr geladen: in den Profil-Ordner verschieben („Ordner öffnen“ im Mod Manager).
- Für offizielle Minecraft-Online-Dienste und Multiplayer wird weiterhin ein
  gültiges Minecraft-Konto benötigt.

EXE ERSTELLEN
BUILD_EXE.bat startet den PyInstaller-Build. Die fertige Anwendung wird unter
dist abgelegt.

AUTO-UPDATE
- In config.json bei "update_url" die https-Adresse deiner update.json eintragen (leer = aus; "auto_update": false schaltet es ab).
- Neues Release bauen: python make_release.py https://.../Adrolla_Client_V26.zip (APP_VERSION in main.py vorher erhöhen), ZIP und update.json hochladen.
- Der Client prüft beim Start, fragt nach, prüft SHA-256, ersetzt die Dateien (mit Backup) und startet neu. config.json bleibt erhalten.
