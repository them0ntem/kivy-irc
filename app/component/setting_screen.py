
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen


class SettingScreen(Screen):
    def __init__(self, **kw):
        super(SettingScreen, self).__init__(**kw)
        Builder.load_file('app/template/setting_screen.kv')
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *args):
        print(self.ids)
