#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.webdesign import lorem_ipsum
from django.db.models.fields import URLField
from dilla import spam
import random
import os
import decimal
import logging
import datetime
import time

log = logging.getLogger('dilla')

dictionary = getattr(settings, 'DICTIONARY', "/usr/share/dict/words")
if os.path.exists(dictionary) and \
        not getattr(settings, 'DILLA_USE_LOREM_IPSUM', False):
    d = open(dictionary, "r").readlines()
    _random_words = \
            lambda n: " ".join([random.choice(d).lower().rstrip() \
            for i in range(n)])
    _random_paragraph = lambda: _random_words(30).capitalize()
    _random_paragraphs = lambda n: \
            ".\n".join([_random_paragraph() for i in range(n)])
else:
    _random_words = lorem_ipsum.words
    _random_paragraphs = lorem_ipsum.paragraphs


@spam.global_handler('CharField')
def random_words(field):
    if isinstance(field, URLField):
        # this is somewhat nasty, URLField.get_internal_type
        # returns 'CharField'
        return "http://%s.com/%s/?%s=%s" % tuple(_random_words(4).split(" "))

    max_length = field.max_length
    words = _random_words(3)
    if max_length and len(words) > max_length:
        return words[max_length:]
    return words


@spam.global_handler('TextField')
def random_text(field):
    return _random_paragraphs(4)


@spam.global_handler('IPAddressField')
def random_ip(field):
    return ".".join([str(random.randrange(0, 255)) for i in range(0, 4)])


@spam.global_handler('SlugField')
def random_slug(field):
    return random_words(field).replace(" ", "-")


@spam.global_handler('NullBooleanField')
@spam.global_handler('BooleanField')
def random_bool(field):
    return bool(random.randint(0, 1))


@spam.global_handler('EmailField')
def random_email(field):
    return "%s@%s.%s" % ( \
             _random_words(1),
             _random_words(1),
             random.choice(["com", "org", "net", "gov", "eu"])
             )


@spam.global_handler('SmallIntegerField')
@spam.global_handler('IntegerField')
def random_int(field):
    return random.randint(-10000, 10000)


@spam.global_handler('BigIntegerField')
def random_bigint(field):
    return random.randint(- 10 ** 10, 10 ** 10)


@spam.global_handler('DecimalField')
def random_decimal(field):
    return decimal.Decimal(str(random.random() + random.randint(1, 20)))


@spam.global_handler('PositiveIntegerField')
def random_posint(field):
    return random.randint(0, 10000)


@spam.global_handler('DateField')
@spam.global_handler('TimeField')
@spam.global_handler('DateTimeField')
def random_datetime(field):
    """
    Calculate random datetime object between last and next month.
    Django interface is pretty tollerant at this point, so three
    decorators instead of three handlers here.
    """

    # This was actually pretty tricky and I wonder if it could be simplified
    # next_month and prev_month represented as datetime.date

    next_month = (datetime.date.today() + datetime.timedelta(365 / 12))
    prev_month = (datetime.date.today() - datetime.timedelta(365 / 12))

    # convert these two to unix timestamps

    ts1 = time.mktime(next_month.timetuple())
    ts2 = time.mktime(prev_month.timetuple())
    seed = random.random()

    # 1. substract earlier from later
    # 2. multiply it by random float in range 0..1
    # 3. add earlier time
    # 4. get the timetuple

    random_struct = time.localtime(ts2 + seed * (ts1 - ts2))

    # convert timetumple to a datetime object by converting it again
    # to unix timestamp and voila

    return datetime.datetime.fromtimestamp(time.mktime(random_struct))


@spam.global_handler('OneToOneField') # TODO Test it
@spam.global_handler('ForeignKey')
def random_fk(field, slice=None):
    Related = field.rel.to
    log.debug('Trying to find related object: %s' % Related)
    try:
        query = Related.objects.all().order_by('?')
        if field.rel.limit_choices_to:
            log.debug('Field %s has limited choices. \
                    Applying to query.' % field)
            query.filter(**field.rel.limit_choices_to)
        if slice:
            return query[:slice]
        return query[0]
    except IndexError, e:
        log.info('Could not find any related objects for %s' % field.name)
        return None
    except Exception, e:
        log.critical(str(e))


@spam.global_handler('ManyToManyField')
def random_manytomany(field):
    return random_fk(field, random.randint(1, 5))
