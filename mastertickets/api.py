# Created by Noah Kantrowitz on 2007-07-04.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
import re

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import DatabaseManager
from trac.ticket.api import ITicketChangeListener, ITicketManipulator
from trac.util.compat import set

import db_default
from model import TicketLinks

class MasterTicketsSystem(Component):
    """Central functionality for the MasterTickets plugin."""

    implements(IEnvironmentSetupParticipant, ITicketChangeListener, ITicketManipulator)
    
    NUMBERS_RE = re.compile(r'\d+', re.U)
    
    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.found_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())
        
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (db_default.name,))
        value = cursor.fetchone()
        if not value:
            self.found_db_version = 0
            return True
        else:
            self.found_db_version = int(value[0])
            #self.log.debug('WeatherWidgetSystem: Found db version %s, current is %s' % (self.found_db_version, db_default.version))
            if self.found_db_version < db_default.version:
                return True
                
        # Check for our custom fields
        if 'blocking' not in self.config['ticket-custom'] or 'blockedby' not in self.config['ticket-custom']:
            return True
            
        # Fall through
        return False
            
    def upgrade_environment(self, db):
        db_manager, _ = DatabaseManager(self.env)._get_connector()
                
        # Insert the default table
        old_data = {} # {table_name: (col_names, [row, ...]), ...}
        cursor = db.cursor()
        if not self.found_db_version:
            cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",(db_default.name, db_default.version))
        else:
            cursor.execute("UPDATE system SET value=%s WHERE name=%s",(db_default.version, db_default.name))
            for tbl in db_default.tables:
                try:
                    cursor.execute('SELECT * FROM %s'%tbl.name)
                    old_data[tbl.name] = ([d[0] for d in cursor.description], cursor.fetchall())
                    cursor.execute('DROP TABLE %s'%tbl.name)
                except Exception, e:
                    if 'OperationalError' not in e.__class__.__name__:
                        raise e # If it is an OperationalError, just move on to the next table
                            
                
        for tbl in db_default.tables:
            for sql in db_manager.to_sql(tbl):
                cursor.execute(sql)
                    
            # Try to reinsert any old data
            if tbl.name in old_data:
                data = old_data[tbl.name]
                sql = 'INSERT INTO %s (%s) VALUES (%s)' % \
                      (tbl.name, ','.join(data[0]), ','.join(['%s'] * len(data[0])))
                for row in data[1]:
                    try:
                        cursor.execute(sql, row)
                    except Exception, e:
                        if 'OperationalError' not in e.__class__.__name__:
                            raise e

        custom = self.config['ticket-custom']
        config_dirty = False
        if 'blocking' not in custom:
            custom.set('blocking', 'text')
            custom.set('blocking.label', 'Blocking')
            config_dirty = True
        if 'blockedby' not in custom:
            custom.set('blockedby', 'text')
            custom.set('blockedby.label', 'Blocked By')
            config_dirty = True
        if config_dirty:
            self.config.save()
            
    # ITicketChangeListener methods
    def ticket_created(self, tkt):
        self.ticket_changed(tkt, '', tkt['reporter'], {})

    def ticket_changed(self, tkt, comment, author, old_values):
        db = self.env.get_db_cnx()
        
        links = TicketLinks(self.env, tkt, db)
        links.blocking = set(self.NUMBERS_RE.findall(tkt['blocking'] or ''))
        links.blocked_by = set(self.NUMBERS_RE.findall(tkt['blockedby'] or ''))
        links.save(author, comment, tkt.time_changed, db)
        
        db.commit()

    def ticket_deleted(self, tkt):
        db = self.env.get_db_cnx()
        
        links = TicketLinks(self.env, tkt, db)
        links.blocking = set()
        links.blocked_by = set()
        links.save('trac', 'Ticket #%s deleted'%tkt.id, when=None, db=db)
        
        db.commit()
        
    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        for field in ('blocking', 'blockedby'):
            try:
                ids = self.NUMBERS_RE.findall(ticket[field] or '')
                for id in ids[:]:
                    cursor.execute('SELECT id FROM ticket WHERE id=%s', (id,))
                    row = cursor.fetchone()
                    if row is None:
                        ids.remove(id)
                ticket[field] = ', '.join(sorted(ids, key=lambda x: int(x)))
            except Exception, e:
                self.log.debug('MasterTickets: Error parsing %s "%s": %s', field, ticket[field], e)
                yield field, 'Not a valid list of ticket IDs'