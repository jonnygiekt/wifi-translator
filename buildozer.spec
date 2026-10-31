[app]
title = WiFi Translator
package.name = wifitranslator
package.domain = org.example
source.dir = .
source.include_exts = py,kv,png,jpg,atlas
version = 1.0
requirements = python3,kivy,pyjnius
orientation = portrait
fullscreen = 0

# Android 12+ (API 31+) support. Buildozer uses these to build the APK.
android.minapi = 31
android.api = 35
android.ndk = 27b
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,NEARBY_WIFI_DEVICES
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
