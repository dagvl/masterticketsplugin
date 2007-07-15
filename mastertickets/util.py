from trac.ticket.model import Ticket
from trac.context import ResourceNotFound

from genshi.builder import tag

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
