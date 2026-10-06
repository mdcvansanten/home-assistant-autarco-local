"""Exercise terminal deployment without a real HA host or network writes."""

import json
import os
from pathlib import Path
import subprocess
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def deployment(tmp_path):
    archive = tmp_path / "source.zip"
    source = ROOT / "custom_components/autarco_local"
    prefix = "home-assistant-autarco-local-test/custom_components/autarco_local"
    with zipfile.ZipFile(archive, "w") as bundle:
        for file in source.rglob("*"):
            if file.is_file() and "__pycache__" not in file.parts and file.suffix != ".pyc":
                bundle.write(file, f"{prefix}/{file.relative_to(source)}")
        bundle.write(ROOT / "tools/legacy_ping_cleanup.py", "home-assistant-autarco-local-test/tools/legacy_ping_cleanup.py")
    config = tmp_path / "config"
    target = config / "custom_components/autarco_local"
    target.mkdir(parents=True)
    (target / "manifest.json").write_text('{"version":"0.6.6"}')
    (target / "old_component.py").write_text("# previous source")
    (config / "configuration.yaml").write_text("# preserve HA config")
    (config / "secrets.yaml").write_text("# preserve secrets")
    commands = tmp_path / "commands"
    commands.mkdir()
    curl = commands / "curl"
    curl.write_text("""#!/usr/bin/env bash
set -eu
printf '%s\\n' "$@" > "$DEPLOY_TEST_CURL_LOG"
[[ "${DEPLOY_TEST_DOWNLOAD_FAIL:-0}" != 1 ]] || exit 22
while (($#)); do
  if [[ "$1" == --output ]]; then
    cp "$DEPLOY_TEST_ARCHIVE" "$2"
    exit 0
  fi
  shift
done
exit 1
""")
    ha = commands / "ha"
    ha.write_text("""#!/usr/bin/env bash
set -eu
echo "$*" >> "$DEPLOY_TEST_HA_LOG"
if [[ "$*" == 'core check' && "${DEPLOY_TEST_CHECK_FAIL:-0}" == 1 ]]; then exit 1; fi
if [[ "$*" == 'core restart' && "${DEPLOY_TEST_RESTART_FAIL:-0}" == 1 ]]; then exit 1; fi
""")
    curl.chmod(0o755)
    ha.chmod(0o755)
    temporary = tmp_path / "temporary"
    temporary.mkdir()
    env = dict(os.environ, PATH=f"{commands}:{os.environ['PATH']}", TMPDIR=str(temporary),
               DEPLOY_TEST_ARCHIVE=str(archive), DEPLOY_TEST_CURL_LOG=str(tmp_path / "curl.log"),
               DEPLOY_TEST_HA_LOG=str(tmp_path / "ha.log"))
    return archive, config, target, temporary, env


def deploy(deployment, *options, overrides=None):
    _, config, _, _, env = deployment
    return subprocess.run(["bash", str(ROOT / "tools/deploy_ble_from_github.sh"),
                           "--config-dir", str(config), *options],
                          env=dict(env, **(overrides or {})), capture_output=True, text=True)


def test_branch_deploy_preserves_config_backs_up_checks_restarts_and_cleans(deployment):
    _, config, target, temporary, env = deployment
    result = deploy(deployment)
    assert result.returncode == 0, result.stderr
    assert json.loads((target / "manifest.json").read_text())["version"] == "0.7.0b2"
    assert not (target / "old_component.py").exists()
    backup = list((config / "backups").glob("*/autarco_local/old_component.py"))
    assert len(backup) == 1 and backup[0].read_text() == "# previous source"
    assert (config / "configuration.yaml").read_text() == "# preserve HA config"
    assert (config / "secrets.yaml").read_text() == "# preserve secrets"
    assert Path(env["DEPLOY_TEST_HA_LOG"]).read_text().splitlines() == ["core check", "core restart"]
    assert "zip/refs/heads/codex/ble-transport-20261005" in Path(env["DEPLOY_TEST_CURL_LOG"]).read_text()
    assert not list(temporary.iterdir())
    assert not list(target.parent.glob(".autarco_ble_*"))


def test_failed_ha_check_restores_previous_component_without_restart(deployment):
    _, config, target, temporary, env = deployment
    result = deploy(deployment, overrides={"DEPLOY_TEST_CHECK_FAIL": "1"})
    assert result.returncode != 0
    assert "oorspronkelijke component" in result.stderr and "HA is niet herstart" in result.stderr
    assert (target / "old_component.py").read_text() == "# previous source"
    assert json.loads((target / "manifest.json").read_text())["version"] == "0.6.6"
    assert Path(env["DEPLOY_TEST_HA_LOG"]).read_text().splitlines() == ["core check"]
    assert len(list((config / "backups").glob("*/autarco_local"))) == 1
    assert not list(temporary.iterdir())
    assert not list(target.parent.glob(".autarco_ble_*"))


def test_failed_check_removes_new_component_when_no_previous_install(deployment):
    _, _, target, temporary, _ = deployment
    import shutil
    shutil.rmtree(target)
    result = deploy(deployment, overrides={"DEPLOY_TEST_CHECK_FAIL": "1"})
    assert result.returncode != 0
    assert not target.exists()
    assert not list(temporary.iterdir())
    assert not list(target.parent.glob(".autarco_ble_*"))


def test_no_restart_option_installs_without_calling_ha(deployment):
    _, _, target, temporary, env = deployment
    result = deploy(deployment, "--no-restart")
    assert result.returncode == 0, result.stderr
    assert json.loads((target / "manifest.json").read_text())["version"] == "0.7.0b2"
    assert not Path(env["DEPLOY_TEST_HA_LOG"]).exists()
    assert not list(temporary.iterdir())


def test_failed_download_does_not_touch_installation(deployment):
    _, config, target, temporary, _ = deployment
    result = deploy(deployment, overrides={"DEPLOY_TEST_DOWNLOAD_FAIL": "1"})
    assert result.returncode != 0
    assert (target / "old_component.py").read_text() == "# previous source"
    assert not (config / "backups").exists()
    assert not list(temporary.iterdir())


def test_unsafe_archive_rejected_before_changing_ha(deployment):
    archive, config, target, temporary, _ = deployment
    with zipfile.ZipFile(archive, "a") as bundle:
        bundle.writestr("../outside.py", "# invalid")
    result = deploy(deployment)
    assert result.returncode != 0 and "onveilig" in result.stderr
    assert (target / "old_component.py").read_text() == "# previous source"
    assert not (config / "backups").exists()
    assert not list(temporary.iterdir())


def test_failed_restart_reports_installed_files_without_claiming_success(deployment):
    _, config, target, temporary, env = deployment
    result = deploy(deployment, overrides={"DEPLOY_TEST_RESTART_FAIL": "1"})
    assert result.returncode != 0 and "herstart is niet bevestigd" in result.stderr
    assert json.loads((target / "manifest.json").read_text())["version"] == "0.7.0b2"
    assert len(list((config / "backups").glob("*/autarco_local"))) == 1
    assert Path(env["DEPLOY_TEST_HA_LOG"]).read_text().splitlines() == ["core check", "core restart"]
    assert not list(temporary.iterdir())


def legacy_package(deployment):
    _, config, _, _, _ = deployment
    packages = config / "packages"
    packages.mkdir()
    file = packages / "autarco_diagnostics.yaml"
    file.write_text("automation:\n  - id: autarco_logger_offline_push\n    actions: []\n"
                    "  - id: autarco_modbus_local_push\n    actions: []\n"
                    "  - id: autarco_connection_recovered_push\n    actions: []\n"
                    "  - id: autarco_data_missing_push\n    actions: []\n")
    return file, file.read_bytes()


def test_deploy_disables_only_known_ping_notifications_with_backup(deployment):
    file, before = legacy_package(deployment)
    _, config, _, _, _ = deployment
    result = deploy(deployment)
    assert result.returncode == 0, result.stderr
    assert file.read_bytes().count(b"initial_state: false") == 3
    assert b"  - id: autarco_data_missing_push\n    actions: []" in file.read_bytes()
    backups = list((config / "backups").glob("*/legacy_notifications/packages/autarco_diagnostics.yaml"))
    assert len(backups) == 1 and backups[0].read_bytes() == before


def test_failed_config_check_restores_notification_yaml_together_with_component(deployment):
    file, before = legacy_package(deployment)
    result = deploy(deployment, overrides={"DEPLOY_TEST_CHECK_FAIL": "1"})
    assert result.returncode != 0
    assert file.read_bytes() == before
