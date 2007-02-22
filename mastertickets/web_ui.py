from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.util.html import html, Markup

from util import *

class MasterTicketsModule(Component):
    """Provides support for ticket dependencies."""
    
    implements(IRequestFilter, ITemplateProvider, ITicketManipulator)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, content_type):
        if req.path_info.startswith('/ticket'):
            tkt_id = req.path_info[8:]
            
            # jQuery!
            add_script(req, 'mastertickets/jquery.js')
            
            # Add in the 'Blocked by' field
            blocking_ids = blocked_by(self.env, tkt_id)
            if blocking_ids:
                req.hdf['ticket.blockedby'] = ', '.join([str(x) for x in blocking_ids])
                req.hdf['ticket.fields.blockedby'] = {
                    'value': '',
                    'custom': 1,
                    'type': 'text',
                    'label': 'Blocked By',
                    'order': 10, # Force this to be at the end, since I am going to disappear it.
                }
                add_stylesheet(req, 'mastertickets/ticket.css')
                add_script(req, 'mastertickets/linkify_blockedby.js')
                
                # If any blockers are not closed, disable the resovle option
                img_src, img_alt = 'checkmark.gif', 'Blockers closed'
                for i in blocking_ids:
                    if Ticket(self.env, i)['status'] != 'closed':
                        if Ticket(self.env, tkt_id)['status'] != 'closed':
                            add_script(req, 'mastertickets/disable_resolve.js')
                            img_src, img_alt = 'x.png', 'Blockers open'
                        else:
                            img_src, img_alt = 'caution.png', 'Blockers open, but current ticket closed'
                         
                # Magic stuff in the footer
                req.hdf['project.footer'] = Markup(req.hdf['project.footer'] + Markup(html.DIV(html.IMG(class_='blockedby_icon', src=req.href.chrome('mastertickets',img_src), alt=img_alt, title=img_alt), ' ', linkify_ids(self.env, req, blocking_ids), id='linkified_blockedby', style='display:none')))
                
            
            # Linkify the 'Blocks' field
            blocks_ids = req.hdf.get('ticket.blocking')
            blocks_ids = blocks_ids.replace('#', '')
            if blocks_ids:
                blocks_ids = [x.strip() for x in blocks_ids.split(',')]
                req.hdf['project.footer'] = Markup(req.hdf['project.footer'] + Markup(html.DIV(linkify_ids(self.env, req, blocks_ids), id='linkified_blocking', style='display:none')))
                add_script(req, 'mastertickets/linkify_blocking.js')
            
        return template, content_type
        
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

