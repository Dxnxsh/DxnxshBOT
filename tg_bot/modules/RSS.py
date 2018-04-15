import re
import logging
import time
import datetime
import pickle
import urllib
import html.parser
from os import path
from telegram.ext import CommandHandler
from telegram.error import BadRequest
import feedparser
import tg_bot.plugins
from tg_bot.snippets import stripln

datadir = "data"
log = logging.getLogger(__name__)
NEWPOST = 'Новый пост в блоге <a href="{url}">{title}</a>!\nПост: {post}\n\n{content}'

# Code for Tumblr special support
valid_tags = re.compile(r'(<(/?)(b|i|pre|code|a href="[^"]+")>)')
invalid_tags = re.compile(r'(?<!\\)[<][^>]*(?<!\\)[>]')
paragraphy = re.compile('</?p>')
unhr = re.compile('<hr>')
unesq_right = re.compile('>')
unesq_left = re.compile('<')
validify_tags = re.compile(r'\\(<|<|>)')

def nadekofy(string):
    return html.parser.unescape(
        validify_tags.sub(r'\1',
            invalid_tags.sub('', 
                paragraphy.sub('\n',
                    unhr.sub('—————————', 
                        valid_tags.sub(r'\<\2\3\>',
                            unesq_left.sub('<', 
                                unesq_right.sub('>', string)
                            )
                        )
                    )
                )
            )
        )
    ).strip()

def get_content(feed):
    try:
        if 'Tumblr' in feed['feed']['generator']:
            # We can use <summary>, but we need to make HTML Nadeko-compatible.
            return nadekofy(feed['entries'][0]['summary'])
        else:
            # Try to get the first Atom content value.
            # for Nadeko-compatible feeds this will be the plain text.
            return feed.entries[0].content[0].get(value) or ""
        #else:
        #    raise ValueError("Falling back to no content format.")
    except:
        # Fallback.
        return ""

class FeedSingleton(type):
    _instances = {}

    def __call__(cls, url):
        if url not in cls._instances:
            cls._instances[url] = super(FeedSingleton, cls).__call__(url)
        return cls._instances[url]


class RSSFeed(metaclass=FeedSingleton):
    def __init__(self, url):
        self.url = url
        self.subscribers = set()
        self.updated = None
        self.lastpost = None

    def subscribe(self, uid):
        self.subscribers.add(uid)

    def unsubscribe(self, uid):
        self.subscribers.remove(uid)

    def check(self, bot, notify_status):
        feed = feedparser.parse(self.url)
        updated = datetime.datetime.fromtimestamp(time.mktime(
            feed.get('updated_parsed') or feed['entries'][0]['published_parsed']
        ))
        if self.updated != updated:
            # Feed is updated!
            self.updated = updated
            lastpost = feed['entries'][0]['id']
            if lastpost != self.lastpost:
                self.lastpost = lastpost
                for chatid in self.subscribers:
                    if isinstance(chatid, str) or notify_status.get('chatid') in [None, True]:
                        try:
                            msg = bot.send_message(
                                chat_id=chatid,
                                text=NEWPOST.format(
                                    title=feed['feed']['title'],
                                    url=feed['feed']['links'][0]['href'],
                                    post=urllib.parse.unquote(
                                        feed['entries'][0]['links'][0]['href']
                                    ),
                                    content=get_content(feed)
                                ), parse_mode="HTML"
                            )
                        except:
                            # Something went wrong, probably when getting content.
                            # XXX Lock the exception on BadRequest from bad markup.
                            msg = bot.send_message(
                                chat_id=chatid,
                                text=NEWPOST.format(
                                    title=feed['feed']['title'],
                                    url=feed['feed']['links'][0]['href'],
                                    post=urllib.parse.unquote(
                                        feed['entries'][0]['links'][0]['href']
                                    ),
                                    content="К сожалению, Телеграм ограничен в разметке, поэтому я не могу отправить содержимое поста. Пока что."
                                ), parse_mode="HTML"
                            )
                        # If target is a channel name, lock onto the channel ID
                        if isinstance(chatid, str):
                            self.subscribers.remove(chatid)
                            self.subscribers.add(msg.chat.id)

    def __getstate__(self):
        return self.__dict__.copy()

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __hash__(self):
        return hash(self.url)


class RSS(tg_bot.plugins.GenericPlugin):
    def __init__(self, updater):
        try:
            with open(path.join(datadir, 'rss.dat'), 'rb') as f:
                RSSFeed._instances.update(pickle.load(f))
        except FileNotFoundError:
            pass
        self.jobqueue = updater.job_queue
        self.updater = updater
        self.dsp = updater.dispatcher
        self.handlers = [
            (CommandHandler(
                'rss', self.reply, pass_job_queue=True,
                pass_args=True, pass_chat_data=True
            ), 0)
        ]
        self.feeds = set()
        chat_data = self.dsp.chat_data
        self.jobqueue.run_repeating(
            self.check_feeds, interval=60, first=0,
            context=lambda: {k: v.get('RSS_notify') for k, v in chat_data.items()}
        )

    def save_data(self):
        log.debug("Saving persistent data...")
        with open(path.join(datadir, 'rss.dat'), 'wb') as f:
            pickle.dump(RSSFeed._instances, f)
        log.debug("Done!")

    def check_feeds(self, bot, job):
        context = job.context()
        feeds = RSSFeed._instances.values()
        log.info("Checking updates for feeds...")
        for feed in feeds:
            log.info("Checking feed %s", feed.url)
            try:
                feed.check(bot, context)
            except:
                log.error("Error checking feed %s!", feed.url, exc_info=1)
        self.save_data()

    def reply(self, bot, update, args, chat_data, job_queue):
        try:
            cmd = args[0]
        except IndexError:
            update.message.reply_text(self.getHelp())
            return
        if cmd == "add":
            feeds = map(RSSFeed, args[1:])
            for feed in feeds:
                feed.subscribe(update.message.chat_id)
            update.message.reply_text("Добавила! Если найду новые посты, я сообщу! ^^")
        elif cmd == "channel":
            channelid = args[1]
            userid = update.message.from_user.id
            try:
                if userid not in map(lambda m: m.user.id, bot.get_chat_administrators(channelid)):
                    update.message.reply_text("Ты не являешься администратором этого канала.")
                    return
                feeds = map(RSSFeed, args[2:])
                for feed in feeds:
                    feed.subscribe(channelid)
                update.message.reply_text("Добавила! Если найду что-то новенькое, оповещу твоих подписчиков!")
            except BadRequest:
                update.message.reply_text("Ой! Кажется, я не являюсь администратором этого канала.")
        elif cmd == "notify":
            try:
                chat_data['RSS_notify'] = not chat_data['RSS_notify']
            except KeyError:
                chat_data['RSS_notify'] = False
            update.message.reply_text("Уведомления {}.".format(
                "включены" if chat_data['RSS_notify'] else "отключены"
            ))
        else:
            update.message.reply_text(self.getHelp())

    @staticmethod
    def getHelp():
        return stripln("""\
            /rss - читалка для RSS.
            /rss add <feed> - добавить новый фид по ссылке.
            /rss channel <id> <feed> - публиковать обновления фида в канал.
            Я должна быть в списке администраторов канала для публикации новых постов в канал.
            Если канал публичный, вместо id можно подставить @короткоеимя канала.
            Чтобы узнать ID приватного канала, воспользуйтесь @ChannelIDBot.
            /rss notify - включить/отключить уведомления.
            Об уведомлениях - каждые пять минут Нядэка проверяет \
            RSS-ленты, добавленные в этом чате, и отправляет \
            уведомления, если нашла что-то новенькое.""")
