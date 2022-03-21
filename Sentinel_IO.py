# import required libraries
import boto3
import xml.etree.ElementTree as ET
import os

from re import search
from sentinelhub.geometry import BBox
from pyproj import Transformer
from os import remove as remove_file
from geometry_utils import point_in_bounding_box
from sentinel_io_utils import API_Error
from http_api_utils import append_directory, append_search_parameter, append_aoi, append_point, append_timestamp, make_url_request

# Define repository
HOST = 'http://data.cloud.code-de.org'
BUCKET = 'CODEDE'
FINDER_API = 'https://finder.code-de.org/resto/api'

class SentinelIOClient:
    def __init__(self, access_key, secret_key):
        self.ACCESS_KEY = access_key
        self.SECRET_KEY = secret_key
        self.aws_client = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                                       endpoint_url=HOST)
        self.product_list = []

    def find(self, collection: str, pretty=True, start_date=None, completion_date=None, processing_level=None,
             aoi=None, show_list=False):

        if '1' in str(collection):
            collection = 'Sentinel1'
            processing_level = 'LEVEL1'
        elif '2' in str(collection):
            collection = 'Sentinel2'
            if processing_level == 1:
                processing_level = 'LEVEL1C'
            if processing_level == 2:
                processing_level = 'LEVEL2A'
        else:
            raise API_Error('collection', collection)

        finder_URL = append_directory(FINDER_API, ['collections', collection, 'search.json?'])

        # if pretty:
        #     finder_URL = append_search_parameter(finder_URL, ('_pretty', 'true'))

        if processing_level:
            finder_URL = append_search_parameter(finder_URL + '&', ('processingLevel', processing_level))

        if start_date or completion_date:
            finder_URL = append_timestamp(start=start_date, end=completion_date,
                                          base_url=finder_URL + '&', api='code-de')

        if aoi:
            if type(aoi) == tuple:
                if aoi[0] > aoi[1]:
                    print("Please make sure the coordinates are stated as: (longitud,latitude)")
                finder_URL = append_point(finder_URL + '&', aoi[0], aoi[1])

            if type(aoi) == list:
                if not len(aoi) == 2:
                    raise ValueError('The aoi has to be a list of the upper left and bottom right coordinate of a '
                                     'bounding box in epsg:4236 Coordinates e.g: [(8.41330, 49.34067), (8.50788,49.26702)]')
                finder_URL = append_aoi(finder_URL + '&', lower_left=aoi[0], upper_right=aoi[1])

        finder_dict = make_url_request(finder_URL).json()
        if finder_dict['type'] == 'FeatureCollection':
            for feature in finder_dict['features']:
                self.product_list.append(feature)

        print(f"Found {len(self.product_list)} products.")
        if show_list:
            for feature in self.product_list:
                print(feature['properties']['productIdentifier'])
        return

    def download_product(self, productID, download_path=None, secret_key=None, access_key=None):
        s3_resource = boto3.resource('s3')
        if not secret_key:
            secret_key = self.secret_key
        if not access_key:
            access_key = self.access_key
        bucket = s3_resource.Bucket(BUCKET, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        print(f"Product to be downloaded {productID}")
        for obj in bucket.objects.filter(Prefix=productID):
            if not os.path.exists(os.path.dirname(obj.key)):
                os.makedirs(os.path.dirname(obj.key))
            if download_path:
                bucket.download_file(obj.key, download_path)
            else:
                bucket.download_file(obj.key, obj.key)  # save to same path


    @staticmethod
    def read_feature_from_manifest(manifest_file_path, feature_id='measurementFrameSet', tag='coordinates'):
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
                                if sub_sub_elem.tag.endswith(tag):  # oder: if tag in sub_sub_elem.tag:
                                    feature_text = sub_sub_elem.text
                                    break
                                else:
                                    sub_elem = sub_sub_elem
        if tag == 'coordinates':
            coordinates = []  # list of 4 coordinate tuples
            coordinates_list_txt = feature_text.strip(' ').split(' ')

            if len(coordinates_list_txt) == 4:  # Format for S1 coordinates: altitude1,latitude1 alt2,lat2 ...
                for coordinate in coordinates_list_txt:
                    coordinates.append((float(coordinate.split(',')[0]),
                                        float(coordinate.split(',')[1])))
            elif len(coordinates_list_txt) > 4 and len(
                    coordinates_list_txt) % 2 == 0:  # Format for S2 coordinates: altitude1 latitude1 alt2-4 lat2-4 alt1 lat1
                for i_coordinate in range(int(len(coordinates_list_txt) / 2)):
                    coordinate = (
                    float(coordinates_list_txt[i_coordinate * 2]), float(coordinates_list_txt[i_coordinate * 2 + 1]))
                    if not coordinate in coordinates:
                        coordinates.append(coordinate)
            else:
                raise ValueError('Coordinates from feature text could not be interpreted.')

            return coordinates
        else:
            return feature_text

    def download_manifest(self, product_id, target_file=None):
        if not target_file:
            target_file = r'manifest.safe'
        manifest_file = product_id.lstrip('codede').lstrip('CODEDE').strip('//') + r'/manifest.safe'

        with open(target_file, 'wb') as data:
            self.aws_client.download_fileobj('CODEDE', manifest_file, data)
            print(f'The target file has been downloaded: {target_file} ')

    #     def filter_for_aoi(self, product_id_list, upper_left:tuple, lower_right:tuple, crs:str):
    def filter_for_aoi(self, product_id_list, aoi: BBox):

        filtered_products = list()
        temp_file = 'manifest_temp.safe'

        for product_id in product_id_list:
            self.download_manifest(product_id, temp_file)

            scene_boundings = self.read_feature_from_manifest(temp_file, 'measurementFrameSet', 'coordinates')
            remove_file(temp_file)
            scene_crs = 'epsg:4263'  # !!!  change to:
            #             scene_geometry, scene_crs = self.get_footprint_from_manifest(product_id)
            #             transform scene geometry to iterable list of coordinates, like scene_geometry
            #             Transform the given geometry to the scene crs

            transformer = Transformer.from_crs(crs_from=str(aoi.crs), crs_to=str(scene_crs))
            for coordinate in [aoi.lower_left, aoi.upper_right]:
                if not point_in_bounding_box(scene_boundings, transformer.transform(coordinate[0], coordinate[1])):
                    continue
                if not product_id in filtered_products:
                    filtered_products.append(product_id)

        return filtered_products


class Sentinel2Client(SentinelIOClient):
    def __init__(self, access_key, secret_key):
        super().__init__(access_key, secret_key)

    def get_data_file_keys(self, collection: str, date: str, tile_id: str, resolution: str, bands: list,
                           max_directory_depth=5):
        prefix = collection + date + '/'
        i = 0
        data_keys = []
        while i < max_directory_depth and data_keys == []:  # Schleife durch die Ebenen
            #             print(prefix)
            try:
                objects = [i for i in
                           self.aws_client.list_objects(Delimiter='/', Bucket='CODEDE', Prefix=prefix, MaxKeys=30000)[
                               'CommonPrefixes']]

            except KeyError:
                try:
                    objects = [i for i in self.aws_client.list_objects(Delimiter='/', Bucket='CODEDE', Prefix=prefix,
                                                                       MaxKeys=30000)['Contents']]
                except KeyError:
                    print(self.aws_client.list_objects(Delimiter='/', Bucket='CODEDE', Prefix=prefix, MaxKeys=30000))
                    raise KeyError('The object does neither feature the key \'CommonPrefixes\' nor \'Contents\'')

            for object_key in objects:  # Schleife durch die Objekte einer Ebene
                try:
                    if tile_id in object_key['Prefix'].split('/')[-2]:  # enter GRANULE data
                        prefix = object_key['Prefix']
                        if not tile_id + '_A0' in object_key['Prefix'].split('/')[-2]:
                            prefix += 'GRANULE/'
                            continue

                    if object_key['Prefix'].endswith('IMG_DATA/'):
                        prefix = object_key['Prefix']
                        continue

                    if object_key['Prefix'].endswith('R' + resolution + '/'):
                        prefix = object_key['Prefix']
                        continue

                except KeyError:
                    try:
                        if object_key['Key'].endswith('.jp2'):
                            if object_key['Key'][-11:-8] in bands or object_key['Key'][
                                                                     -7:-4] in bands:  # assumes ending of key like: ...T103021_B04_10m.jp2
                                data_keys.append(object_key['Key'])

                    except KeyError as err:
                        print(f"The object does neither feature the key \"Prefix\" nor \"Key\":")
                        print(object_key)
            i += 1

        print(f"{len(data_keys)} elements have been found")
        for key in data_keys:
            print(key)
        return data_keys

    def download_band_data(self, target_files: list, download_files: list):
        if len(target_files) != len(download_files):
            raise ValueError('The file lists have to be the same length.')

        for i_file in range(len(target_files)):
            with open(target_files[i_file], 'wb') as data:
                self.aws_client.download_fileobj('CODEDE', download_files[i_file], data)


class Sentinel1Client(SentinelIOClient):
    def __init__(self, access_key, secret_key):
        super().__init__(access_key, secret_key)

    def get_data_file_keys(self, collection: str, date: str, mission_id: str, scan_mode: str, product_type: str,
                           resolution: str, polarisation_class: str, check_for_relative_orbit=None,
                           processing_level='1', product_class='S', aoi=None, max_directory_depth=5):

        if collection.startswith('codede/'):
            collection = collection.lstrip('codede/')

        prefix = collection + date + '/'
        product_title_elements = ['Mission ID', 'Scan Mode', 'Produkt Typ', 'Resolution', 'Processing Level',
                                  'Product Class', 'Polarisation Class', 'Date']
        product_title_list = [mission_id + '_', scan_mode + '_', product_type, resolution + '_', processing_level,
                              product_class, polarisation_class + '_', date.replace('/', '')]
        product_title = prefix
        i_product_err = 0

        i = 0
        data_keys = []

        while i < max_directory_depth and data_keys == []:  # Schleife durch die Ebenen

            objects = [i for i in
                       self.aws_client.list_objects(Delimiter='/', Bucket='CODEDE', Prefix=prefix, MaxKeys=30000)[
                           'CommonPrefixes']]

            for object_key in objects:  # Schleife durch die Objekte eines Datums
                err = None

                product_title = prefix
                for i_product in range(len(product_title_list)):  # Schleife durch die Elemente des Produkttitels
                    product_title += product_title_list[i_product]

                    if not object_key['Prefix'].startswith(product_title):
                        i_product_err = max(i_product, i_product_err)
                        err = f"No data could be found under the given {product_title_elements[i_product_err]}: {product_title_list[i_product_err].rstrip('_')}"
                        break

                    if check_for_relative_orbit:
                        abs_orbit_nr = int(
                            object_key['Prefix'].split('_')[-3])  # check whether the orbit number matches the date
                        if not self._is_in_relative_orbit(abs_orbit_nr, int(check_for_relative_orbit), mission_id):
                            err = f"No data could be found for the given relative orbit number ({check_for_relative_orbit}) on the {date}."
                            break

                    if not err and i_product == len(product_title_list) - 1:
                        data_keys.append(object_key['Prefix'])

            if data_keys == []:
                print(err)
                break

            i += 1  # Ende der while-Schleife, neue Ebene im Data-file-Path

        print(f"{len(data_keys)} elements have been found")
        for i_key in range(len(data_keys)):
            data_keys[i_key] = BUCKET + '/' + data_keys[i_key]

            print(data_keys[i_key])

        if type(aoi) == BBox:
            filtered_keys = self.filter_for_aoi(data_keys, aoi)
            return filtered_keys
        else:
            return data_keys

    @staticmethod
    def _is_in_relative_orbit(abs_orbit_nr: int, relative_orbit_nr: int, mission_id: str):

        if mission_id == 'S1A':
            def _in_orbit(abs_orbit_nr, relative_orbit_nr):
                return relative_orbit_nr == (abs_orbit_nr - 73) % 175 + 1
        elif mission_id == 'S1B':
            def _in_orbit(abs_orbit_nr, relative_orbit_nr):
                return relative_orbit_nr == (abs_orbit_nr - 27) % 175 + 1
        else:
            raise ValueError('The mission ID is restricted to either \'S1A\' or \'S1B\'.')

        return _in_orbit(abs_orbit_nr, relative_orbit_nr)

    def download_grd_data(self, product_id: str, polarisation: str, target_directory='',
                          target_files_list=None):  # Polarisation vv, vh , hh oder hv, auch v und h für beide polarisierung

        data_keys = list()

        data_key = product_id.lstrip('CODEDE/').lstrip('codede/').rstrip('/') + r'/measurement'
        data_directory = [i for i in
                          self.aws_client.list_objects(Delimiter='/', Bucket='CODEDE', Prefix=data_key, MaxKeys=30000)[
                              'CommonPrefixes']][0]['Prefix']
        data_files = [i for i in self.aws_client.list_objects(Delimiter='/', Bucket='CODEDE', Prefix=data_directory,
                                                              MaxKeys=30000)['Contents']]

        for data_file in data_files:
            if search(r'(?<=-)' + polarisation, data_file['Key'].split('/')[-1]):
                data_keys.append(data_file['Key'])

        if target_files_list:
            if not len(target_files_list) == len(data_keys):
                raise ValueError(f'The target files has to be of the same length as the data keys')
        else:
            target_files_list = [(target_directory + '/' + data_keys[i].split('/')[-1]).lstrip('/') for i in
                                 range(len(data_keys))]

        for i_key in range(len(data_keys)):
            print(data_keys[i_key])
            with open(target_files_list[i_key], 'wb') as data:
                self.aws_client.download_fileobj('CODEDE', data_keys[i_key], data)

        print(f'The target files have been downloaded: {target_files_list}')
        return target_files_list
