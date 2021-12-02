import subprocess
import sys
import xml.etree.ElementTree as ET

from SNAP_utils import SNAP_BIN, snap_exists


def append_subelements_from_list(parameter:list, parent_element, tag=None):
    if tag:
        parent = ET.SubElement(parent_element, tag)
    else:
        parent = parent_element

    for param in parameter:
        subelement = ET.SubElement(parent, param[0])
        subelement.text = param[1]
    return parent_element


def append_subelement_from_str(parameter, parent_element, subelement_key):
    subelement = ET.SubElement(parent_element, subelement_key)
    subelement.text = parameter
    return parent_element


def append_dict_to_xml_subelement(parent_element: ET.Element, element_tag:str, parameter_dict:dict):
    current_subelement = ET.SubElement(parent_element, element_tag)
    print(f"New Parameter found {element_tag}")
    for key in list(parameter_dict.keys()):
        head_parameter = parameter_dict[key]
        current_parameter = head_parameter

        if type(current_parameter) == list:
            current_subelement = append_subelements_from_list(current_parameter, current_subelement, key)
        elif type(current_parameter) == str:
            current_subelement = append_subelement_from_str(current_parameter, current_subelement, key)

    # sicher gehen dass alle dictionaries durchgangen werden (horizontal)
        while type(current_parameter) == dict:
            print(f'New Subelement added {key}')
            sub_parameter_keys = list(current_parameter.keys())
            current_subelement = ET.SubElement(current_subelement, key)

            for key in sub_parameter_keys:
                print(f'New Subparameter found {key}')
                # sicher gehen dass alle keys in einem dictionary durchgangen werden
                sub_parameter = current_parameter[key]

                if type(sub_parameter) == list:
                    current_subelement = append_subelements_from_list(sub_parameter, current_subelement)
                elif type(sub_parameter) == str:
                    current_subelement = append_subelement_from_str(sub_parameter, current_subelement, key)
                else:
                    raise ValueError(f'Could not parse the parameter dictionary due to an unexpected parameter type.')

            current_parameter = head_parameter
            break






class SNAP_Node:
    def __init__(self, node_id, operator=str(), sources=dict(), parameters=dict()):
        self.node_id = node_id
        self.operator = operator
        self.sources = sources
        self.parameters = parameters

    def __str__(self):
        return str(self.node_id)

    def to_xml_element(self):
        """ Creates a node in the xml format for the SNAP Graphical Processing Framework. """
        gpf_node = ET.Element('node')
        gpf_node.set('id', self.node_id)
        operator = ET.SubElement(gpf_node, 'operator')
        operator.text = self.operator

        append_dict_to_xml_subelement(parent_element=gpf_node, element_tag='sources', parameter_dict=self.sources)
        if type(self.parameters) == dict:
            append_dict_to_xml_subelement(parent_element=gpf_node, element_tag='parameters', parameter_dict=self.parameters)
        elif type(self.parameters) == list:
            gpf_node = append_subelements_from_list(parent_element=gpf_node, parameter=self.parameters, tag='parameters')

        return gpf_node

    def execute(self):
        process = subprocess.Popen(["dir"], shell=True)  # , stdout=subprocess.DEVNULL)
        print(f"Waiting for the {self.node_id}...")
        process.wait()
        if process.returncode == 0:
            print(f"{self.node_id} done!")
        else:
            print(f"Wuuuups, something went wrong! ")


class ExtractBand(SNAP_Node):
    def __init__(self, target_band_name, node_id="ExtractBand", expression=str(), description=str(), type='int32',
                 no_data_value='Nan'):

        parameters = {'targetBands': {'targetBand': [('name', target_band_name), ('expression', expression),
                                                     ('description', description), ('type', type),
                                                     ('noDataValue', no_data_value)]}}
        sources = {'sourceProducts': '${sourceProducts}'}

        super().__init__(node_id, operator="BandMaths", sources=sources, parameters=parameters)

class Write(SNAP_Node):
    def __init__(self, node_id, file, format_name='GeoTIFF', delete_on_failure=False, write_entire_tile_rows=False,
                 clear_cache_after_row_write=True):
        parameters = [('file', file), ('formatName', str(format_name)),
                      ('deleteOutputOnFailure', str(delete_on_failure)),
                      ('writeEntireTileRows', str(write_entire_tile_rows)),
                      ('clearCacheAfterRowWrite', str(clear_cache_after_row_write))]
        sources = {'source': '${source}'}

        super().__init__(node_id, operator="Write", sources=sources, parameters=parameters)