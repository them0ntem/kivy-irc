from __future__ import print_function

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
        self._namescallback = {}
        self._privmsgcallback = []
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *args):
        self.channel = self.factory.channel
        print(self.nickname)

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
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        Logger.info("IRC: I have joined %s" % channel)
        self.factory.app.on_joined(self)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        # user = user.split('!', 1)[0]
        # Logger.info("IRC: <%s> %s" % (user, msg))

        for cb in self._privmsgcallback:
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

    def on_message(self, callback):
        self._privmsgcallback.append(callback)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        Logger.info("IRC: * %s %s" % (user, msg))

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        Logger.info("IRC: %s is now known as %s" % (old_nick, new_nick))

    def names(self, channel):
        channel = channel.lower()
        d = defer.Deferred()
        if channel not in self._namescallback:
            self._namescallback[channel] = ([], [])

        self._namescallback[channel][0].append(d)
        self.sendLine("NAMES %s" % channel)
        return d

    def irc_RPL_NAMREPLY(self, prefix, params):
        channel = params[2].lower()
        nicklist = params[3].split(' ')

        if channel not in self._namescallback:
            return

        n = self._namescallback[channel][1]
        n += nicklist

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        channel = params[1].lower()
        if channel not in self._namescallback:
            return

        callbacks, namelist = self._namescallback[channel]

        for cb in callbacks:
            cb.callback(namelist)

        del self._namescallback[channel]
