from math import ceil

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, NumericProperty, DictProperty
from kivy.uix.screenmanager import Screen
from kivymd.list import BaseListItem

from app.component.channel_chat_tab import ChannelChatTab


class MultiLineListItem(BaseListItem):
    _txt_top_pad = NumericProperty(dp(10))
    _txt_bot_pad = NumericProperty(dp(10))
    _num_lines = 1

    def __init__(self, **kwargs):
        super(MultiLineListItem, self).__init__(**kwargs)
        self._num_lines = ceil(len(self.text) / 100.0)
        self.height = dp(37 + 20 * (self._num_lines - 1))
        self.text_size = self.width, None
        self.__post_init__(kwargs)

    def __post_init__(self, *args):
        self.ids._lbl_primary.markup = True


class ChatScreen(Screen):
    app = ObjectProperty(None)
    nick_data = DictProperty()

    def __init__(self, **kw):
        super(ChatScreen, self).__init__(**kw)
        self.app = App.get_running_app()
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *args):
        for channel in self.app.channel:
            self.tab_panel.add_widget(
                ChannelChatTab(
                    name=channel,
                    text=channel
                )
            )

    def __post_connection__(self, connection):
        for tab in self.tab_panel.ids.tab_manager.screens:
            tab.__post_connection__(connection)

    def __post_joined__(self, connection):
        for tab in self.tab_panel.ids.tab_manager.screens:
            tab.__post_joined__(connection)
