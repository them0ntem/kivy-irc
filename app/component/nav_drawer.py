from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.navigationdrawer import NavigationDrawer


class NavDrawer(NavigationDrawer):
    def __init__(self, **kw):
        super(NavDrawer, self).__init__(**kw)
        Builder.load_file('app/template/nav_drawer.kv')
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *args):
        pass
