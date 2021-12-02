import subprocess
import sys
import re
import xml.etree.ElementTree as ET


from SNAP_utils import SNAP_BIN, snap_exists
from SNAP_Operators import SNAP_Node


EMPTY_GRAPH = r"empty_graph.xml"


class SNAP_GPF:
    def __init__(self, graph_id, snap_bin=SNAP_BIN):

        self.graph_id = graph_id
        self.snap_exe_path = snap_exists(snap_bin)
        self.xml_tree = None
        self.nodes = []

    def append_nodes(self, nodes):
        if type(nodes) == list:
            for node in nodes:
                if not isinstance(node, SNAP_Node):
                    raise ValueError(f"The node {node} was found not be a SNAP_Node and could not be appended to the Graph")
            self.nodes = nodes
        elif type(nodes) == SNAP_Node:
            self.nodes.append(nodes)
        else:
            raise ValueError("Could not append nodes to the SNAP Graph. Nodes is expected to be of list or "
                             "SNAP_Node type")

    def from_xml(self, xml_file=EMPTY_GRAPH):
        self.xml_tree = ET.parse(xml_file)
        return self.xml_tree

    def to_xml(self, output_graph):
        if len(self.nodes) == 0:
            raise ValueError("There are no nodes in the Graph.")

        # edit the graphs id
        tree = self.from_xml()
        for element in tree.iter():
            if element.tag == 'graph':
                element.set('id', self.graph_id)
                graph_root = element

        # append the nodes as elements to the graphs tree
        for node in self.nodes:
            graph_root.append(node.to_xml_element())

        if not output_graph.endswith('.xml'):
            output_graph += '.xml'
        tree.write(output_graph, encoding='utf-8', xml_declaration=True)
