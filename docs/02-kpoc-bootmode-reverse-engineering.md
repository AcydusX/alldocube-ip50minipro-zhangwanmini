# KPOC boot-mode reverse engineering notes

## Purpose

This document preserves the deeper KPOC investigation so future agents do not assume every charger-animation failure is an Android userspace problem.

## Observed chain

MediaTek early boot stages establish boot reason/mode. Main LK eventually passes the selected mode to Linux using `/chosen/atag,boot`.

A reverse-engineered LK path showed:

- an off-mode charging path can produce mode value `8`,
- failed traces still reached `boot_linux_fdt` with `lk boot mode = 0`,
- `set_fdt_atag_boot()` calls the final LK mode getter and writes a 16-byte property:

```text
+0x00 size 0x10
+0x04 tag  0x41000802
+0x08 final LK boot mode
+0x0c boot type
```

Linux vendor modules such as battery/charger framework code parse this same property and read the mode/type words. Runtime logs confirmed the structure with mode `0` in the failed case.

## Consequence

There was no evidence that Linux changed an LK-provided KPOC mode 8 into mode 0. In those failure traces, main LK had already selected normal mode 0.

Therefore:

- adding charger images alone cannot repair an LK boot-mode decision failure,
- TWRP PLATFORM missing charger resources is a separate, real problem,
- and KPOC troubleshooting must distinguish early boot-mode selection from later userspace rendering.

## Historical BL2_EXT splash note

An early low-battery/charger splash (“slot 2” in project notes) was interpreted as a BL2_EXT temporary framebuffer state, not proof that the actual battery was low. If main LK then continues in mode 0, nothing later replaces that early frame with the full KPOC sequence.

## Final-stack relevance

The final production-like stack preserved stock-derived vendor_boot/KPOC content and did not attempt to solve KPOC solely by installing TWRP. The LK modification performed in the final AVB stage changed the trusted AVB modulus, not the KPOC mode logic.
