# -*- coding: utf-8 -*-

from pkg_resources import get_distribution
pkgInfo = get_distribution(__name__.split('.')[0]).get_metadata('PKG-INFO')

from email import message_from_string
pkg = message_from_string(pkgInfo)

__version__ = pkg['version']
__author__ = pkg['author']
__license__ = pkg['license']
