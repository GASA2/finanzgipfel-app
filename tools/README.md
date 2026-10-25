# Werkzeuge für Updates

- `finanzen-app.html` – Quellfassung der App (gleich wie das claude.ai-Artifact / die Backup-HTML). Änderungen immer hier machen.
- `build_pwa.py` – erzeugt daraus die Offline-Version im Hauptordner (`index.html`, `sw.js`, `manifest.webmanifest`, `robots.txt`, `.nojekyll`).

## Ablauf für ein Update
1. Änderung in `tools/finanzen-app.html` machen (inkl. `const APP_VERSION="x.y"`).
2. Optional im Artifact testen (Artifact mit dieser Datei veröffentlichen).
3. `python3 tools/build_pwa.py` ausführen (aus dem Repo-Hauptordner). Die Cache-Version in `sw.js` ändert sich dabei automatisch.
4. Testen (z. B. `python3 -m http.server` im Hauptordner), committen, pushen.

Icons (`icon-*.png`, `apple-touch-icon.png`) sind fertige Dateien und werden vom Skript nicht verändert.
Keine persönlichen Daten ins Repository: die Daten liegen nur im localStorage des Handys.
