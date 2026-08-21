from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "autarco_local"
    / "energy_logic.py"
)
spec = importlib.util.spec_from_file_location("autarco_energy_logic_test", MODULE_PATH)
assert spec and spec.loader
energy_logic = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = energy_logic
spec.loader.exec_module(energy_logic)


class EnergyLogicTests(unittest.TestCase):
    def base_registers(self) -> dict[int, int]:
        return {
            43010: 100,
            43011: 20,
            43018: 10,
            43024: 40,
            43027: 1000,
            43110: 1,  # self-use
            43137: 20,
            43141: 0,
            43142: 0,
        }

    def test_healthy_soc_relationship_is_not_blocked(self) -> None:
        health = energy_logic.configuration_health(self.base_registers())
        self.assertEqual("healthy", health["state"])
        self.assertEqual(0, health["blocking"])

    def test_reserve_below_minimum_blocks_configuration(self) -> None:
        registers = self.base_registers()
        registers[43024] = 10
        health = energy_logic.configuration_health(registers)
        self.assertEqual("blocked", health["state"])
        self.assertEqual(1, health["blocking"])
        self.assertEqual("reserve_below_minimum", health["findings"][0]["code"])

    def test_self_use_is_detected_as_primary_scenario(self) -> None:
        result = energy_logic.evaluate_scenarios(self.base_registers())
        self.assertEqual("self_use", result["primary"])
        self.assertIn("self_use", result["active"])

    def test_time_of_use_has_priority_when_active(self) -> None:
        registers = self.base_registers()
        registers[43110] = (1 << 0) | (1 << 1)
        result = energy_logic.evaluate_scenarios(registers)
        self.assertEqual("time_of_use", result["primary"])
        self.assertIn("time_of_use", result["active"])

    def test_scenario_readiness_is_blocked_by_invalid_configuration(self) -> None:
        registers = self.base_registers()
        registers[43024] = 10
        result = energy_logic.evaluate_scenarios(registers)
        self.assertEqual("blocked", result["configuration_health"])
        self.assertTrue(
            all(
                scenario["readiness"]
                in ("blocked_by_configuration", "unavailable")
                for scenario in result["scenarios"]
            )
        )


if __name__ == "__main__":
    unittest.main()
