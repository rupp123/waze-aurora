[app]
title = Waze Auroras Pro
package.name = wazeauroras
package.domain = org.wazeauroras

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0.0
requirements = python3,kivy,requests

orientation = portrait
fullscreen = 0

permissions = internet, access_network_state, access_fine_location

log_level = 2

[buildozer]
platform = android
android.accept_sdk_license = True
android.sdk = 34
