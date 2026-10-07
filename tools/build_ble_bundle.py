#!/usr/bin/env python3
"""Build the tested, integrity-checked standalone installation bundle."""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    version = json.loads((root / "custom_components/autarco_local/manifest.json").read_text())["version"]
    prefix = f"autarco-local-ble-{version}"
    paths = []
    for directory in ["custom_components/autarco_local", "tests", "tools"]:
        paths.extend(file for file in (root / directory).rglob("*")
                     if file.is_file() and "__pycache__" not in file.parts and file.suffix != ".pyc")
    paths.extend(root / name for name in ["README.md", "LICENSE", "pytest.ini", "docs/bluetooth-beta.md"])
    contents = {str(file.relative_to(root)): file.read_bytes() for file in sorted(paths)}
    manifest = {"version": version, "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            archive.writestr(f"{prefix}/{name}", data)
        archive.writestr(f"{prefix}/bundle_manifest.json", json.dumps(manifest, indent=2) + "\n")
    print(f"{args.output.resolve()}: {len(contents)} files; version {version}")


if __name__ == "__main__":
    main()
