# Created by Noah Kantrowitz on 2007-07-04.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.db import Table, Column

name = 'mastertickets'
version = 1
tables = [
    Table('mastertickets', key=('source','dest'))[
        Column('source'),
        Column('dest'),
    ],
]