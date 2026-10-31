import re
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivy.properties import StringProperty, ListProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

KV = r"""
<NetworkButton>:
    size_hint_y: None
    height: "52dp"
    background_normal: ""
    background_color: (0.12, 0.19, 0.29, 1)
    color: (1, 1, 1, 1)
    halign: "left"
    padding_x: "14dp"

BoxLayout:
    orientation: "vertical"
    padding: "18dp"
    spacing: "12dp"
    canvas.before:
        Color:
            rgba: (0.035, 0.055, 0.09, 1)
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "WiFi Translator"
        font_size: "27sp"
        bold: True
        color: (0.20, 0.72, 0.96, 1)
        size_hint_y: None
        height: "54dp"

    Label:
        text: "Discover networks and select yours"
        font_size: "16sp"
        color: (0.85, 0.89, 0.94, 1)
        size_hint_y: None
        height: "32dp"

    Button:
        text: "Scan Wi-Fi Networks"
        size_hint_y: None
        height: "48dp"
        background_normal: ""
        background_color: (0.02, 0.48, 0.75, 1)
        on_release: app.scan_networks()

    Label:
        text: app.status
        size_hint_y: None
        height: "42dp"
        color: (0.95, 0.78, 0.35, 1)
        text_size: self.width, None

    ScrollView:
        do_scroll_x: False
        GridLayout:
            id: network_list
            cols: 1
            spacing: "7dp"
            size_hint_y: None
            height: self.minimum_height

    Label:
        text: "Selected Network"
        size_hint_y: None
        height: "26dp"
        color: (0.8, 0.85, 0.92, 1)

    Label:
        id: selected_ssid
        text: app.selected_ssid if app.selected_ssid else "No network selected"
        size_hint_y: None
        height: "35dp"
        color: (1, 1, 1, 1)
        bold: True

    Button:
        text: "Calculate Expected Password"
        size_hint_y: None
        height: "48dp"
        background_normal: ""
        background_color: (0.02, 0.55, 0.34, 1)
        on_release: app.translate_selected()

    Label:
        text: "Result according to translation rules"
        size_hint_y: None
        height: "25dp"
        color: (0.8, 0.85, 0.92, 1)

    Label:
        id: result
        text: app.result
        size_hint_y: None
        height: "42dp"
        font_size: "21sp"
        bold: True
        color: (0.30, 0.90, 0.55, 1)

    Button:
        text: "Copy Result"
        size_hint_y: None
        height: "44dp"
        background_normal: ""
        background_color: (0.16, 0.38, 0.65, 1)
        on_release: app.copy_result()

    Button:
        text: "Open Wi-Fi Settings"
        size_hint_y: None
        height: "44dp"
        background_normal: ""
        background_color: (0.28, 0.30, 0.36, 1)
        on_release: app.open_wifi_settings()

    Label:
        text: "Note: The result is a rule-based guess, not an actual password retrieval."
        size_hint_y: None
        height: "38dp"
        font_size: "11sp"
        color: (0.65, 0.70, 0.78, 1)
"""

class NetworkButton(Button):
    pass


class WifiTranslatorApp(App):
    status = StringProperty("Grant Wi-Fi and Location permissions when prompted, then tap Scan.")
    selected_ssid = StringProperty("")
    result = StringProperty("—")
    networks = ListProperty([])

    def build(self):
        self.root = Builder.load_string(KV)
        return self.root

    def on_start(self):
        if platform == "android":
            self.request_android_permissions()

    def request_android_permissions(self):
        try:
            from android.permissions import request_permissions, Permission
            perms = [Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION]
            perms.append("android.permission.NEARBY_WIFI_DEVICES")
            request_permissions(perms, self.permission_callback)
        except Exception as exc:
            self.status = f"Failed to request permissions: {exc}"

    def permission_callback(self, permissions, grants):
        if grants and all(grants):
            self.status = "Permissions granted. Tap 'Scan Wi-Fi Networks'."
        else:
            self.status = "Location / Nearby devices permission is required to scan networks."

    def scan_networks(self):
        if platform != "android":
            self.status = "Scanning is only available inside the installed Android app."
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            activity = PythonActivity.mActivity
            wifi = activity.getApplicationContext().getSystemService(Context.WIFI_SERVICE)

            started = wifi.startScan()
            self.status = "Scanning networks..." if started else "Cannot start new scan; attempting to read cached results."
            Clock.schedule_once(lambda dt: self.read_scan_results(wifi), 3.0)
        except Exception as exc:
            self.status = f"Error during scan: {exc}"

    def read_scan_results(self, wifi):
        try:
            results = wifi.getScanResults()
            found = []
            for item in results:
                ssid = str(item.SSID)
                if ssid and ssid not in found:
                    found.append(ssid)
            self.networks = found
            container = self.root.ids.network_list
            container.clear_widgets()
            if not found:
                self.status = ("No networks found. Ensure Wi-Fi & Location services are ON "
                               "and permissions are granted, then try again.")
                return
            for ssid in found:
                btn = NetworkButton(text=ssid)
                btn.bind(on_release=lambda _btn, name=ssid: self.select_network(name))
                container.add_widget(btn)
            self.status = f"Found {len(found)} network(s) (results may be cached)."
        except Exception as exc:
            self.status = f"Failed to read scan results: {exc}"

    def select_network(self, ssid):
        self.selected_ssid = ssid
        self.result = "—"
        self.status = f"Selected: {ssid}"

    @staticmethod
    def convert_name(ssid):
        value = ssid.lower()
        value = value.replace("fh_", "wlan")
        for old, new in (("a", "5"), ("d", "2"), ("b", "4"),
                         ("f", "0"), ("8", "7"), ("9", "6")):
            value = value.replace(old, new)
        return value

    def translate_selected(self):
        if not self.selected_ssid:
            self.status = "Please select a network from the list first."
            return
        self.result = self.convert_name(self.selected_ssid)
        self.status = "Translation rules applied."

    def copy_result(self):
        if not self.result or self.result == "—":
            self.status = "Calculate the result first."
            return
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.result)
            self.status = "Result copied to clipboard."
        except Exception as exc:
            self.status = f"Failed to copy: {exc}"

    def open_wifi_settings(self):
        if platform != "android":
            self.status = "This option only works on Android."
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Settings = autoclass("android.provider.Settings")
            Intent = autoclass("android.content.Intent")
            activity = PythonActivity.mActivity
            intent = Intent(Settings.ACTION_WIFI_SETTINGS)
            activity.startActivity(intent)
        except Exception as exc:
            self.status = f"Failed to open Wi-Fi settings: {exc}"


if __name__ == "__main__":
    WifiTranslatorApp().run()
