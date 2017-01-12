import time

from kivy.clock import Clock
from kivy.logger import Logger
from twisted.internet import defer
from twisted.internet import protocol
from twisted.internet import reactor
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
        bot = IRCClient()
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


class IRCClient(irc.IRCClient, protocol.Protocol):
    """A logging IRC bot."""
    nickname = None
    channel = None

    def __init__(self):
        self._joincallback = {}
        self._whocallback = {}
        self._privmsgcallback = {}
        self._userjoinedcallback = {}
        self._userleftcallback = {}
        self._userquitcallback = []
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *args):
        self.channel = self.factory.channel

    def connectionMade(self):
        self.nickname = self.factory.nickname
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

    def on_joined(self, channel, callback):
        channel = channel.lower()

        if channel not in self._joincallback:
            self._joincallback[channel] = []
        self._joincallback[channel].append(callback)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        Logger.info("IRC: I have joined %s" % channel)
        channel = channel.strip('#')
        if channel not in self._joincallback:
            return

        callbacks = self._joincallback[channel]

        for cb in callbacks:
            cb(channel)

    def on_privmsg(self, channel, callback):
        channel = channel.lower()

        if channel not in self._privmsgcallback:
            self._privmsgcallback[channel] = []
        self._privmsgcallback[channel].append(callback)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        channel = channel.strip('#')
        if channel not in self._privmsgcallback and channel != self.nickname:
            return

        callbacks = self._privmsgcallback[channel]

        for cb in callbacks:
            cb(user, channel, msg)

            # # Check to see if they're sending me a private message
            # if channel == self.nickname:
            #     msg = "It isn't nice to whisper!  Play nice with the group."
            #     self.msg(user, msg)
            #     return
            #
            # # Otherwise check to see if it is a message directed at me
            # if msg.startswith(self.nickname + ":"):
            #     msg = "%s: I am a log bot" % user
            #     self.msg(channel, msg)
            #     Logger.info("IRC: <%s> %s" % (self.nickname, msg))

    def on_usr_joined(self, channel, callback):
        channel = channel.lower()

        if channel not in self._userjoinedcallback:
            self._userjoinedcallback[channel] = []
        self._userjoinedcallback[channel].append(callback)

    def userJoined(self, user, channel):
        channel = channel.strip('#')
        if channel not in self._userjoinedcallback:
            return

        callbacks = self._userjoinedcallback[channel]

        for cb in callbacks:
            cb(user, channel)

    def on_usr_left(self, channel, callback):
        channel = channel.lower()

        if channel not in self._userleftcallback:
            self._userleftcallback[channel] = []
        self._userleftcallback[channel].append(callback)

    def userLeft(self, user, channel):
        channel = channel.strip('#')
        if channel not in self._userleftcallback:
            return

        callbacks = self._userleftcallback[channel]

        for cb in callbacks:
            cb(user, channel)

    def on_usr_quit(self, callback):
        self._userquitcallback.append(callback)

    def userQuit(self, user, quit_message):
        if not self._userquitcallback:
            return

        callbacks = self._userquitcallback

        for cb in callbacks:
            cb(user, quit_message)

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
        channel = channel.lower()
        d = defer.Deferred()
        if channel not in self._whocallback:
            self._whocallback[channel] = ([], [])

        self._whocallback[channel][0].append(d)
        self.sendLine("WHO %s" % "#" + channel)
        return d

    def irc_RPL_WHOREPLY(self, prefix, params):
        channel = params[1].lower().strip('#')
        if channel not in self._whocallback:
            return

        n = self._whocallback[channel][1]
        n.append(params)

    def irc_RPL_ENDOFWHO(self, prefix, params):
        channel = params[1].lower().strip('#')
        if channel not in self._whocallback:
            return

        callbacks, nick_data = self._whocallback[channel]

        nick_data = {x[5]: x for x in nick_data}
        for cb in callbacks:
            cb.callback(nick_data)

        del self._whocallback[channel]

    def irc_unknown(self, prefix, command, params):
        """Print all unhandled replies, for debugging."""
        print('UNKNOWN:', prefix, command, params)
