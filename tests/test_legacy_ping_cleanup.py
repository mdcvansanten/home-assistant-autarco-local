"""Targeted legacy-notification cleanup must preserve all other HA YAML."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("legacy_ping_cleanup", ROOT / "tools/legacy_ping_cleanup.py")
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


def test_cleanup_disables_ping_error_and_recovery_but_preserves_data_alert_and_comments():
    original = b'''# preserve this comment\ninput_boolean:\n  unrelated:\n    initial: true\nautomation:\n  - id: autarco_logger_offline_push\n    alias: "Autarco diagnose - logger offline"\n    actions: []\n  - id: 'autarco_modbus_local_push'\n    initial_state: true # keep comment\n    actions: []\n  - id: autarco_connection_recovered_push\n    actions: []\n  - id: autarco_data_missing_push\n    actions: []\n'''
    updated, identifiers = cleanup.disable_legacy_notifications(original)
    assert set(identifiers) == cleanup.LEGACY_IDS
    assert updated.count(b"initial_state: false") == 3
    assert b"false  # keep comment" in updated
    assert b"  - id: autarco_data_missing_push\n    actions: []\n" in updated
    assert updated.startswith(b"# preserve this comment\ninput_boolean:\n  unrelated:\n    initial: true\n")
    assert cleanup.disable_legacy_notifications(updated) == (updated, ())


def test_comments_script_ids_and_block_scalar_contents_are_not_modified():
    original = b'''# - id: autarco_modbus_local_push\nscript:\n  - id: autarco_logger_offline_push\n    actions: []\nautomation:\n  - id: unrelated\n    actions:\n      - data:\n          message: |-\n            - id: autarco_modbus_local_push\n              sample: this is message text\n'''
    assert cleanup.disable_legacy_notifications(original) == (original, ())


def test_root_automations_and_crlf_are_supported_without_touching_unrelated_yaml():
    original = b"- id: autarco_modbus_local_push\r\n  alias: old\r\n  actions: []\r\n- id: unrelated\r\n  actions: []\r\n"
    updated, identifiers = cleanup.disable_legacy_notifications(original)
    assert identifiers == ("autarco_modbus_local_push",)
    assert updated == original.replace(b"  alias:", b"  initial_state: false\r\n  alias:")


def test_cleanup_plan_finds_packages_and_automations_and_preserves_other_files(tmp_path):
    packages = tmp_path / "packages"
    packages.mkdir()
    legacy = packages / "autarco_diagnostics.yaml"
    legacy.write_bytes(b"automation:\n  - id: autarco_modbus_local_push\n    actions: []\n")
    other = packages / "unrelated.yaml"
    other.write_text("secret_ref: !secret something\n")
    plan = cleanup.plan_cleanup(tmp_path)
    assert list(plan) == [legacy]
    before, after, _ = plan[legacy]
    cleanup.replace_file(legacy, before, after)
    assert b"initial_state: false" in legacy.read_bytes()
    assert other.read_text() == "secret_ref: !secret something\n"
    cleanup.replace_file(legacy, after, before)
    assert legacy.read_bytes() == before
