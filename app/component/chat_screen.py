from __future__ import print_function

from math import ceil

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, Logger, NumericProperty
from kivy.uix.screenmanager import Screen
from kivymd.list import BaseListItem


class MultiLineListItem(BaseListItem):
    _txt_top_pad = NumericProperty(dp(5))
    _txt_bot_pad = NumericProperty(dp(5))
    _num_lines = 1

    def __init__(self, **kwargs):
        super(MultiLineListItem, self).__init__(**kwargs)
        self._num_lines = ceil(len(self.text) / 100.0)
        self.height = dp(27 + 20 * (self._num_lines - 1))
        self.text_size = self.width, None
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
        self.app.connection.msg("#" + self.app.config.get('irc', 'channel'), self.ids.irc_message.text)
        self.msg_list.add_widget(
            MultiLineListItem(
                text="[b][color=1A237E]@" + self.app.config.get('irc', 'nickname') + "[/color][/b] "
                     + self.ids.irc_message.text,
                font_style='Subhead',
            )
        )
        Logger.info("IRC: <%s> %s" % (self.app.config.get('irc', 'nickname'), self.ids.irc_message.text))

    def on_privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        self.msg_list.add_widget(
            MultiLineListItem(
                text="[b][color=F44336]@" + user + "[/color][/b] " + msg,
                font_style='Subhead',
            )
        )
        Logger.info("IRC: <%s> %s" % (user, msg))

    def on_usr_joined(self, user, channel):
        self.msg_list.add_widget(
            MultiLineListItem(
                text="[b][color=9C27B0]" + user + "[/color][/b] -> joined",
                font_style='Subhead',
            )
        )
        self.app.connection.names("#" + self.app.config.get('irc', 'channel')).addCallback(self.names_callback)
        Logger.info("IRC: %s -> %s" % (user, 'joined'))

    def names_callback(self, nicklist):
        nicklist.sort()
        self.nick_list.clear_widgets()
        for nick in nicklist:
            self.nick_list.add_widget(
                MultiLineListItem(
                    text=nick
                )
            )
        Logger.info("IRC: <%s> -> nicks -> %s" % (self.app.config.get('irc', 'channel'), nicklist))

    def __post_joined__(self, connection):
        self.app.connection.names(self.app.config.get('irc', 'channel')).addCallback(self.names_callback)
        self.ids.irc_message.disabled = False
        self.ids.irc_message_send_btn.disabled = False
        self.ids.irc_message._hint_lbl.text = '@' + self.app.config.get('irc', 'nickname')
        self.app.connection.on_privmsg(self.app.config.get('irc', 'channel'), self.on_privmsg)
        self.app.connection.on_usr_joined(self.app.config.get('irc', 'channel'), self.on_usr_joined)
