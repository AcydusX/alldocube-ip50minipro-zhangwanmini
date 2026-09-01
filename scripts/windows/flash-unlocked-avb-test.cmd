@echo off
REM Reference hardware gate. Keep bootloader UNLOCKED. Do not run blindly.
set DEPLOY=E:\alldocube_logo_work\LOCKED-AVB-TEST-01

fastboot getvar unlocked
fastboot getvar current-slot

REM In fastbootd:
fastboot flash system_a "%DEPLOY%\system_a.img"
fastboot flash vendor_a "%DEPLOY%\vendor_a.img"
fastboot getvar partition-size:system_a
fastboot getvar partition-size:vendor_a

fastboot reboot bootloader
fastboot flash vbmeta_system_a "%DEPLOY%\vbmeta_system_a.img"
fastboot flash vbmeta_vendor_a "%DEPLOY%\vbmeta_vendor_a.img"
fastboot flash vbmeta_a "%DEPLOY%\vbmeta_a.img"
fastboot set_active a
fastboot reboot
