"""Brand-neutral energy configuration logic used by Autarco Local.

The module intentionally contains no Home Assistant or Modbus client imports.
It converts the validated Autarco/Solis-compatible holding-register snapshot into
canonical settings, evaluates cross-setting relations and derives user-facing
operating scenarios. Keeping this layer pure makes it reusable by a future EMS.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Final, Mapping


SETTING_REGISTERS: Final[dict[str, int]] = {
    "overcharge_soc": 43010,
    "minimum_soc": 43011,
    "force_charge_soc": 43018,
    "reserve_soc": 43024,
    "force_charge_power_limit": 43027,
    "storage_mode": 43110,
    "off_grid_minimum_soc": 43137,
    "scheduled_charge_current": 43141,
    "scheduled_discharge_current": 43142,
}

STORAGE_MODE_BITS: Final[dict[str, int]] = {
    "self_use": 0,
    "time_of_use": 1,
    "off_grid": 2,
    "reserve_mode": 4,
    "allow_grid_charge": 5,
    "feed_in_priority": 6,
}

SEVERITY_INFO: Final = "info"
SEVERITY_WARNING: Final = "warning"
SEVERITY_BLOCKING: Final = "blocking"

READINESS_GUIDED: Final = "guided"
READINESS_PENDING: Final = "pending_validation"
READINESS_UNAVAILABLE: Final = "unavailable"


@dataclass(frozen=True, slots=True)
class RelationFinding:
    """One evaluated relationship between settings."""

    code: str
    severity: str
    title: str
    message: str
    related_settings: tuple[str, ...]
    blocks_write: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["related_settings"] = list(self.related_settings)
        return data


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    """Describe a user-facing operating scenario."""

    key: str
    name: str
    goal: str
    description: str
    related_settings: tuple[str, ...]
    readiness: str
    ems_capability: str
    safety_note: str


SCENARIOS: Final[tuple[ScenarioDefinition, ...]] = (
    ScenarioDefinition(
        key="self_use",
        name="Normaal zelfgebruik",
        goal="Huis eerst → accu → net",
        description=(
            "Dagelijks standaardbedrijf waarbij lokale productie eerst voor het huis "
            "en de batterij wordt gebruikt."
        ),
        related_settings=("self_use", "minimum_soc", "reserve_mode", "reserve_soc"),
        readiness=READINESS_GUIDED,
        ems_capability="self_consumption",
        safety_note="Mode-writes blijven vergrendeld tot de volledige work-mode transactie is gevalideerd.",
    ),
    ScenarioDefinition(
        key="reserve",
        name="Accu vasthouden",
        goal="Energie bewaren tot gekozen reserve-SOC",
        description=(
            "Beschermt een ingestelde batterijreserve voor later gebruik zonder het "
            "normale dagelijkse beeld onnodig technisch te maken."
        ),
        related_settings=("reserve_mode", "reserve_soc", "minimum_soc"),
        readiness=READINESS_PENDING,
        ems_capability="battery_reserve",
        safety_note="Reserve SOC mag nooit lager zijn dan Minimum SOC.",
    ),
    ScenarioDefinition(
        key="manual_grid_charge",
        name="Nu laden vanaf het net",
        goal="Handmatig laden tot gekozen doel-SOC",
        description=(
            "Toekomstige gebruikersactie voor gecontroleerd netladen, onafhankelijk "
            "van prijs, PV of andere EMS-signalen."
        ),
        related_settings=(
            "allow_grid_charge",
            "force_charge_soc",
            "force_charge_power_limit",
            "minimum_soc",
        ),
        readiness=READINESS_PENDING,
        ems_capability="manual_grid_charge",
        safety_note=(
            "Pas activeerbaar nadat start, stop, doel-SOC, timeout en herstel van de "
            "oorspronkelijke mode hardwarematig zijn bewezen."
        ),
    ),
    ScenarioDefinition(
        key="time_of_use",
        name="Nacht-/tijdladen",
        goal="Laden of ontladen binnen ingestelde tijdvakken",
        description=(
            "Groepeert Time of Use, laad-/ontlaadstroom en tijdsloten tot één logische "
            "gebruikersflow."
        ),
        related_settings=(
            "time_of_use",
            "scheduled_charge_current",
            "scheduled_discharge_current",
        ),
        readiness=READINESS_PENDING,
        ems_capability="scheduled_dispatch",
        safety_note="Tijdslot-writes blijven geblokkeerd tot read-back en mode-herstel zijn gevalideerd.",
    ),
    ScenarioDefinition(
        key="feed_in_priority",
        name="Maximaal terugleveren",
        goal="PV-export krijgt voorrang",
        description=(
            "Presenteert terugleverprioriteit als scenario in plaats van als los work-mode bit."
        ),
        related_settings=("feed_in_priority", "self_use", "time_of_use"),
        readiness=READINESS_PENDING,
        ems_capability="feed_in_priority",
        safety_note="Work-mode bits moeten als één atomaire toestand worden behandeld.",
    ),
    ScenarioDefinition(
        key="peak_shaving",
        name="Peak shaving",
        goal="Netpiek begrenzen",
        description=(
            "EMS-scenario voor een dynamische importlimiet op basis van betrouwbare meter- "
            "en batterijdata."
        ),
        related_settings=("minimum_soc",),
        readiness=READINESS_UNAVAILABLE,
        ems_capability="grid_import_limit",
        safety_note="Benodigde Autarco-registers zijn nog niet hardwarematig gemapt.",
    ),
    ScenarioDefinition(
        key="backup_reserve",
        name="Backupreserve",
        goal="Vaste noodreserve beschikbaar houden",
        description=(
            "Maakt de relatie tussen Battery Reserve, Reserve SOC en Minimum SOC begrijpelijk."
        ),
        related_settings=("reserve_mode", "reserve_soc", "minimum_soc", "off_grid_minimum_soc"),
        readiness=READINESS_PENDING,
        ems_capability="backup_reserve",
        safety_note="Netuitvalgedrag en EPS/off-grid randvoorwaarden blijven leidend.",
    ),
    ScenarioDefinition(
        key="battery_maintenance",
        name="Onderhoud / battery healing",
        goal="Accu gecontroleerd naar een onderhoudstoestand brengen",
        description=(
            "Expert-scenario voor toekomstig gecontroleerd balanceren/herstellen van batterijmodules."
        ),
        related_settings=(
            "allow_grid_charge",
            "force_charge_power_limit",
            "minimum_soc",
            "off_grid_minimum_soc",
        ),
        readiness=READINESS_UNAVAILABLE,
        ems_capability="battery_maintenance",
        safety_note="Alleen beschikbaar nadat batterij- en BMS-afhankelijkheden zijn gevalideerd.",
    ),
)


def _u16(registers: Mapping[int, int], address: int) -> int | None:
    value = registers.get(address)
    return None if value is None else int(value)


def _bit(registers: Mapping[int, int], address: int, bit: int) -> bool | None:
    value = _u16(registers, address)
    return None if value is None else bool(value & (1 << bit))


def normalized_settings(registers: Mapping[int, int]) -> dict[str, Any]:
    """Return a brand-neutral setting snapshot from validated holding registers."""
    storage_mode = _u16(registers, SETTING_REGISTERS["storage_mode"])
    data: dict[str, Any] = {
        "overcharge_soc": _u16(registers, SETTING_REGISTERS["overcharge_soc"]),
        "minimum_soc": _u16(registers, SETTING_REGISTERS["minimum_soc"]),
        "force_charge_soc": _u16(registers, SETTING_REGISTERS["force_charge_soc"]),
        "reserve_soc": _u16(registers, SETTING_REGISTERS["reserve_soc"]),
        "force_charge_power_limit": _u16(
            registers, SETTING_REGISTERS["force_charge_power_limit"]
        ),
        "storage_mode_raw": storage_mode,
        "off_grid_minimum_soc": _u16(
            registers, SETTING_REGISTERS["off_grid_minimum_soc"]
        ),
    }
    charge_current_raw = _u16(registers, SETTING_REGISTERS["scheduled_charge_current"])
    discharge_current_raw = _u16(
        registers, SETTING_REGISTERS["scheduled_discharge_current"]
    )
    data["scheduled_charge_current"] = (
        None if charge_current_raw is None else round(charge_current_raw * 0.1, 1)
    )
    data["scheduled_discharge_current"] = (
        None if discharge_current_raw is None else round(discharge_current_raw * 0.1, 1)
    )
    for key, bit in STORAGE_MODE_BITS.items():
        data[key] = _bit(registers, SETTING_REGISTERS["storage_mode"], bit)
    return data


def evaluate_relations(registers: Mapping[int, int]) -> list[RelationFinding]:
    """Evaluate proven safety rules and useful dependency guidance."""
    settings = normalized_settings(registers)
    findings: list[RelationFinding] = []

    reserve_soc = settings["reserve_soc"]
    minimum_soc = settings["minimum_soc"]
    if reserve_soc is not None and minimum_soc is not None and reserve_soc < minimum_soc:
        findings.append(
            RelationFinding(
                code="reserve_below_minimum",
                severity=SEVERITY_BLOCKING,
                title="Reserve SOC lager dan Minimum SOC",
                message=(
                    f"Reserve SOC is {reserve_soc}% en Minimum SOC is {minimum_soc}%. "
                    "Autarco Local blokkeert scenario-writes tot Reserve SOC minimaal "
                    "gelijk is aan Minimum SOC."
                ),
                related_settings=("reserve_soc", "minimum_soc"),
                blocks_write=True,
            )
        )

    work_modes = [
        key
        for key in ("self_use", "feed_in_priority", "off_grid")
        if settings.get(key) is True
    ]
    if len(work_modes) > 1:
        findings.append(
            RelationFinding(
                code="multiple_work_modes",
                severity=SEVERITY_WARNING,
                title="Meerdere work-mode bits actief",
                message=(
                    "Self-use, Feed-in Priority en Off-grid worden als één gekoppelde "
                    "work-mode toestand behandeld. Autarco Local zal deze toestand bij "
                    "toekomstige writes altijd volledig snapshotten en teruglezen."
                ),
                related_settings=tuple(work_modes),
                blocks_write=False,
            )
        )

    if settings.get("reserve_mode") is False and reserve_soc is not None:
        findings.append(
            RelationFinding(
                code="reserve_value_inactive",
                severity=SEVERITY_INFO,
                title="Reserve SOC momenteel niet actief",
                message="De Reserve SOC-waarde heeft pas effect wanneer Battery Reserve actief is.",
                related_settings=("reserve_mode", "reserve_soc"),
            )
        )

    scheduled_nonzero = any(
        value not in (None, 0, 0.0)
        for value in (
            settings.get("scheduled_charge_current"),
            settings.get("scheduled_discharge_current"),
        )
    )
    if settings.get("time_of_use") is False and scheduled_nonzero:
        findings.append(
            RelationFinding(
                code="tou_values_inactive",
                severity=SEVERITY_INFO,
                title="Time-of-Use instellingen niet actief",
                message=(
                    "Geplande laad-/ontlaadstromen zijn ingesteld, maar Time of Use staat uit. "
                    "De waarden blijven zichtbaar maar sturen de omvormer nu niet."
                ),
                related_settings=(
                    "time_of_use",
                    "scheduled_charge_current",
                    "scheduled_discharge_current",
                ),
            )
        )

    force_soc = settings.get("force_charge_soc")
    if force_soc is not None and minimum_soc is not None and force_soc > minimum_soc:
        findings.append(
            RelationFinding(
                code="force_charge_above_minimum",
                severity=SEVERITY_WARNING,
                title="Force-charge SOC boven Minimum SOC",
                message=(
                    f"Force-charge SOC is {force_soc}% en Minimum SOC is {minimum_soc}%. "
                    "Dit is geen automatisch schrijfverbod, maar vraagt controle omdat de "
                    "beschermingsdrempels elkaar kunnen overlappen."
                ),
                related_settings=("force_charge_soc", "minimum_soc", "allow_grid_charge"),
            )
        )

    return findings


def configuration_health(registers: Mapping[int, int]) -> dict[str, Any]:
    """Return a compact health state plus serialisable relation findings."""
    if not registers:
        return {"state": "unavailable", "findings": [], "blocking": 0, "warnings": 0}
    findings = evaluate_relations(registers)
    blocking = sum(1 for item in findings if item.severity == SEVERITY_BLOCKING)
    warnings = sum(1 for item in findings if item.severity == SEVERITY_WARNING)
    state = "blocked" if blocking else "warning" if warnings else "healthy"
    return {
        "state": state,
        "findings": [item.as_dict() for item in findings],
        "blocking": blocking,
        "warnings": warnings,
    }


def _scenario_active(key: str, settings: Mapping[str, Any]) -> bool:
    if key == "self_use":
        return settings.get("self_use") is True
    if key in ("reserve", "backup_reserve"):
        return settings.get("reserve_mode") is True
    if key == "manual_grid_charge":
        return settings.get("allow_grid_charge") is True
    if key == "time_of_use":
        return settings.get("time_of_use") is True
    if key == "feed_in_priority":
        return settings.get("feed_in_priority") is True
    return False


def evaluate_scenarios(registers: Mapping[int, int]) -> dict[str, Any]:
    """Derive scenario visibility/readiness from the current setting snapshot."""
    settings = normalized_settings(registers)
    health = configuration_health(registers)
    scenario_rows: list[dict[str, Any]] = []
    active_keys: list[str] = []

    for definition in SCENARIOS:
        active = _scenario_active(definition.key, settings)
        if active:
            active_keys.append(definition.key)
        readiness = definition.readiness
        if health["blocking"] and readiness != READINESS_UNAVAILABLE:
            readiness = "blocked_by_configuration"
        scenario_rows.append(
            {
                "key": definition.key,
                "name": definition.name,
                "goal": definition.goal,
                "description": definition.description,
                "related_settings": list(definition.related_settings),
                "readiness": readiness,
                "configured_readiness": definition.readiness,
                "active": active,
                "ems_capability": definition.ems_capability,
                "safety_note": definition.safety_note,
            }
        )

    if not registers:
        primary = "unavailable"
    elif settings.get("time_of_use") is True:
        primary = "time_of_use"
    elif settings.get("feed_in_priority") is True:
        primary = "feed_in_priority"
    elif settings.get("off_grid") is True:
        primary = "off_grid"
    elif settings.get("self_use") is True:
        primary = "self_use"
    else:
        primary = "custom"

    return {
        "primary": primary,
        "active": active_keys,
        "scenarios": scenario_rows,
        "settings": settings,
        "configuration_health": health["state"],
    }
