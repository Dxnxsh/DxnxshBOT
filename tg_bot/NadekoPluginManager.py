#!/usr/bin/env python
"""Plugin system."""
import os
import re
import sys
import logging
import pkgutil
import traceback
import Nadeko.NadekoAPI.config as config
import Nadeko.modules
# pylint: disable=invalid-name, too-many-arguments,broad-except,too-many-nested-blocks,too-many-branches

BLACKLIST = config.getfromjson("modules", "blacklist")

if sys.version_info.minor < 6:
    ModuleNotFoundError = ImportError


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NadekoPluginManager(metaclass=Singleton):
    log = logging.getLogger(__name__)
    """Plugin Manager for Nadeko."""
    def __init__(self, plugin_dir, updater):
        """Save bot dispatcher value and pass everything else to super()."""
        self.plugin_dir = plugin_dir
        self.instances = []
        self.updater = updater

    def loadPlugin(self, cls):
        """Load a single plugin. Useful for pulling up dependencies."""
        inst = cls(self.updater)
        self.log.debug("Instantiating class %s", cls)
        inst.activate()
        self.instances.append(inst)
        return inst

    def loadPlugins(self, doreload=False):
        """Load plugins, reloading them if possible."""
        for _, module, ispkg in pkgutil.iter_modules(Nadeko.modules.__path__, Nadeko.modules.__name__ + "."):
            try:
                if module == '__pycache__' or module.startswith('.'):
                    continue
                elif re.search(r'\.py$', module):
                    module = module.replace(".py", "")
                if module.split('.')[-1] in BLACKLIST:
                    self.log.info("Plugin %s is blacklisted.", module)
                    continue
                self.log.info("Loading plugin %s...", module)
                plugin = __import__(module, globals(), locals(), "dummy", 0)
                self.loadPlugin(getattr(plugin, module.split('.')[-1]))
            except ModuleNotFoundError as e:
                self.log.error("Cannot import module %s for plugin %s, disabling.", e.name, module)
            except Exception as e:
                self.log.error('%s is not a module!', module)
                self.log.error(''.join(traceback.format_exception(*sys.exc_info())))
                continue
