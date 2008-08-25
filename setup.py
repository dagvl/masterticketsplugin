#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracMasterTickets',
    version = '2.1.3',
    packages = ['mastertickets'],
    package_data = { 'mastertickets': ['templates/*.html', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Provides support for ticket dependencies and master tickets.',
    license = 'BSD',
    keywords = 'trac plugin ticket dependencies master',
    url = 'http://trac-hacks.org/wiki/MasterTicketsPlugin',
    classifiers = [
        'Framework :: Trac',
        #'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    install_requires = ['Trac>=0.11', 'Genshi>=0.5'],

    entry_points = {
        'trac.plugins': [
            'mastertickets.web_ui = mastertickets.web_ui',
            'mastertickets.api = mastertickets.api',
        ]
    }
)
