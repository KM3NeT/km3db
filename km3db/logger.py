#!/usr/bin/env python3
from hashlib import sha256
import os
import re
import sys
import logging
import logging.handlers

loggers = {}  # this holds all the registered loggers


ATTRIBUTES = dict(
    list(
        zip(
            ["bold", "dark", "", "underline", "blink", "", "reverse", "concealed"],
            list(range(1, 9)),
        )
    )
)
del ATTRIBUTES[""]

ATTRIBUTES_RE = r"\033\[(?:%s)m" % "|".join(["%d" % v for v in ATTRIBUTES.values()])

HIGHLIGHTS = dict(
    list(
        zip(
            [
                "on_grey",
                "on_red",
                "on_green",
                "on_yellow",
                "on_blue",
                "on_magenta",
                "on_cyan",
                "on_white",
            ],
            list(range(40, 48)),
        )
    )
)

HIGHLIGHTS_RE = r"\033\[(?:%s)m" % "|".join(["%d" % v for v in HIGHLIGHTS.values()])

COLORS = dict(
    list(
        zip(
            [
                "grey",
                "red",
                "green",
                "yellow",
                "blue",
                "magenta",
                "cyan",
                "white",
            ],
            list(range(30, 38)),
        )
    )
)

COLORS_RE = r"\033\[(?:%s)m" % "|".join(["%d" % v for v in COLORS.values()])

RESET = r"\033[0m"
RESET_RE = r"\033\[0m"


def supports_color():
    """Checks if the terminal supports color."""
    if isnotebook():
        return True
    supported_platform = sys.platform != "win32" or "ANSICON" in os.environ
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    if not supported_platform or not is_a_tty:
        return False

    return True


def colored(text, color=None, on_color=None, attrs=None, ansi_code=None):
    """Colorize text, while stripping nested ANSI color sequences.

    Author:  Konstantin Lepa <konstantin.lepa@gmail.com> / termcolor

    Available text colors:
        red, green, yellow, blue, magenta, cyan, white.
    Available text highlights:
        on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white.
    Available attributes:
        bold, dark, underline, blink, reverse, concealed.
    Example:
        colored('Hello, World!', 'red', 'on_grey', ['blue', 'blink'])
        colored('Hello, World!', 'green')
    """
    if os.getenv("ANSI_COLORS_DISABLED") is None:
        if ansi_code is not None:
            return "\033[38;5;{}m{}\033[0m".format(ansi_code, text)
        fmt_str = "\033[%dm%s"
        if color is not None:
            text = re.sub(COLORS_RE + "(.*?)" + RESET_RE, r"\1", text)
            text = fmt_str % (COLORS[color], text)
        if on_color is not None:
            text = re.sub(HIGHLIGHTS_RE + "(.*?)" + RESET_RE, r"\1", text)
            text = fmt_str % (HIGHLIGHTS[on_color], text)
        if attrs is not None:
            text = re.sub(ATTRIBUTES_RE + "(.*?)" + RESET_RE, r"\1", text)
            for attr in attrs:
                text = fmt_str % (ATTRIBUTES[attr], text)
        return text + RESET
    else:
        return text


def hash_coloured_escapes(text):
    """Return the ANSI hash colour prefix and suffix for a given text"""
    ansi_code = int(sha256(text.encode("utf-8")).hexdigest(), 16) % 230
    prefix, suffix = colored("SPLIT", ansi_code=ansi_code).split("SPLIT")
    return prefix, suffix


def isnotebook():
    """Check if running within a Jupyter notebook"""
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False


def get_logger(name, filename=None, stream_loglevel="INFO", file_loglevel="DEBUG"):
    """Helper function to get a logger"""
    if name in loggers:
        return loggers[name]
    logger = logging.getLogger(name)
    logger.propagate = False

    with_color = supports_color()

    pre1, suf1 = hash_coloured_escapes(name) if with_color else ("", "")
    pre2, suf2 = hash_coloured_escapes(name + "salt") if with_color else ("", "")
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s {}+{}+{} "
        "%(name)s: %(message)s".format(pre1, pre2, suf1),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if filename is not None:
        ch_file = logging.handlers.RotatingFileHandler(
            filename, maxBytes=5 * 1024 * 1024, backupCount=10
        )
        ch_file.setLevel(file_loglevel)
        ch_file.setFormatter(formatter)
        logger.addHandler(ch_file)
    ch = logging.StreamHandler()
    ch.setLevel(stream_loglevel)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    loggers[name] = logger

    logger.once_dict = {}

    return logger


def set_level(log_or_name, level):
    """Set the log level for given logger"""
    if isinstance(log_or_name, str):
        log = get_logger(log_or_name)
    else:
        log = log_or_name
    log.setLevel(level)
    for handler in log.handlers:
        handler.setLevel(level)


if supports_color():
    logging.addLevelName(
        logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO)
    )
    logging.addLevelName(
        logging.DEBUG, "\033[1;34m%s\033[1;0m" % logging.getLevelName(logging.DEBUG)
    )
    logging.addLevelName(
        logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING)
    )
    logging.addLevelName(
        logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR)
    )
    logging.addLevelName(
        logging.CRITICAL,
        "\033[1;101m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL),
    )


log = get_logger("km3db")
set_level(log, "WARNING")
