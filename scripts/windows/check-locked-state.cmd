@echo off
adb shell getprop sys.boot_completed
adb shell getprop ro.build.version.release
adb shell getprop ro.boot.slot_suffix
adb shell getprop ro.boot.verifiedbootstate
adb shell getprop ro.boot.vbmeta.device_state
adb shell getprop ro.boot.flash.locked
adb shell getprop ro.boot.veritymode
adb shell getprop ro.boot.vbmeta.hash_alg
adb shell getprop ro.boot.vbmeta.size
adb shell getprop ro.boot.vbmeta.digest
