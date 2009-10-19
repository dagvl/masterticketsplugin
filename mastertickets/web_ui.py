import subprocess

from pkg_resources import resource_filename
from genshi.core import Markup, START, END, TEXT
from genshi.builder import tag
from genshi.filters.transform import StreamBuffer, Transformer

from trac.core import *
from trac.web.api import IRequestHandler, IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script, \
                            add_ctxtnav
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.config import Option, BoolOption
from trac.util.html import html, Markup
from trac.util.compat import set, sorted, partial

import graphviz
from util import *
from model import TicketLinks

class MasterTicketsModule(Component):
    """Provides support for ticket dependencies."""
    
    implements(IRequestHandler, IRequestFilter, ITemplateStreamFilter, 
               ITemplateProvider, ITicketManipulator)
    
    dot_path = Option('mastertickets', 'dot_path', default='dot',
                      doc='Path to the dot executable.')
    gs_path = Option('mastertickets', 'gs_path', default='gs',
                     doc='Path to the ghostscript executable.')
    use_gs = BoolOption('mastertickets', 'use_gs', default=False,
                        doc='If enabled, use ghostscript to produce nicer output.')
    
    FIELD_XPATHS = {
        'query': 'table[@class="listing tickets"]/tbody/td[@class="%s"]/text()',
        'ticket_id': 'table[@class="listing tickets"]/tbody/td[@class="id"]/a/text()',
        'ticket': 'div[@id="ticket"]/table[@class="properties"]/td[@headers="h_%s"]/text()',
    }
    fields = set(['blocking', 'blockedby'])
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        if data is not None:
            if req.path_info.startswith('/query'):
                tkts = data['tickets']
            elif req.path_info.startswith('/ticket'):
                tkts = [data['ticket']]
            else:
                tkts = []

            if tkts:
                add_stylesheet(req, 'mastertickets/ticket.css')
            #self.log.debug("MasterTickets ticket list: %s", tkts)
            #self.log.debug("MasterTickets pre-mod data: %s", data)
            data['mastertickets'] = {}

            for tkt in tkts:
                #tkt = data['ticket']
                if not isinstance(tkt, Ticket):
                    try:
                        tkt = Ticket(self.env, tkt)
                    except TypeError:
                        tkt = Ticket(self.env, tkt['id'])
                #self.log.debug("MasterTickets Ticket: %s", tkt)
                links = TicketLinks(self.env, tkt)
            
                #FIXME: Not sure how the following is affected by the new
                #       query screen functionality
                for i in links.blocked_by:
                    if Ticket(self.env, i)['status'] != 'closed':
                        add_script(req, 'mastertickets/disable_resolve.js')
                        break

                #Prepending # to the ticket id to ease lookup via xpath later
                data['mastertickets']['#%s' % tkt.id] = {
                    'blocking': linkify_ids(self.env, req, links.blocking),
                    'blockedby': linkify_ids(self.env, req, links.blocked_by),
                }
            
                # Add link to depgraph if needed
                # Suppressed on query screen, as there could be many tickets
                if links and not req.path_info.startswith('/query'):
                    add_ctxtnav(req, 'Depgraph', req.href.depgraph(tkt.id))
            
                for change in data.get('changes', {}):
                    if not change.has_key('fields'):
                        continue
                    for field, field_data in change['fields'].iteritems():
                        if field in self.fields:
                            new = set()
                            old = set()

                            if field_data['new'].strip():
                                try:
                                    new = set([int(n) for n in field_data['new'].split(',')])
                                except ValueError, e:
                                    pass #we ignore unparsable fields

                            if field_data['old'].strip():
                                try:
                                    old = set([int(n) for n in field_data['old'].split(',')])
                                except ValueError, e:
                                    pass #we ignore unparsable fields

                            add = new - old
                            sub = old - new
                            elms = tag()
                            if add:
                                elms.append(
                                    tag.em(u', '.join([unicode(n) for n in sorted(add)]))
                                )
                                elms.append(u' added')
                            if add and sub:
                                elms.append(u'; ')
                            if sub:
                                elms.append(
                                    tag.em(u', '.join([unicode(n) for n in sorted(sub)]))
                                )
                                elms.append(u' removed')
                            field_data['rendered'] = elms
            
        return template, data, content_type
        
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if 'mastertickets' in data:
            if req.path_info.startswith('/query'):
                #Implementation cribbed from:
                #http://genshi.edgewall.org/wiki/ApiDocs/genshi.filters.transform#genshi.filters.transform:Transformer:copy
                id_xpath = self.FIELD_XPATHS['ticket_id']
                #The out-of-scope data must be passed in as optional parameter
                #global didn't seem to work
                def replace_text(ticket_id, field, data=data['mastertickets']):
                    if ticket_id in data:
                        return data[ticket_id][field]
                    else:
                        #Shouldn't ever happen
                        return 'There was an error retrieving %s tickets' % field
                template = dict([(fld, {'buff': StreamBuffer(),
                                        'xpath': self.FIELD_XPATHS['query'] % fld}) \
                                    for fld in self.fields])
                for fld_name, fld_data in template.iteritems():
                    fld_buff, fld_xpath = fld_data['buff'], fld_data['xpath']
                    func = lambda buff=fld_buff, fld=fld_name: replace_text(str(buff), fld)
                    stream |= Transformer(id_xpath).copy(fld_buff).end().select(fld_xpath).replace(func)
                
            elif req.path_info.startswith('/ticket'):
                xpath = self.FIELD_XPATHS['ticket']
                #Should only ever be one tkt_id           
                for tkt_id, field_values in data['mastertickets'].iteritems():
                    for field, value in field_values.iteritems():
                        stream |= Transformer(xpath % field).replace(value)
        return stream
        
    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass
        
    def validate_ticket(self, req, ticket):
        if req.args.get('action') == 'resolve':
            links = TicketLinks(self.env, ticket)
            for i in links.blocked_by:
                if not Ticket(self.env, i)['status'] in ['closed', 'resolved']:
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
        g = self._build_graph(req, tkt_id)
        if '/' in path_info or 'format' in req.args:
            
            format = req.args.get('format')
            if format == 'text':
                req.send(str(g), 'text/plain')
            elif format == 'debug':
                import pprint
                req.send(pprint.pformat(TicketLinks(self.env, tkt_id)), 'text/plain')
            elif format is not None:
                req.send(g.render(self.dot_path, format), 'text/plain')
            
            if self.use_gs:
                ps = g.render(self.dot_path, 'ps2')
                gs = subprocess.Popen([self.gs_path, '-q', '-dTextAlphaBits=4', '-dGraphicsAlphaBits=4', '-sDEVICE=png16m', '-o', '%stdout%', '-'], 
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                img, err = gs.communicate(ps)
                if err:
                    self.log.debug('MasterTickets: Error from gs: %s', err)
            else:
                img = g.render(self.dot_path)
            req.send(img, 'image/png')
        else:
            data = {}
            
            tkt = Ticket(self.env, tkt_id)
            data['tkt'] = tkt
            data['graph'] = g
            data['graph_render'] = partial(g.render, self.dot_path)
            data['use_gs'] = self.use_gs
            
            add_ctxtnav(req, 'Back to Ticket #%s'%tkt.id, req.href.ticket(tkt_id))
            return 'depgraph.html', data, None

    def _build_graph(self, req, tkt_id):
        links = TicketLinks(self.env, tkt_id)
        
        g = graphviz.Graph()
        
        node_default = g['node']
        node_default['style'] = 'filled'
        
        edge_default = g['edge']
        edge_default['style'] = ''
        
        # Force this to the top of the graph
        g[tkt_id] 
        
        links = sorted(links.walk(), key=lambda link: link.tkt.id)
        for link in links:
            tkt = link.tkt
            node = g[tkt.id]
            node['label'] = u'#%s'%tkt.id
            node['fillcolor'] = tkt['status'] == 'closed' and 'green' or 'red'
            node['URL'] = req.href.ticket(tkt.id)
            node['alt'] = u'Ticket #%s'%tkt.id
            node['tooltip'] = tkt['summary']
            
            for n in link.blocking:
                node > g[n]
        
        return g

