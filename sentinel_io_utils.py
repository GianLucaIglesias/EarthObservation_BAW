"""
A module implementing utilities for extracting meta information from Sentinel data.
"""
import re
import xml.etree.ElementTree as ET



from pathlib import Path
from datetime import datetime
from sentinelhub.geometry import CRS, Geometry
from shapely.geometry.polygon import Polygon


class API_Error(Exception):
    def __init__(self, param_key, param_value):
        message = f"There is an error finding the {param_key} ({param_value}) in the Finder API."
        super().__init__(message)


def get_time_stamp_from_filename(file_name):
    """ """
    if re.search(r'(?<=_)\d\d\d\d\d\d\d\dT\d\d\d\d\d\d', file_name):
        time_string = re.search(r'(?<=_)\d\d\d\d\d\d\d\dT\d\d\d\d\d\d', file_name).group(0)
        year = int(time_string[0:4])
        month = int(time_string[4:6])
        day = int(time_string[6:8])
        hour = int(time_string[9:11])
        minute = int(time_string[11:13])
        second = int(time_string[13:15])
        stamp = datetime(year, month, day, hour, minute, second)

    else:
        raise ValueError('Time stamp could not be retrieved due to unknown date convention in the file name.')

    return stamp


def get_footprint_from_gcps(height: int, width: int, gcps: list, epsg_code: str):
    """ """
    for i in range(len(gcps)):
        if gcps[i].col == 0 and gcps[i].row == 0:
            p1 = (gcps[i].x, gcps[i].y)
        elif gcps[i].col == width - 1 and gcps[i].row == 0:
            p2 = (gcps[i].x, gcps[i].y)
        elif gcps[i].col == width - 1 and gcps[i].row == height - 1:
            p3 = (gcps[i].x, gcps[i].y)
        elif gcps[i].col == 0 and gcps[i].row == height - 1:
            p4 = (gcps[i].x, gcps[i].y)
    return Geometry(Polygon([p1, p2, p3, p4]), crs=CRS(epsg_code))


def get_footprint_from_manifest(product_id, feature_id='measurementFrameSet'):
    """ """
    if product_id.endswith("manifest.safe"):
        manifest_file_path = Path(product_id)
    else:
        manifest_file_path = Path(product_id) / Path("manifest.safe")

    tree = ET.parse(manifest_file_path)
    root = tree.getroot()

    i = 0
    for elem in root:
        for sub_elem in elem:
            if 'ID' in sub_elem.attrib.keys():
                if sub_elem.attrib['ID'] == feature_id:
                    while i < 8:
                        i += 1
                        for sub_sub_elem in sub_elem:
                            if 'srsName' in sub_sub_elem.attrib.keys():
                                if re.search(r'(?<=#)\d\d\d\d\d', sub_sub_elem.attrib['srsName']):
                                    epsg_code = re.search(r'(?<=#)\d\d\d\d\d', sub_sub_elem.attrib['srsName']).group()
                                else:
                                    epsg_code = re.search(r'(?<=#)\d\d\d\d', sub_sub_elem.attrib['srsName']).group()

                            if sub_sub_elem.tag.endswith('coordinates'):  # oder: if tag in sub_sub_elem.tag:
                                coordinates_text = sub_sub_elem.text
                                break
                            else:
                                sub_elem = sub_sub_elem
    coordinates = []  # list of 4 coordinate tuples
    coordinates_list_txt = coordinates_text.strip(' ').split(' ')

    if len(coordinates_list_txt) == 4:  # Format for S1 coordinates: altitude1,latitude1 alt2,lat2 ...
        for coordinate in coordinates_list_txt:
            coordinates.append((float(coordinate.split(',')[0]),
                                float(coordinate.split(',')[1])))
    elif len(coordinates_list_txt) > 4 and len(coordinates_list_txt) % 2 == 0:  # Format for S2 coordinates: altitude1 latitude1 alt2-4 lat2-4 alt1 lat1
        for i_coordinate in range(int(len(coordinates_list_txt)/2)):
            coordinate = (float(coordinates_list_txt[i_coordinate*2]), float(coordinates_list_txt[i_coordinate*2+1]))
            if not coordinate in coordinates:
                coordinates.append(coordinate)
    else:
        raise ValueError('Coordinates from feature text could not be interpreted.')

    return Geometry(Polygon(coordinates), crs=CRS(epsg_code))