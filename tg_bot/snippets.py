#!/usr/bin/env python
"""Various helper functions for making bot development easier."""
import re
import random


def callUserByName(user):
    """Get user first and last name and print 'em together."""
    first_name = user.first_name or ''
    last_name = (' ' + user.last_name) if user.last_name else ''
    return first_name + last_name


def callUser(user):
    """Version of callUserByName which can @mention user if available."""
    username = user.username
    val = callUserByName(user) if username is None else '@' + username
    return val


def randomLongLetter(letter, minimum, maximum):
    """Generate a randomly long string filled with same character."""
    assert isinstance(letter, str)
    return letter * random.randint(minimum, maximum)


def randomizeList(choices):
    """A shorthand for a list randomizer.
    Difference from random.shuffle() is that my shuffler copies the array."""
    args = choices.copy()
    return random.shuffle(args)


def kawaiiSmile(minimum=0, maximum=10):
    """Generate a ^_______^ kaomoji with randomization."""
    whiskers = bool(random.getrandbits(1))
    mouth = randomLongLetter('_', minimum, maximum)
    fangs = whiskers and bool(random.getrandbits(1)) and len(mouth) >= 2
    return ''.join([
        ('=' if whiskers else ''),
        '^', (',' if fangs else ''),
        mouth, (',' if fangs else ''),
        '^', ('=' if whiskers else '')
    ])


def stripln(string):
    """str.strip() every line of a string."""
    return '\n'.join(list(map(lambda string: string.strip(), string.splitlines())))


def format_list(lst, empty, header, numbered=True):
    """Generic list formatter.
        lst (list) - list that needs to be formatted
        header (str) - list header
        empty (str) - string to return if list is empty
    """
    string = '\n'.join(
        list(map(
            lambda t: "{} {}".format(t[0], t[1]),
            map(
                lambda i: (''.join([str(i[0]), '.']), i[1]),
                enumerate(lst, 1)
            ) if numbered else map(lambda i: ("-", i), lst)
        ))
    )
    if string is "":
        return empty
    else:
        return '\n'.join([header, string])


def inline_list(lst):
    """Format a list to string, separating elements by comma and adding "and" before the last element."""
    length = len(lst)
    if length <= 0:
        return ''
    if length == 1:
        return lst[0]
    return ', '.join(lst[:-1]) + ' и ' + lst[-1]


def me(username, text=None, nickname=None):
    """/me-format a string."""
    return (
        "<code>※</code> <b>{username}</b>{text}" if nickname is None else "<code>※</code> <b>{username}</b> ({nickname}) {text}"
    ).format(username=username, nickname=nickname, text="" if text is None else " "+text)


awoo = re.compile(r'(<(/?)(b|i|pre|code|a href="[^"]+")>)')
nya = re.compile(r'(?<!\\)[<]')
meow = re.compile(r'(?<!\\)[>]')
rawr = re.compile(r'\\(&lt;|<|>)')


def escape(string):
    """Escape invalid HTML tags."""
    return rawr.sub(r'\1', meow.sub('&gt;', nya.sub('&lt;', awoo.sub(r'\<\2\3\>', string))))
