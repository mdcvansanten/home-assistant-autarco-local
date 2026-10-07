#!/usr/bin/env bash
# Deploy the BLE beta branch to Home Assistant OS; keep a rollback backup.
set -euo pipefail

autarco_branch="codex/ble-transport-20261005"
autarco_repo="mdcvansanten/home-assistant-autarco-local"
autarco_config="/config"
autarco_restart="yes"

while (($#)); do
  case "$1" in
    --config-dir)
      [[ $# -ge 2 ]] || { echo "--config-dir vereist een pad" >&2; exit 2; }
      autarco_config="$2"; shift 2 ;;
    --no-restart) autarco_restart="no"; shift ;;
    -h|--help)
      echo "Gebruik: bash deploy_ble_from_github.sh [--config-dir /config] [--no-restart]"
      exit 0 ;;
    *) echo "Onbekende optie: $1" >&2; exit 2 ;;
  esac
done

[[ -d "$autarco_config" ]] || { echo "HA-configuratiemap ontbreekt: $autarco_config" >&2; exit 1; }
command -v curl >/dev/null || { echo "curl ontbreekt; gebruik de Home Assistant Terminal & SSH-add-on." >&2; exit 1; }
if command -v python3 >/dev/null; then
  autarco_python="$(command -v python3)"
elif [[ -x "$autarco_config/solis-ble-venv/bin/python" ]]; then
  autarco_python="$autarco_config/solis-ble-venv/bin/python"
else
  echo "Python 3 ontbreekt; de bestaande solis-ble-venv is ook niet gevonden." >&2
  exit 1
fi
if [[ "$autarco_restart" == "yes" ]] && ! command -v ha >/dev/null; then
  echo "HA CLI ontbreekt. Gebruik de HA-terminal of voeg --no-restart toe." >&2
  exit 1
fi

autarco_temp="$(mktemp -d -t autarco-ble-deploy.XXXXXX)"
trap 'rm -rf -- "$autarco_temp"' EXIT
echo "GitHub ophalen: $autarco_repo → $autarco_branch"
curl --fail --location --silent --show-error --retry 2 \
  --connect-timeout 15 --max-time 180 \
  "https://codeload.github.com/$autarco_repo/zip/refs/heads/$autarco_branch" \
  --output "$autarco_temp/source.zip"

"$autarco_python" - "$autarco_temp" "$autarco_config" "$autarco_restart" "$autarco_repo" "$autarco_branch" <<'PY'
from datetime import datetime, timezone
import hashlib
import json
import os
import runpy
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import uuid
import zipfile

temporary, config = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
restart, repository, branch = sys.argv[3:]
archive = temporary / "source.zip"
unpacked = temporary / "source"
expected_version = "0.7.0b3"

# Validate every archive member before extracting or changing HA files.
with zipfile.ZipFile(archive) as bundle:
    entries = bundle.infolist()
    if not entries or sum(item.file_size for item in entries) > 50 * 1024 * 1024:
        raise SystemExit("GitHub-pakket is leeg of onverwacht groot")
    names, roots = set(), set()
    for item in entries:
        path = PurePosixPath(item.filename)
        mode = item.external_attr >> 16
        if (not path.parts or path.is_absolute() or ".." in path.parts
                or "\\" in item.filename or stat.S_ISLNK(mode)
                or item.filename in names):
            raise SystemExit("GitHub-pakket bevat een onveilig of dubbel pad")
        names.add(item.filename)
        roots.add(path.parts[0])
    if len(roots) != 1:
        raise SystemExit("GitHub-pakket bevat meerdere projectmappen")
    bundle.extractall(unpacked)

source = unpacked / roots.pop() / "custom_components" / "autarco_local"
required = ["manifest.json", "__init__.py", "ble_client.py", "ble_protocol.py",
            "coordinator.py", "config_flow.py", "runtime_quality.py",
            "services.yaml", "frontend/autarco-dashboard-ble.js"]
if not all((source / name).is_file() for name in required):
    raise SystemExit("De opgehaalde branch bevat niet de volledige Bluetooth-integratie")
for file in source.rglob("*.json"):
    json.loads(file.read_text(encoding="utf-8"))
manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
if manifest.get("domain") != "autarco_local" or manifest.get("version") != expected_version:
    raise SystemExit("Onverwachte integratie of versie; er is niets geïnstalleerd")

cleanup_path = source.parents[1] / "tools" / "legacy_ping_cleanup.py"
if not cleanup_path.is_file():
    raise SystemExit("De branch mist de cleanup voor de oude pingmeldingen")
cleanup = runpy.run_path(str(cleanup_path))
legacy_changes = cleanup["plan_cleanup"](config)

target = config / "custom_components" / "autarco_local"
if target.parent.is_symlink() or target.is_symlink():
    raise SystemExit("De componentmap is een symlink; installatie afgebroken")
if target.exists() and not target.is_dir():
    raise SystemExit("De componentmap is geen map; installatie afgebroken")
target.parent.mkdir(parents=True, exist_ok=True)
unique = uuid.uuid4().hex[:10]
timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = config / "backups" / f"autarco_ble_{timestamp}_{unique}"
stage = target.parent / (".autarco_ble_new_" + unique)
old = target.parent / (".autarco_ble_old_" + unique)
had_previous = target.exists()
ignore = shutil.ignore_patterns("__pycache__", "*.pyc")

backup.mkdir(parents=True)
if had_previous:
    shutil.copytree(target, backup / "autarco_local", ignore=ignore)
    print(f"Back-up: {backup / 'autarco_local'}", flush=True)
for file, (before, after, identifiers) in legacy_changes.items():
    saved = backup / "legacy_notifications" / file.relative_to(config)
    saved.parent.mkdir(parents=True, exist_ok=True)
    saved.write_bytes(before)
(backup / "deployment.json").write_text(json.dumps({
    "repository": repository, "branch": branch, "version": expected_version,
    "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    "target": str(target), "had_previous_component": had_previous,
    "deployed_at": datetime.now(timezone.utc).isoformat(),
}, indent=2) + "\n", encoding="utf-8")

swapped = False
changed_legacy = []
try:
    shutil.copytree(source, stage, ignore=ignore)
    if had_previous:
        os.replace(target, old)
    try:
        os.replace(stage, target)
        swapped = True
        for file, (before, after, identifiers) in legacy_changes.items():
            cleanup["replace_file"](file, before, after)
            changed_legacy.append(file)
            print("Oude ping/Modbus-push uitgeschakeld: " + ", ".join(identifiers), flush=True)
        if restart == "yes":
            print("Home Assistant-configuratie controleren…", flush=True)
            subprocess.run(["ha", "core", "check"], check=True, timeout=240)
    except BaseException:
        if swapped and target.exists():
            shutil.rmtree(target)
        if old.exists():
            os.replace(old, target)
        for file in reversed(changed_legacy):
            before, after, _ = legacy_changes[file]
            cleanup["replace_file"](file, after, before)
        print("Deploy afgebroken; de oorspronkelijke component en gewijzigde meldingsconfiguratie zijn hersteld. HA is niet herstart.",
              file=sys.stderr, flush=True)
        raise
    if old.exists():
        shutil.rmtree(old)
finally:
    if stage.exists():
        shutil.rmtree(stage)

print(f"Autarco Local {expected_version} geïnstalleerd vanuit {branch}.", flush=True)
if restart == "yes":
    print("Home Assistant herstarten…", flush=True)
    try:
        subprocess.run(["ha", "core", "restart"], check=True, timeout=120)
    except (subprocess.SubprocessError, OSError) as error:
        raise SystemExit("De component is geïnstalleerd, maar de herstart is niet bevestigd. "
                         "Controleer HA en herstart zo nodig handmatig.") from error
    print("Herstart aangevraagd. Wacht tot Home Assistant weer beschikbaar is.", flush=True)
else:
    print("Controleer de HA-configuratie en herstart Home Assistant handmatig.", flush=True)
print("Daarna: Instellingen → Apparaten & diensten → Autarco Local → ⋮ → Herconfigureren.")
print("Kies Bluetooth met wifi-terugval (beta). Behoud het logger-IP en de Modbus-poort.")
print("Verbreek vooraf de lokale Solis-appverbinding.")
print("De tijdelijke download en uitpakmap worden nu opgeruimd.")
PY
