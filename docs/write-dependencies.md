# Dependency-aware setting writes

Autarco/Solis hybrid settings are not all independent. Some settings are only editable or effective while a parent mode is active. Autarco Local must therefore treat a setting change as a transaction instead of blindly writing one register.

## Core rule: preserve the user's original state

Before any dependent write:

1. Read a fresh snapshot of the target setting and all parent/mode registers that can be affected.
2. Store the original state.
3. If the required parent mode is already active, leave it active and do **not** restore/disable it afterwards.
4. If Autarco Local must temporarily activate the parent mode, mark that activation as integration-owned.
5. Apply the requested setting and verify it by immediate read-back.
6. Only for integration-owned temporary changes, restore the complete original mode state.
7. Verify the restored state by read-back.
8. Log target old/new values, dependency state before/after, whether a temporary activation was needed, and every verification result.

A write is not considered successful until both the target value and any required restoration have been verified.

## Failure handling

If a target write fails after Autarco Local temporarily changed a mode, restoration is still attempted in a `finally`/cleanup path.

If restoration cannot be verified, the operation must report a high-priority failure and must **not** silently claim success. The UI must tell the user which mode could not be restored.

Autarco Local must never switch a mode off merely because it was required for a setting write. A mode is switched back only when the integration itself temporarily changed it from the user's original state.

## Validated hardware dependency

### Off-grid minimum SOC (`43137`)

Hardware observation on S2.LH-MII:

- With Off-grid mode OFF, the local Installer UI hides/locks Off-grid minimum SOC and the direct `43137` Modbus write `10 -> 20` was acknowledged without a Modbus exception but read-back stayed `10`.
- In the official local Installer UI, enabling Off-grid mode first exposes the Off-grid minimum SOC field.
- The SOC can then be changed.
- Off-grid mode can subsequently be returned to its original state.

Therefore the write transaction for this setting is:

- Fresh-read current storage/work-mode register (`43110`) and target register (`43137`).
- Determine whether Off-grid mode (bit 2 of `43110`) is already active.
- If already active: leave the mode untouched, write/verify `43137`, and leave Off-grid active.
- If inactive: snapshot the complete original `43110` value, temporarily activate Off-grid, verify the active state, write/verify `43137`, then restore and verify the complete original work-mode state.

The complete mode state is preserved because activating one storage mode may affect other mutually exclusive modes (for example Self-use).

## Documented relationships that still need hardware write validation

These relationships are recorded now but must **not** yet trigger automatic parent-mode writes until validated on the supported Autarco hardware.

### Time of Use

Solis documentation states that charge/discharge times are effective only when the Time of Use switch is enabled. This applies to:

- scheduled charge current;
- scheduled discharge current;
- charge time slots;
- discharge time slots.

Policy: record `Time of Use` as a parent/effective-mode dependency. Do not automatically toggle it during writes until the local Autarco UI behaviour and Modbus write sequence are hardware-validated.

### Battery Reserve

Solis documents Reserve SOC as part of Battery Reserve mode. The local behaviour must be validated before Autarco Local automatically enables/disables Reserve mode to edit Reserve SOC.

Policy: Reserve SOC retains the backend invariant `Reserve SOC >= Minimum battery SOC`. Parent-mode automation remains disabled until validated.

### Mutually exclusive storage/work modes

Solis documents that Self-use cannot be active simultaneously with modes such as Feed-in Priority, Peak Shaving, or Off-grid. A mode change may therefore modify more than one bit/state.

Policy: any future mode-changing transaction must snapshot and restore the complete relevant work-mode state rather than assuming a single independent bit.

## Concurrency policy

During a dependent write transaction, Autarco Local serializes its own Modbus operations. Before restoration it performs a fresh read and compares the observed mode state with the expected transaction state. If an unexpected external change is detected, the integration must avoid blindly overwriting it and report a conflict for manual review.

## Current rollout policy

- No undocumented unlock registers.
- No guessed write registers.
- Read-modify-write for bitfields.
- Fresh pre-read before every write.
- Mandatory read-back after every write.
- Original user state always wins.
- Dependencies become automatically managed only after hardware validation.
