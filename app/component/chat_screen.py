from __future__ import print_function

from math import ceil
from random import sample
from string import ascii_lowercase

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty, Logger, NumericProperty
from kivy.uix.screenmanager import Screen
from kivymd.list import TwoLineListItem, BaseListItem


class MultiLineListItem(BaseListItem):
    _txt_top_pad = NumericProperty(dp(16))
    _txt_bot_pad = NumericProperty(dp(15))  # dp(20) - dp(5)
    _num_lines = 1

    def __init__(self, **kwargs):
        super(MultiLineListItem, self).__init__(**kwargs)
        self._num_lines = ceil(len(self.text) / 100.0)
        self.height = dp(48 + 20 * (self._num_lines - 1))
        self.__post_init__(kwargs)

    def __post_init__(self, *args):
        self.ids._lbl_primary.markup = True


class ChatScreen(Screen):
    app = ObjectProperty(None)

    def __init__(self, **kw):
        super(ChatScreen, self).__init__(**kw)
        Builder.load_file('app/template/chat_screen.kv')
        self.app = App.get_running_app()
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *args):
        self.ids.irc_message.disabled = True
        self.ids.irc_message_send_btn.disabled = True
        self.ids.irc_message._hint_lbl.text = 'Connecting...'

    def update_irc_message_text(self, dt):
        self.ids.irc_message.text = ''
        self.ids.irc_message.on_focus()

    def send_message(self):
        Clock.schedule_once(self.update_irc_message_text, -1)
        self.app.connection.msg("#"+self.app.config.get('irc', 'channel'), self.ids.irc_message.text)
        self.update_list(self.app.config.get('irc', 'nickname'), self.ids.irc_message.text)
        Logger.info("IRC: <%s> %s" % (self.app.config.get('irc', 'nickname'), self.ids.irc_message.text))

    def on_message(self, user, channel, msg):
        user = user.split('!', 1)[0]
        Logger.info("IRC: <%s> %s" % (user, msg))
        self.update_list(user, msg)

    def update_list(self, username, message):
        self.msg_list.add_widget(
            MultiLineListItem(
                text="[b][color=ff3333]@" + username + "[/color][/b] " + message,
                secondary_text=message,
                font_style='Subhead',
                _num_lines=3
            )
        )

    def __post_joined__(self, connection):
        self.ids.irc_message.disabled = False
        self.ids.irc_message_send_btn.disabled = False
        self.ids.irc_message._hint_lbl.text = '@manthansharma'
        self.app.connection.on_message(self.on_message)
