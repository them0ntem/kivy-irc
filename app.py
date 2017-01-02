# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.navigationdrawer import NavigationDrawer
from kivymd.theming import ThemeManager

from app import *


class KitchenSink(App):
    theme_cls = ThemeManager()
    nav_drawer = ObjectProperty()
    previous_date = ObjectProperty()

    def build(self):
        main_widget = Builder.load_file('app.kv')
        self.nav_drawer = NavDrawer()
        print(main_widget.ids.scr_mngr.screens)
        print(main_widget.ids)
        return main_widget


if __name__ == '__main__':
    KitchenSink().run()
