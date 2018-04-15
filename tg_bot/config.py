# Create a new config.py file in same dir and import, then extend this class.
class Config(object):
    LOGGER = True

    # REQUIRED
    API_KEY = "531470781:AAFH4b4LAIubsFfyljjdYvQnI2qWKvmWhvQ"    
    OWNER_ID = "462346966"  # If you dont know, run the bot and do /id in your private chat with it
    OWNER_USERNAME = "Dxnxsh"

    # RECOMMENDED
    SQLALCHEMY_DATABASE_URI ='postgres://xvcvmtghoxawjg:fa1e4144be6d88ee991f6bb9b35a9f2bae55dc42541b4f7d8e63aec2313b0c19@ec2-54-221-192-231.compute-1.amazonaws.com:5432/d70mlirihnovou'  # needed for any database modules
    MESSAGE_DUMP = None  # needed to make sure 'save from' messages persist
    LOAD = []
    NO_LOAD = ['translation']
    WEBHOOK = False
    URL = None

    # OPTIONAL
    SUDO_USERS = []  # List of id's (not usernames) for users which have sudo access to the bot.
    SUPPORT_USERS = []  # List of id's (not usernames) for users which are allowed to gban, but can also be banned.
    WHITELIST_USERS = []  # List of id's (not usernames) for users which WONT be banned/kicked by the bot.
    DONATION_LINK = None  # EG, paypal
    CERT_PATH = None
    PORT = 5000
    DEL_CMDS = False  # Whether or not you should delete "blue text must click" commands
    STRICT_GBAN = False
    WORKERS = 8  # Number of subthreads to use. This is the recommended amount - see for yourself what works best!
    BAN_STICKER = 'CAADAgADOwADPPEcAXkko5EB3YGYAg'  # banhammer marie sticker
    ALLOW_EXCL = False  # Allow ! commands as well as /


class Production(Config):
    LOGGER = False


class Development(Config):
    LOGGER = True