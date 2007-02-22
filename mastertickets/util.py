from trac.ticket.model import Ticket
from trac.util.html import html, Markup

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
    return Markup(', '.join([unicode(html.A('#%s'%i, href=req.href.ticket(i), class_='%s ticket'%Ticket(env, i)['status'])) for i in ids]))