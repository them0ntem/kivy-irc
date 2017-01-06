import time
from pprint import pprint

from kivy.support import install_twisted_reactor

install_twisted_reactor()

from twisted.internet import reactor, defer
from twisted.internet import protocol
from twisted.words.protocols import irc
from kivy.logger import Logger

from kivy.app import App
from kivy.uix.label import Label


class TwistedServerApp(App):
    connection = None

    def __init__(self, **kwargs):
        super(TwistedServerApp, self).__init__(**kwargs)
        self.label = None

    def build(self):
        # reactor.stop()
        self.label = Label(text="server started\n")
        self.connect_to_server()
        return self.label

    def connect_to_server(self):
        reactor.connectTCP("irc.freenode.net", 6667, LogBotFactory(self, 'test-kivy-irc'))

    def on_connection(self, connection):
        Logger.info("IRC: connected successfully!")
        self.connection = connection

    def test(self):
        def got_names(nicklist):
            pprint(nicklist)

        self.connection.names("#test-kivy-irc").addCallback(got_names)

    def handle_message(self, msg):
        self.label.text = "received:  %s\n" % msg

        if msg == "ping":
            msg = "pong"
        if msg == "plop":
            msg = "kivy rocks"
        self.label.text += "responded: %s\n" % msg
        return msg


class LogBotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """
    autoreconnect = True
    bot = None
    MAX_ATTEMPTS = 5
    RECONNECT_DELAY = 60

    def __init__(self, app, channel):
        self.channel = channel
        self.app = app
        self.connection_attempts = 0

    def buildProtocol(self, addr):
        bot = LogBot()
        bot.factory = self
        self.bot = bot
        self.connection_attempts = 0
        return bot

    def get_bot(self):
        return self.bot

    def clientConnectionLost(self, connector, reason):
        """Triggered on"""
        Logger.error("connection lost (%s)" % reason)
        if self.bot:
            for channel in self.bot.channelwatchers:
                for watcher in self.bot.channelwatchers[channel]:
                    watcher.error("Connection lost")
        if self.autoreconnect:
            connector.connect()
        else:
            reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        Logger.error("connection failed (%s)" % reason)
        if self.bot:
            for channel in self.bot.channelwatchers:
                for watcher in self.bot.channelwatchers[channel]:
                    watcher.error("Connection failed")
        if self.connection_attempts < LogBotFactory.MAX_ATTEMPTS:
            reactor.callLater(LogBotFactory.RECONNECT_DELAY,
                              connector.connect)
            self.connection_attempts += 1
        else:
            Logger.info("IRC: Connection can't be established - Shutting down")
            reactor.stop()


class LogBot(irc.IRCClient, protocol.Protocol):
    """A logging IRC bot."""
    nickname = "twistedbot"

    def __init__(self):
        self._namescallback = {}

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        Logger.info("IRC: connected at %s" %
                    time.asctime(time.localtime(time.time())))
        self.factory.app.on_connection(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        Logger.info("IRC: disconnected at %s" %
                    time.asctime(time.localtime(time.time())))

    # callbacks for events

    def signedOn(self):
        """Called when bot has successfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        def got_names(nicklist):
            pprint(nicklist)

        """This will get called when the bot joins the channel."""
        Logger.info("IRC: I have joined %s" % channel)
        self.factory.app.test()

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        Logger.info("IRC: <%s> %s" % (user, msg))

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "It isn't nice to whisper!  Play nice with the group."
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname + ":"):
            msg = "%s: I am a log bot" % user
            self.msg(channel, msg)
            Logger.info("IRC: <%s> %s" % (self.nickname, msg))

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


if __name__ == '__main__':
    TwistedServerApp().run()
