from kivy.clock import Clock
from kivy.uix.screenmanager import Screen


class SettingScreen(Screen):
    def __init__(self, **kw):
        super(SettingScreen, self).__init__(**kw)
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *args):
        pass

    def __post_connection__(self, connection):
        pass

    def __post_joined__(self, connection):
        pass
