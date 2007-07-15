from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.util.html import html, Markup

from genshi.core import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer 

from util import *
from model import TicketLinks

class MasterTicketsModule(Component):
    """Provides support for ticket dependencies."""
    
    implements(IRequestFilter, ITemplateStreamFilter, ITemplateProvider, ITicketManipulator)
    
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
            
        return template, data, content_type
        
    # ITemplateStreamFilter methods
    def match_stream(self, req, method, filename, stream, data):
        return req.path_info.startswith('/ticket/')

    def filter_stream(self, req, method, filename, stream, data):
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
        from pkg_resources import resource_filename
        return [('mastertickets', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        #from pkg_resources import resource_filename
        #return [resource_filename(__name__, 'templates')]
        return []

