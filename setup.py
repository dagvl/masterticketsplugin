#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracMasterTickets',
    version = '1.0',
    packages = ['mastertickets'],
    package_data = { 'mastertickets': ['htdocs/*.js', 'htdocs/*.css' ] },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Provides support for ticket dependencies and master tickets.",
    license = "BSD",
    keywords = "trac plugin ticket dependencies master",
    url = "http://trac-hacks.org/wiki/MasterTicketsPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracWebAdmin'],

    entry_points = {
        'trac.plugins': [
            'mastertickets.web_ui = mastertickets.web_ui',
        ]
    }
)
