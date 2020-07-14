import logging
import sys
from logging import Logger
from logging.handlers import TimedRotatingFileHandler


class Snitch(Logger):
    '''Basic logging class for consistent handling'''
    def __init__(
        self,
        name,
        log_file=None,
        log_format="{asctime} - {name} - **{levelname}** - {message}",
        level='WARNING',
        *args,
        **kwargs
    ):
        self.formatter = logging.Formatter(log_format,
                                           datefmt='%Y-%m-%d %H:%M:%S',
                                           style='{'
                                           )
        self.log_file = log_file

        Logger.__init__(self, name, *args, **kwargs)

        self.addHandler(self.get_console_handler())
        if log_file:
            self.addHandler(self.get_file_handler())

        self.propogate = False  # Don't push up to parent

        self.setLevel(level)

    def get_console_handler(self):
        '''Create console logging output'''
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        return console_handler

    def get_file_handler(self):
        '''Create log file output, rotate log at midnight'''
        file_handler = TimedRotatingFileHandler(self.log_file, when="midnight")
        file_handler.setFormatter(self.formatter)
        return file_handler

    def snitch_level(self, level='WARNING'):
        '''Changle log level'''
        level = 'logging.' + level.upper()
 #       self.setLevel(level)
