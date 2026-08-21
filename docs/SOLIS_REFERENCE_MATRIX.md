# Solis reference matrix for Autarco Local

This matrix tracks which mature Solis Modbus concepts are adopted as patterns and what still requires local Autarco validation.

| Concept | Autarco Local v0.7.0 | Hardware write status |
|---|---|---|
| Persistent Modbus connection + reconnect | Existing | Proven/read-only operation |
| Separate runtime and settings reads | Existing | Proven |
| Work-mode bit-field treated as one state | Adopted | Partial: Off-grid dependency path proven |
| Setting dependencies | Adopted | Per setting validation required |
| Scenario-oriented configuration | Added | Preview/guidance only |
| Configuration relationship guard | Added | Active for proven rules |
| Read-back after writes | Existing | Proven for Off-grid minimum SOC path |
| Restore original mode after temporary change | Existing | Proven for Off-grid minimum SOC path |
| Grouped register profile | Added as device metadata | Poller switch deferred |
| Fast/normal/slow cadence model | Added as device metadata | Deferred |
| Remote dispatch / force-battery control | Architecture reserved | Not enabled |
| Peak shaving / import limit | Scenario reserved | Registers not yet validated |
| Manual grid charge to target SOC | Scenario reserved | Transaction not yet validated |
| Detailed diagnostics | Expanded | Active |
| Brand-neutral EMS capability mapping | Added | Read-only metadata |
