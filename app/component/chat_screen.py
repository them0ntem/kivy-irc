from random import sample
from string import ascii_lowercase

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen


class ChatScreen(Screen):
    def __init__(self, **kw):
        super(ChatScreen, self).__init__(**kw)
        Builder.load_file('app/template/chat_screen.kv')
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *args):
        self.rv.data = [{'value': ''.join(sample(ascii_lowercase, 6))}
                        for x in range(50)]
