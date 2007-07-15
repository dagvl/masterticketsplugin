from trac.ticket.model import Ticket
from trac.context import ResourceNotFound
from trac.util.html import html, Markup

from genshi.builder import tag

__all__ = ['blocked_by', 'linkify_ids']

def blocked_by(env, tkt):
    if isinstance(tkt, Ticket):
        tkt = tkt.id # Allow passing a Ticket object
    
    db = env.get_db_cnx()
    cursor = db.cursor()
    
    cursor.execute('SELECT ticket FROM ticket_custom WHERE name=%s AND (value LIKE %s OR value LIKE %s)', 
                   ('blocking', '%%%s,%%'%tkt, '%%%s'%tkt))
    blocking_ids = [row[0] for row in cursor]
    return blocking_ids
    
def linkify_ids(env, req, ids):
    data = []
    for id in sorted(ids, key=lambda x: int(x)):
        try:
            tkt = Ticket(env, id)
            data.append(tag.a('#%s'%tkt.id, href=req.href.ticket(tkt.id), class_='%s ticket'%tkt['status'], title=tkt['summary']))
        except ResourceNotFound:
            data.append('#%s'%id)
        data.append(', ')
    if data:
        del data[-1] # Remove the last comma if needed
    return tag.span(*data)
    #return Markup(', '.join([unicode(tag.a('#%s'%i, href=req.href.ticket(i), class_='%s ticket'%Ticket(env, i)['status'])) for i in ids]))