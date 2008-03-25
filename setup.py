#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracMasterTickets',
    version = '2.1.1',
    packages = ['mastertickets'],
    package_data = { 'mastertickets': ['templates/*.html', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Provides support for ticket dependencies and master tickets.",
    license = "BSD",
    keywords = "trac plugin ticket dependencies master",
    url = "http://trac-hacks.org/wiki/MasterTicketsPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac', 'Genshi >= 0.5.dev-r698,==dev'],

    entry_points = {
        'trac.plugins': [
            'mastertickets.web_ui = mastertickets.web_ui',
            'mastertickets.api = mastertickets.api',
        ]
    }
)
