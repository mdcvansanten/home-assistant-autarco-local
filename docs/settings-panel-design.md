# Autarco Local Settings Center UI v2

The native Home Assistant Options Flow remains available as a fallback and diagnostic surface, but it cannot control typography or field placement precisely enough for the intended mobile UI.

v0.6.2 introduces a dedicated Autarco Local panel with this visual pattern:

```
🟡 Minimum-SOC off-grid                         10 %
Minimum-SOC during off-grid operation. A higher value keeps more emergency reserve.
```

For future writable settings the value position becomes the editor location:

```
🟡 Minimum-SOC off-grid                      [ 20 ] %
Minimum-SOC during off-grid operation. A higher value keeps more emergency reserve.
```

Design rules:

- access-level dot stays the existing size;
- setting name is larger and more readable than the native Options Flow field label;
- current value/editor is aligned to the right on wide screens and wraps below the name on narrow screens;
- description is slightly larger and remains directly below the setting row;
- Standard, Expert and Installer/system groups remain visually distinct;
- Installer/system values stay read-only;
- physical writes remain locked until the write protocol is confirmed.
