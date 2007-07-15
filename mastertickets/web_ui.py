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
            
            data['field_types']['blocking'] = 'text'
            data['fields'].append({
                'label': 'Blocking',
                'name': 'blocking',
                'optional': False,
                'options': [],
                'skip': False,
                'type': 'text',
            })
            tkt['blocking'] = '1, 2'
            data['mastertickets'] = {
                'field_values': {
                    'blocking': tag.b('Foobar'),
                },
            }
            
        return template, data, content_type
        
    # ITemplateStreamFilter methods
    def match_stream(self, req, method, filename, stream, data):
        return req.path_info.startswith('/ticket/')

    def filter_stream(self, req, method, filename, stream, data):
        return stream | Transformer('div[@id="ticket"]/table[@class="properties"]/td[@headers="h_blocking"]/text()').replace(data['mastertickets']['field_values']['blocking'])
        
    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass
        
    def validate_ticket(self, req, ticket):
        if req.args.get('action') == 'resolve':
            for i in blocked_by(self.env, ticket):
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

