from pkg_resources import resource_filename
from genshi.core import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer

from trac.core import *
from trac.web.api import IRequestHandler, IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script, \
                            add_ctxtnav
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.util.html import html, Markup
from trac.util.compat import set

import graphviz
from util import *
from model import TicketLinks

class MasterTicketsModule(Component):
    """Provides support for ticket dependencies."""
    
    implements(IRequestHandler, IRequestFilter, ITemplateStreamFilter, 
               ITemplateProvider, ITicketManipulator)
    
    FIELD_XPATH = 'div[@id="ticket"]/table[@class="properties"]/td[@headers="h_%s"]/text()'
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/ticket/'):
            tkt = data['ticket']
            links = TicketLinks(self.env, tkt)
            
            for i in links.blocked_by:
                if Ticket(self.env, i)['status'] != 'closed':
                    add_script(req, 'mastertickets/disable_resolve.js')
                    break

            data['mastertickets'] = {
                'field_values': {
                    'blocking': linkify_ids(self.env, req, links.blocking),
                    'blockedby': linkify_ids(self.env, req, links.blocked_by),
                },
            }
            
            # Add link to depgraph if needed
            if links:
                add_ctxtnav(req, 'Depgraph', req.href.depgraph(tkt.id))
            
        return template, data, content_type
        
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if 'mastertickets' in data:
            for field, value in data['mastertickets']['field_values'].iteritems():
                stream |= Transformer(self.FIELD_XPATH % field).replace(value)
        return stream
        
    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass
        
    def validate_ticket(self, req, ticket):
        if req.args.get('action') == 'resolve':
            links = TicketLinks(self.env, ticket)
            for i in links.blocked_by:
                if Ticket(self.env, i)['status'] != 'closed':
                    yield None, 'Ticket #%s is blocking this ticket'%i

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('mastertickets', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return [resource_filename(__name__, 'templates')]

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/depgraph')

    def process_request(self, req):
        path_info = req.path_info[10:]
        
        if not path_info:
            raise TracError('No ticket specified')
        
        tkt_id = path_info.split('/', 1)[0]
        if '/' in path_info:
            g = graphviz.Graph()
            root = graphviz.Node(tkt_id)
            g.add(root)
            
            memo = set()
            def visit(tkt, next_fn):
                if tkt in memo:
                    return
                memo.add(tkt)
                
                tkt = Ticket(self.env, tkt)
                node = g[tkt.id]
                node['label'] = '#%s'%tkt.id
                node['style'] = 'filled'
                node['fillcolor'] = tkt['status'] == 'closed' and 'red' or 'green'
                
                links = TicketLinks(self.env, tkt)
                if tkt.id != tkt_id:
                    for n in links.blocking:
                        node > g[n]
                
                for n in next_fn(links):
                    visit(n, next_fn)
            
            links = TicketLinks(self.env, tkt_id)
            for n in links.blocking:
                g[tkt_id] > g[n]
            visit(tkt_id, lambda links: links.blocking)
            memo = set()
            visit(tkt_id, lambda links: links.blocked_by)
            
            img = g.render('/opt/local/bin/dot')
            req.send(img, 'image/png')
        else:
            data = {}
            
            tkt = Ticket(self.env, tkt_id)
            data['tkt'] = tkt
            
            add_ctxtnav(req, 'Back to Ticket #%s'%tkt.id, req.href.ticket(tkt_id))
            return 'depgraph.html', data, None