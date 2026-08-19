# Support request — Autarco EMS write access

Use this checklist when contacting Autarco Support about local third-party EMS write access for the LH-MII.

Required confirmations:

- communication stick model;
- communication stick firmware;
- whether Modbus TCP steering/writes are enabled on that firmware;
- required Unit ID/slave ID;
- write function code for persistent holding-register settings;
- whether an enable/unlock/authentication step is required;
- whether a separate save/apply/commit command is required after a setting write;
- whether register 43137 (Off-grid minimum SOC) is writable through the stick;
- direct-RS485 fallback procedure if the stick filters writes;
- official LH-MII write-capable EMS/Modbus table.

Observed hardware result:

- register 43137 read = 10;
- function-06 write request = 20;
- no Modbus exception;
- repeated read-back = 10.

This suggests the local TCP transport is healthy but the configuration change is not being applied/persisted by the current path.
