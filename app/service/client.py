import pydle


class MyClient(pydle.Client):
    """ This is a simple bot that will greet people as they join the channel. """
    on_channel_message_callback = None

    def on_connect(self):
        super(MyClient, self).on_connect()
        self.join('#test-kivy-irc')

    def on_join(self, channel, user):
        super(MyClient, self).on_join(channel, user)
        self.message(channel, 'Hey {}! Welcome to Test Kivy IRC'.format(user))

    def on_channel_message(self, target, by, message):
        super(MyClient, self).on_channel_message(target, by, message)
        self.on_channel_message_callback(target, by, message)
        print(target)

    def on_channel_message__(self, callback):
        self.on_channel_message_callback = callback
