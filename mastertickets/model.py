# Created by Noah Kantrowitz on 2007-07-04.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
from trac.ticket.model import Ticket

class TicketLinks(object):
    """A model for the ticket links used MasterTickets."""
    
    def __init__(self, env, tkt_id, db=None):
        self.env = env
        self.tkt_id = tkt_id
        
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute('SELECT dest FROM mastertickets WHERE source=%s', (self.tkt_id,))
        self.blocking = [Ticket(self.env, num) for num, in cursor]
        
        cursor.execute('SELECT source FROM mastertickets WHERE dest=%s', (self.tkt_id,))
        self.blocked_by = [Ticket(self.env, num) for num, in cursor]
        
    def save(self, db=None):
        """Save new links."""
        handle_commit = False
        if db is None:
            db = self.env.get_db_cnx()
            handle_commit = True
        cursor = db.cursor()
        
        cursor.execute('DELETE FROM mastertickets WHERE source=%s OR dest=%s', (self.tkt_id, self.tkt_id))
        data = []
        for tkt in self.blocking:
            if isinstance(tkt, Ticket):
                tkt = tkt.id
            data.append((self.tkt_id, tkt))
        for tkt in self.blocked_by:
            if isisntance(tkt, Ticket):
                tkt = tkt.id
            data.append((tkt, self.tkt_id))
        
        cursor.executemany('INSERT INTO mastertickets (source, dest) VALUES (%s, %s)', data)
        
        if handle_commit:
            db.commit()
            
    def __repr__(self):
        def l(arr):
            arr2 = []
            for tkt in arr:
                if isinstance(tkt, Ticket):
                    tkt = tkt.id
                arr2.append(tkt)
            return '[%s]'%','.join(arr2)
            
        return '<mastertickets.model.TicketLinks blocking=%s blocked_by=%s>'% \
               (l(self.blocking), l(self.blocked_by))