from math import ceil

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ObjectProperty, Logger, NumericProperty, DictProperty
from kivymd.bottomsheet import MDListBottomSheet
from kivymd.list import BaseListItem
from kivymd.tabs import MDTab


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


class ChannelChatTab(MDTab):
    app = ObjectProperty(None)
    irc_message = ObjectProperty(None)
    irc_message_send_btn = ObjectProperty(None)
    nick_data = DictProperty()

    def __init__(self, **kw):
        super(ChannelChatTab, self).__init__(**kw)
        self.app = App.get_running_app()
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *args):
        self.irc_message._hint_lbl.text = '@' + self.app.config.get('irc', 'nickname')
        self.app.connection.on_privmsg(self.text, self.on_privmsg)
        self.app.connection.on_usr_action(self.text, self.on_usr_action)

    def update_irc_message_text(self, dt):
        self.irc_message.text = ''
        self.irc_message.on_focus()

    def send_message(self):
        Clock.schedule_once(self.update_irc_message_text)
        self.app.connection.msg("#" + self.text, self.irc_message.text)
        self.msg_list.add_widget(
            MultiLineListItem(
                text="[b][color=1A237E]@" + self.app.config.get('irc', 'nickname') + "[/color][/b] "
                     + self.irc_message.text,
                font_style='Subhead',
            )
        )
        Logger.info("IRC: <%s> %s" % (self.app.config.get('irc', 'nickname'), self.irc_message.text))

    def on_privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        self.msg_list.add_widget(
            MultiLineListItem(
                text="[b][color=F44336]@" + user + "[/color][/b] " + msg,
                font_style='Subhead',
            )
        )
        Logger.info("IRC: <%s> %s" % (user, msg))

    def on_usr_action(self, user, channel, quit_message, action):
        if action == 0:
            self.msg_list.add_widget(
                MultiLineListItem(
                    text="[color=9C27B0]" + user + "[/color] has joined #" + self.text,
                    font_style='Subhead',
                )
            )
            Logger.info("IRC: %s -> %s" % (user, 'joined'))
        elif action == 1:
            self.msg_list.add_widget(
                MultiLineListItem(
                    text="[color=9C27B0]" + user + "[/color] has left #" + self.text,
                    font_style='Subhead',
                )
            )
            Logger.info("IRC: %s <- %s" % (user, 'left'))
        elif action == 2:
            self.msg_list.add_widget(
                MultiLineListItem(
                    text="[color=9A2FB0]" + user + "[/color] has quit &bl;" + quit_message + "&bt;",
                    font_style='Subhead',
                )
            )
            Logger.info("IRC: %s <- %s" % (user, 'quit'))
        self.app.connection.who(self.text).addCallback(self.who_callback)

    def nick_details(self, nick_list_item):
        self.app.connection.signedOn()
        nick_item_data = self.nick_data[nick_list_item.text]
        bs = MDListBottomSheet()
        bs.add_item("WHOIS ({})".format(nick_list_item.text), lambda x: x)
        bs.add_item("{} ({}@{})".format(nick_item_data[7].split(' ')[1],
                                        nick_item_data[3],
                                        nick_item_data[2]), lambda x: x)
        bs.add_item("{} is connected via {}".format(nick_list_item.text, nick_item_data[4]), lambda x: x)
        bs.open()

    def who_callback(self, nick_data):
        self.nick_data = nick_data
        nick_list = nick_data.keys()
        nick_list.sort()
        self.nick_list.clear_widgets()
        for nick in nick_list:
            list_item = MultiLineListItem(
                text=nick
            )
            list_item.bind(on_press=self.nick_details)
            self.nick_list.add_widget(list_item)

        Logger.info("IRC: <%s> -> nicks -> %s" % (self.text, nick_list))

    def __post_connection__(self, connection):
        pass

    def __post_joined__(self, connection):
        connection.who(self.text).addCallback(self.who_callback)
