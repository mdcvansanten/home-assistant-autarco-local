# Autarco Local — Modbus write-access checklist

This document tracks the prerequisites for enabling controlled writes in Autarco Local.

## Current hardware result

- Reading holding register `43137` works and returns the live **Off-grid minimum SOC** value.
- A guarded Modbus function-06 write `10 -> 20` receives no transport/Modbus exception, but repeated read-back still returns `10`.
- Therefore the current TCP path is not yet proven to apply configuration writes.
- Do **not** broaden writes to other registers until the write path is confirmed.

## Autarco official integration path

Autarco documents third-party EMS steering as supported over two routes:

1. **Modbus TCP** through an Autarco communication adapter.
2. **RS485 / Modbus RTU** directly to the inverter on the dedicated EMS/RS485 port where available.

For TCP/IP EMS operation Autarco currently documents the following prerequisite for the LAN stick:

- communication device: `S2.LAN.STICK.D`;
- communication-stick firmware: `100101B0`;
- EMS polling should not be faster than once per second.

Autarco also documents `S2.WIFI-STICK-D2` as a supported TCP/IP steering path for external EMS systems.

## Information to request from Autarco Support

For the LH-MII / S2.LH-MII integration ask Autarco to confirm:

- exact communication-stick model installed on the inverter;
- installed communication-stick firmware and whether it supports **write/steering**, not only Modbus TCP reads;
- whether Modbus TCP write access requires an enable flag, Digital O&M setting, installer permission, unlock command, password/token or different Unit ID;
- official write-capable Modbus register table/protocol for the LH-MII generation;
- whether holding register `43137` is writable through the communication stick and which function code is required;
- whether persistent configuration writes require a commit/save/apply command after writing the register;
- whether the same write is supported over direct RS485 if the communication stick filters configuration writes;
- recommended inter-frame delay and minimum interval between commands;
- any warranty/support restrictions for third-party EMS writes.

Suggested support wording:

> We are developing a local third-party EMS integration for an Autarco S2.LH-MII hybrid inverter. Holding-register reads over Modbus TCP work correctly. Register 43137 reads the live Off-grid minimum SOC (10%). A guarded function-06 write of 20 returns without a Modbus exception, but immediate repeated read-back remains 10%. Please confirm the supported write/steering procedure for LH-MII through the installed Autarco communication stick, including required firmware, permissions/unlock, Unit ID, function code and whether a save/apply command is required. We would also like the official write-capable Modbus/EMS protocol table for this model.

## Solis-origin protocol fallback

Solis publishes a non-NDA Modbus table for reading. For organisations requiring write-access capabilities, Solis currently directs EMS companies, system integrators, OEMs, SCADA providers and enterprise customers to submit a support ticket; its product team then reviews the request and NDA requirements.

Because this inverter is Autarco-branded and Autarco explicitly supports third-party EMS integration, **Autarco Support is the preferred first route**. The Solis NDA route is a fallback for protocol confirmation if required.

## Safety policy for Autarco Local

Until write access is formally confirmed:

- all normal settings stay read-only;
- the failed `43137` pilot must not be automatically retried;
- no undocumented unlock or neighbouring registers are probed by writes;
- once write access is confirmed, each setting receives an explicit allow-list entry, validation, confirmation where appropriate, immediate read-back and audit logging;
- backend safety invariants remain authoritative, including `Reserve SOC >= Minimum battery SOC`.
