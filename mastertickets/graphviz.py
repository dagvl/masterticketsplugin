# Created by Noah Kantrowitz on 2007-12-21.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
import os
import subprocess
import tempfile
import time
import itertools

try:
    set = set
except NameError:
    from sets import Set as set

def _format_options(base_string, options):
    return '%s [%s]'%(base_string, ', '.join(['%s="%s"'%x for x in options.iteritems()]))

class Edge(dict):
    """Model for an edge in a dot graph."""

    def __init__(self, source, dest, **kwargs):
        self.source = source
        self.dest = dest
        dict.__init__(self, **kwargs)

    def __str__(self):
        ret = '%s -> %s'%(self.source.name, self.dest.name)
        if self:
            ret = _format_options(ret, self)
        return ret

    def __hash__(self):
        return hash(id(self))


class Node(dict):
    """Model for a node in a dot graph."""

    def __init__(self, name, **kwargs):
        self.name = str(name)
        self.edges = set()
        dict.__init__(self, **kwargs)
        self['label'] = str(name)

    def __str__(self):
        ret = self.name
        if self:
            ret = _format_options(ret, self)
        return ret

    def __gt__(self, other):
        """Allow node1 > node2 to add an edge."""
        edge = Edge(self, other)
        self.edges.add(edge)
        other.edges.add(edge)
        return edge

    def __lt__(self, other):
        edge = Edge(other, self)
        self.edges.add(edge)
        other.edges.add(edge)
        return edge

    def __hash__(self):
        return hash(id(self))


class Graph(object):
    """A model object for a graphviz digraph."""

    def __init__(self, name='graph'):
        super(Graph,self).__init__()
        self.name = name
        self.nodes = {}
        self.edges = set()

    def add(self, obj):
        if isinstance(obj, Node):
            self.nodes[obj.name] = obj
        elif isinstance(obj, Edge):
            self.edges.add(obj)

    def __getitem__(self, key):
        key = str(key)
        if key not in self.nodes:
            self.nodes[key] = Node(key)
        return self.nodes[key]

    def __setitem__(self, key, val):
        key = str(key)
        self.nodes[key] = val

    def __delitem__(self, key):
        key = str(key)
        del self.nodes[key]

    def __str__(self):
        edges = set()
        nodes = set()
        
        memo = set()
        def process(lst):
            for obj in lst:
                if obj in memo:
                    continue
                memo.add(obj)
                
                if isinstance(obj, Node):
                    nodes.add(obj)
                    process(obj.edges)
                elif isinstance(obj, Edge):
                    edges.add(obj)
                    if isinstance(obj.source, Node):
                        process((obj.source,))
                    if isinstance(obj.dest, Node):
                        process((obj.dest,))
        
        process(self.nodes.itervalues())
        process(self.edges)
        
        lines = ['digraph "%s" {'%self.name]
        for obj in itertools.chain(nodes, edges):
            lines.append('\t%s;'%obj)
        lines.append('}')
        return '\n'.join(lines)

    def render(self, dot_path='dot', format='png'):
        """Render a dot graph."""
        proc = subprocess.Popen([dot_path, '-T%s'%format], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        out, _ = proc.communicate(str(self))
        return out


if __name__ == '__main__':
    g = Graph()
    root = Node('me')
    root > Node('them')
    root < Node('us')
    
    g.add(root)
    
    print g.render('dot')