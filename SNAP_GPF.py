import subprocess
import sys
import re
import xml.etree.ElementTree as ET


from SNAP_utils import SNAP_BIN, snap_exists
from SNAP_Operators import SNAP_Node

from datetime import datetime


EMPTY_GRAPH = r"empty_graph.xml"


def exectue_gpf(graph_file, sources: list, target_files=[], error_details=True, format='GeoTIFF'):
    options = []
    if target_files:
        if type(target_files) == str:
            options.append(f"t {target_files} ")
        elif type(target_files) == list:
            options.append(f"t ")
            for target in target_files:
                options.append(str(target).strip())
        else:
            raise ValueError(f"The file parameters did not follow an expected format. Either a list or a string is expected.")

    if error_details:
        options.append("-e")
    # if format:
    #     options.append("-f")
    #     options.append(format)

    if type(sources) == str:
        options.append(sources)
    elif type(sources) == list:
        for source in sources:
            options.append(str(source).strip())
    else:
        raise ValueError(f"The file parameters did not follow an expected format. Either a list or a string is expected.")

    cmd_list = ["gpt", graph_file] + options
    print(f"Executing the command: \n{cmd_list}")

    process = subprocess.Popen(cmd_list, shell=True)  # , stdout=subprocess.DEVNULL
    process.wait()

    if process.returncode == 0:
        print(f"Executing the graph: {graph_file} done!")
    else:
        print(f"Wuuuups, something went wrong! ")


class SNAP_Branch:
    def __init__(self, branch_id, sources, targets=None):
        self.branch_id = branch_id
        self.sources = sources
        self.targets = targets

        self.nodes = []

    def append_nodes(self, nodes):
        if not nodes:
            raise ValueError("The statement of nodes is required.")

        if type(nodes) == list:
            for node in nodes:
                if not isinstance(node, SNAP_Node):
                    raise ValueError(f"The node {node} was found not be a SNAP_Node and could not be appended to the Graph")
            nodes_to_append = nodes
        elif type(nodes) == SNAP_Node:
            nodes_to_append = [nodes]
        else:
            raise ValueError("Could not append nodes to the SNAP Graph. Nodes is expected to be of list or "
                 "SNAP_Node type")

        for node in nodes_to_append:
            if self.nodes:  # there are existing nodes in the branch
                node.set_source(self.nodes[-1].node_id)
            self.nodes.append(node)


    def execute(self, graph_file_name=None, error_details=True):
        gpf = self.to_gpf()
        gpf.execute(graph_file_name=graph_file_name, error_details=error_details)

    def to_xml(self, output_graph):
        gpf = self.to_gpf()
        gpf.to_xml(output_graph)

    def to_gpf(self, snap_bin=SNAP_BIN):
        return SNAP_GPF(graph_id=self.branch_id, sources=self.sources, snap_bin=snap_bin, branches=self.nodes)


class SNAP_GPF:
    def __init__(self, graph_id, sources, snap_bin=SNAP_BIN, branches=[], targets=None):
        self.graph_id = graph_id
        self.snap_exe_path = snap_exists(snap_bin)
        self.xml_tree = None

        self.sources = sources
        self.targets = targets

        self.branches = branches

    def from_xml(self, xml_file=EMPTY_GRAPH):
        self.xml_tree = ET.parse(xml_file)
        return self.xml_tree

    def to_xml(self, output_graph):
        if len(self.branches) == 0:
            raise ValueError("There are no nodes in the Graph.")
        # edit the graphs id
        tree = self.from_xml()
        for element in tree.iter():
            if element.tag == 'graph':
                element.set('id', self.graph_id)
                graph_root = element
        # append the nodes as elements to the graphs tree
        for node in self.branches:
            graph_root.append(node.to_xml_element())

        if not output_graph.endswith('.xml'):
            output_graph += '.xml'
        print(f'Writing the graph to {output_graph}')
        tree.write(output_graph, encoding='utf-8', xml_declaration=True)

    def execute(self, graph_file_name=None, error_details=True):
        if not graph_file_name:
            now = datetime.now().strftime("%d%m%Y_%H-%M")
            graph_file = "graph_" + now + ".xml"
        else:
            graph_file = graph_file_name
            if not graph_file.endswith('.xml'):
                graph_file += '.xml'

        self.to_xml(graph_file_name)

        if not self.sources:
            raise ValueError('Please set the source files prior to executing the processing graph.')

        exectue_gpf(graph_file, sources=self.sources, target_files=self.targets, error_details=error_details)
