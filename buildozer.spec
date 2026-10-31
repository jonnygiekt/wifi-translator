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

# Android settings
android.minapi = 26
android.api = 33
android.ndk = 25b
android.archs = arm64-v8a
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
