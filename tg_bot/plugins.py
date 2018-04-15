"""Base classes for plugin system."""
import re
import logging
from collections import deque
from telegram.ext import RegexHandler
from telegram.ext.dispatcher import run_async

log = logging.getLogger(__name__)


class GenericPlugin:
    """The most generic Nadeko Plugin.
    Does nothing, don't activate it accidentally!
    You may want to override __init__() and reply().
    """
    def __init__(self, updater, group=0):
        """Initializes generic plugin. You may want to override this."""
        self.handlers = []
        self.updater = updater
        self.group = group

    def activate(self):
        """Activates a plugin."""
        def activate_handler(handler):
            log.debug("Activating handler %s", handler)
            self.updater.dispatcher.add_handler(handler[0], handler[1])
        deque(map(activate_handler, self.handlers), maxlen=0)

    # pylint: disable=R0201,W0613
    def reply(self, bot, update):
        """Replies... with nothing by default. Override it."""
        logging.getLogger(__name__).critical("CALLED EMPTY REPLY METHOD!!! THIS IS A BUG, REPORT IT!!!")

    def deactivate(self):
        """Deactivates a plugin."""
        def deactivate_handler(handler):
            self.updater.dispatcher.remove_handler(handler[0])
        map(deactivate_handler, self.handlers)


class GenericRegex(GenericPlugin):
    """Generic regex module.
    Extend it to build your own plugin which would react to human language... as precisely as you can parse it."""
    # pylint: disable=R0903,W0231
    def __init__(self, updater, regex, reply, group=0, pass_user_data=False):
        """Adds handler for regex to dispatcher.
        Regex strings are compiled with re.IGNORECASE by default. Pass compiled pattern if this is undesirable."""
        if isinstance(regex, str):
            regex = re.compile(regex, re.IGNORECASE)
        self.handlers = [
            (RegexHandler(regex, reply, pass_user_data=pass_user_data), group)
        ]
        self.updater = updater


class RegexTextReplier(GenericRegex):
    """Replies with predetermined text or generates text from lambda on-the-fly."""
    def __init__(self, dispatcher, regex, replytext, group=0, pass_user_data=False):
        """Set up reply handler."""
        self.replytext = replytext
        reply_callback = self.reply
        super(RegexTextReplier, self).__init__(dispatcher, regex, reply_callback, group, pass_user_data)

    @run_async
    def reply(self, bot, update):
        """Reply with text."""
        if callable(self.replytext):
            text = self.replytext(update)
        else:
            text = self.replytext
        update.message.reply_text(text)
