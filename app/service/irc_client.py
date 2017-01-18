from __future__ import print_function

import time

from kivy.logger import Logger
from twisted.internet import defer, protocol, reactor
from twisted.words.protocols import irc


class IRCClientFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """
    autoreconnect = True
    bot = None
    MAX_ATTEMPTS = 5
    RECONNECT_DELAY = 60

    def __init__(self, app, channel, nickname):
        self.channel = channel
        self.nickname = nickname
        self.app = app
        self.connection_attempts = 0

    def buildProtocol(self, addr):
        bot = IRCClient(self.nickname, self.app.config.get('irc', 'password'))
        bot.factory = self
        self.bot = bot
        self.connection_attempts = 0
        return bot

    def get_bot(self):
        return self.bot

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print("connection failed:", reason)
        reactor.stop()


class IRCClient(irc.IRCClient):
    """A logging IRC bot."""
    channels = []
    _join_callback = {}
    _who_callback = {}
    _priv_msg_callback = {}
    _user_action_callback = {}
    _irc_unknown_callback = []
    _noticed_callback = []

    def __init__(self, nickname, password):
        self.nickname = nickname
        self.password = password

    def connectionMade(self):
        self.channels = self.factory.app.channel

        irc.IRCClient.connectionMade(self)
        Logger.info("IRC: connected at %s" %
                    time.asctime(time.localtime(time.time())))
        self.factory.app.on_irc_connection(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        Logger.info("IRC: disconnected at %s" %
                    time.asctime(time.localtime(time.time())))

    def signedOn(self):
        """Called when bot has successfully signed on to server."""
        for channel in self.channels:
            self.join(channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        Logger.info("IRC: I have joined %s" % channel)
        channel = channel.strip('#')
        self.factory.app.scr_mngr.get_screen('irc_chat').add_channel_tab(channel)

    def on_privmsg(self, channel, callback):
        channel = channel.lower()

        if channel not in self._priv_msg_callback:
            self._priv_msg_callback[channel] = []
        self._priv_msg_callback[channel].append(callback)

    def on_irc_unknown(self, callback):
        self._irc_unknown_callback.append(callback)

    def on_noticed(self, callback):
        self._noticed_callback.append(callback)

    def on_usr_action(self, channel, callback):
        channel = channel.lower()

        if channel not in self._user_action_callback:
            self._user_action_callback[channel] = []
        self._user_action_callback[channel].append(callback)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        channel = channel.strip('#')
        if channel in self._priv_msg_callback:
            callbacks = self._priv_msg_callback[channel]
            print(callbacks)
            for cb in callbacks:
                cb(user, channel, msg)
        if user.split('!')[0] in self._priv_msg_callback:
            callbacks = self._priv_msg_callback[user.split('!')[0]]

            for cb in callbacks:
                cb(user, channel, msg)
        else:
            if channel == self.nickname:
                self.factory.app.scr_mngr.get_screen('irc_chat').add_private_tab(user.split('!')[0], msg)
                return

                # Check to see if they're sending me a private message
                #
                # # Otherwise check to see if it is a message directed at me
                # if msg.startswith(self.nickname + ":"):
                #     msg = "%s: I am a log bot" % user
                #     self.msg(channel, msg)
                #     Logger.info("IRC: <%s> %s" % (self.nickname, msg))

    def userJoined(self, user, channel):
        """Called when I see another user joining a channel."""
        channel = channel.strip('#')
        if channel not in self._user_action_callback:
            return

        callbacks = self._user_action_callback[channel]

        for cb in callbacks:
            cb(user, channel, None, 0)

    def userLeft(self, user, channel):
        """Called when I see another user leaving a channel."""
        channel = channel.strip('#')
        if channel not in self._user_action_callback:
            return

        callbacks = self._user_action_callback[channel]

        for cb in callbacks:
            cb(user, channel, None, 1)

    def userQuit(self, user, quit_message):
        """Called when I see another user disconnect from the network."""
        if not self._user_action_callback:
            return

        for channel, callbacks in self._user_action_callback.iteritems():
            print(callbacks)
            for cb in callbacks:
                cb(user, None, quit_message, 2)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        Logger.info("IRC: * %s %s" % (user, msg))

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        Logger.info("IRC: %s is now known as %s" % (old_nick, new_nick))

    def who(self, channel):
        """Called to send WHO command for a channel."""
        channel = channel.lower()
        d = defer.Deferred()
        if channel not in self._who_callback:
            self._who_callback[channel] = ([], [])

        self._who_callback[channel][0].append(d)
        self.sendLine("WHO %s" % "#" + channel)
        return d

    def irc_RPL_WHOREPLY(self, prefix, params):
        """This will get called when the bot sees someone do an action."""
        channel = params[1].lower().strip('#')
        if channel not in self._who_callback:
            return

        n = self._who_callback[channel][1]
        n.append(params)

    def irc_RPL_ENDOFWHO(self, prefix, params):
        """Print all unhandled replies, for debugging."""
        channel = params[1].lower().strip('#')
        if channel not in self._who_callback:
            return

        callbacks, nick_data = self._who_callback[channel]

        nick_data = {x[5]: x for x in nick_data}
        for cb in callbacks:
            cb.callback(nick_data)

        del self._who_callback[channel]

    def noticed(self, user, channel, message):
        """Called when I have a notice from a user to me or a channel."""
        callbacks = self._noticed_callback

        for cb in callbacks:
            cb(user, channel, message)

    def irc_unknown(self, prefix, command, params):
        """Print all unhandled replies, for debugging."""
        callbacks = self._irc_unknown_callback

        for cb in callbacks:
            cb(prefix, command, params)
