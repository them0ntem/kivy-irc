from math import ceil

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ObjectProperty, Logger, NumericProperty
from kivymd.bottomsheet import MDListBottomSheet
from kivymd.dialog import MDDialog
from kivymd.label import MDLabel
from kivymd.list import BaseListItem
from kivymd.tabs import MDTab


class MultiLineListItem(BaseListItem):
    _txt_top_pad = NumericProperty(dp(10))
    _txt_bot_pad = NumericProperty(dp(10))
    _num_lines = 1

    def __init__(self, **kwargs):
        super(MultiLineListItem, self).__init__(**kwargs)
        self._num_lines = ceil(len(self.text) / 120.0)
        self.height = dp(37 + 20 * (self._num_lines - 1))
        self.text_size = self.width, None
        self.__post_init__(kwargs)

    def __post_init__(self, *args):
        self.ids._lbl_primary.markup = True


class StatusTab(MDTab):
    app = ObjectProperty(None)
    irc_action = ObjectProperty(None)
    irc_action_send_btn = ObjectProperty(None)

    def __init__(self, **kw):
        super(StatusTab, self).__init__(**kw)
        self.app = App.get_running_app()
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, args):
        pass

    def update_irc_action_text(self, dt):
        self.irc_action.text = ''
        self.irc_action.on_focus()

    def send_action(self):
        Clock.schedule_once(self.update_irc_action_text)
        self.app.connection.sendLine(self.irc_action.text.strip('/'))
        self.msg_list.add_widget(
            MultiLineListItem(
                text="[b][color=1A237E]" + self.app.config.get('irc', 'nickname') + "[/color][/b] "
                     + self.irc_action.text,
                font_style='Subhead',
            )
        )
        self.msg_list.parent.scroll_to(self.msg_list.children[0])
        Logger.info("IRC: <%s> %s" % (self.app.config.get('irc', 'nickname'), self.irc_action.text))

    def on_irc_unknown(self, prefix, command, params):
        Logger.info("IRC UNKNOWN: <%s> %s %s" % (prefix, command, params))

    def on_noticed(self, user, channel, action):
        user = user.split('!')[0]
        if user == 'ChanServ':
            content = MDLabel(font_style='Body1',
                              theme_text_color='Secondary',
                              text=action,
                              size_hint_y=None,
                              valign='top')
            content.bind(texture_size=content.setter('size'))
            self.dialog = MDDialog(title="Notice: {}".format(user),
                                   content=content,
                                   size_hint=(.8, None),
                                   height=dp(200),
                                   auto_dismiss=False)

            self.dialog.add_action_button("Dismiss",
                                          action=lambda *x: self.dialog.dismiss())
            self.dialog.open()
        else:
            self.msg_list.add_widget(
                MultiLineListItem(
                    text="[b][color=F44336]" + user + "[/color][/b] " + action,
                    font_style='Subhead',
                )
            )
            self.msg_list.parent.scroll_to(self.msg_list.children[0])
        Logger.info("IRC NOTICED: <%s> %s %s" % (user, channel, action))

    def nick_details(self, nick_list_item):
        self.app.connection.signedOn()
        nick_item_data = self.nick_data[nick_list_item.text]
        bs = MDListBottomSheet()
        bs.add_item("Whois ({})".format(nick_list_item.text), lambda x: x)
        bs.add_item("{} ({}@{})".format(nick_item_data[7].split(' ')[1],
                                        nick_item_data[3],
                                        nick_item_data[2]), lambda x: x)
        bs.add_item("{} is connected via {}".format(nick_list_item.text, nick_item_data[4]), lambda x: x)
        bs.open()

    def __post_connection__(self, connection):
        connection.on_irc_unknown(self.on_irc_unknown)
        connection.on_noticed(self.on_noticed)

    def __post_joined__(self, connection):
        pass
