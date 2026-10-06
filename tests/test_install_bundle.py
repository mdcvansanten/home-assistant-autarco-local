"""Install/recovery regression tests using a disposable HA config directory."""

import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bundle_and_config(tmp_path):
    archive = tmp_path / "beta.zip"
    subprocess.run([sys.executable, str(ROOT / "tools/build_ble_bundle.py"), str(archive)], check=True, capture_output=True)
    config = tmp_path / "config"
    target = config / "custom_components/autarco_local"
    target.mkdir(parents=True)
    (target / "manifest.json").write_text('{"version":"0.6.6"}')
    (target / "old_component.py").write_text("# old source")
    (config / "configuration.yaml").write_text("# preserve configuration")
    return archive, config, target


def install(archive, config):
    return subprocess.run(["bash", str(ROOT / "tools/install_ble_beta.sh"), str(archive), str(config)], capture_output=True, text=True)


def test_bundle_installs_preserves_config_and_old_component(bundle_and_config):
    archive, config, target = bundle_and_config
    result = install(archive, config)
    assert result.returncode == 0, result.stderr
    assert json.loads((target / "manifest.json").read_text())["version"] == "0.7.0b2"
    assert (config / "configuration.yaml").read_text() == "# preserve configuration"
    assert not (target / "old_component.py").exists()
    backup = list((config / "backups").glob("*/autarco_local/old_component.py"))
    assert len(backup) == 1 and backup[0].read_text() == "# old source"
    assert not list(target.parent.glob(".autarco_ble_*"))
    assert not list(target.rglob("*.pyc"))


def test_archive_traversal_rejected_before_install(bundle_and_config):
    archive, config, target = bundle_and_config
    with zipfile.ZipFile(archive, "a") as bundle:
        bundle.writestr("../outside.py", "# invalid")
    result = install(archive, config)
    assert result.returncode != 0 and "onveilig pad" in result.stderr
    assert (target / "old_component.py").read_text() == "# old source"
    assert not (config / "backups").exists()


def test_checksum_failure_rejected_before_install(bundle_and_config):
    archive, config, target = bundle_and_config
    with zipfile.ZipFile(archive) as bundle:
        files = {name: bundle.read(name) for name in bundle.namelist()}
    manifest_name = next(name for name in files if name.endswith("bundle_manifest.json"))
    manifest = json.loads(files[manifest_name])
    key = next(name for name in manifest["sha256"] if name.endswith("ble_client.py"))
    manifest["sha256"][key] = "0" * 64
    files[manifest_name] = json.dumps(manifest).encode()
    with zipfile.ZipFile(archive, "w") as bundle:
        for name, data in files.items():
            bundle.writestr(name, data)
    result = install(archive, config)
    assert result.returncode != 0 and "Pakketcontrole mislukt" in result.stderr
    assert (target / "old_component.py").read_text() == "# old source"
