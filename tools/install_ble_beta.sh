#!/usr/bin/env bash
# Install the exact reviewed beta archive, preserving a rollback copy.
set -euo pipefail
autarco_zip="${1:-/config/autarco-local-ble-0.7.0b2.zip}"
autarco_config="${2:-/config}"
python3 - "$autarco_zip" "$autarco_config" <<'PY'
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import uuid
import zipfile

archive, config = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
if not archive.is_file():
    raise SystemExit(f"ZIP niet gevonden: {archive}")
if not config.is_dir():
    raise SystemExit(f"Home Assistant-configuratiemap niet gevonden: {config}")
with tempfile.TemporaryDirectory(prefix="autarco-ble-install-") as temporary:
    unpacked = Path(temporary)
    with zipfile.ZipFile(archive) as bundle:
        if sum(info.file_size for info in bundle.infolist()) > 50 * 1024 * 1024:
            raise SystemExit("Installatiepakket is onverwacht groot")
        for info in bundle.infolist():
            path = Path(info.filename)
            mode = info.external_attr >> 16
            if path.is_absolute() or ".." in path.parts or "\\" in info.filename or stat.S_ISLNK(mode):
                raise SystemExit("ZIP bevat een onveilig pad")
        bundle.extractall(unpacked)
    roots = list(unpacked.glob("*/bundle_manifest.json"))
    if len(roots) != 1:
        raise SystemExit("Dit is niet het verwachte Autarco BLE-installatiepakket")
    root = roots[0].parent
    manifest = json.loads(roots[0].read_text())
    if manifest.get("version") != "0.7.0b2":
        raise SystemExit("Onverwachte pakketversie")
    actual = {str(file.relative_to(root)) for file in root.rglob("*") if file.is_file()}
    if actual != set(manifest["sha256"]) | {"bundle_manifest.json"}:
        raise SystemExit("Pakket bevat onverwachte of ontbrekende bestanden")
    for name, digest in manifest["sha256"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise SystemExit("Ongeldig verificatiepad")
        file = root / relative
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            raise SystemExit(f"Pakketcontrole mislukt: {name}")
    source = root / "custom_components" / "autarco_local"
    version = json.loads((source / "manifest.json").read_text())["version"]
    if version != "0.7.0b2":
        raise SystemExit("Onverwachte integratieversie")
    target = config / "custom_components" / "autarco_local"
    target.parent.mkdir(parents=True, exist_ok=True)
    unique = uuid.uuid4().hex[:10]
    backup = config / "backups" / ("autarco_ble_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + unique)
    if target.exists():
        backup.mkdir(parents=True)
        shutil.copytree(target, backup / "autarco_local", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    stage = target.parent / (".autarco_ble_new_" + unique)
    old = target.parent / (".autarco_ble_old_" + unique)
    try:
        shutil.copytree(source, stage, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if target.exists():
            os.replace(target, old)
        try:
            os.replace(stage, target)
        except BaseException:
            if old.exists():
                os.replace(old, target)
            raise
        if old.exists():
            shutil.rmtree(old)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print("Autarco Local 0.7.0b2 geïnstalleerd. Omvormerinstellingen zijn niet gewijzigd.")
    if backup.exists():
        print(f"Vorige integratie: {backup / 'autarco_local'}")
    print("ZIP uitgepakt; tijdelijke uitpakmap wordt nu opgeruimd. Originele ZIP blijft bewaard.")
    print("Controleer Home Assistant-configuratie en herstart HA. Kies daarna Herconfigureren → Bluetooth met wifi-terugval.")
PY
