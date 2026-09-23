# src/maxson_build_utils/kivy/app.py
from __future__ import annotations

from kivy.app import App
from kivy.uix.label import Label


class MaxsonBuildUtilsApp(App):
    def build(self):
        return Label(text="Hello from maxson-build-utils!")


def launch_kivy_app() -> None:
    app = MaxsonBuildUtilsApp()
    app.run()
