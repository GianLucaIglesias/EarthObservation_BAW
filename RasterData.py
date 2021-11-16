import rasterio
import fiona
import matplotlib.pyplot as pyplot
import rasterio.plot as rplot
import rasterio.mask
import re
import xml.etree.ElementTree as ET

from pathlib import Path
from datetime import datetime
from os.path import splitext
from pyproj import Proj, transform
from sentinelhub.geometry import BBox, CRS, Geometry
from shapely.geometry.polygon import Polygon


def get_time_stamp_from_filename(file_name):
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


def get_footprint_from_manifest(product_id, feature_id='measurementFrameSet'):
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


class RasterData:
    def __init__(self):
        self.meta = dict()
        self.shapes = None

    def get_window(self, upper_left: tuple, bottom_right: tuple, reference_crs='epsg:4326'):
        print('Transforming window...')
        in_proj = Proj(reference_crs)
        out_proj = Proj('epsg:32632')
        x_up, y_up = transform(in_proj, out_proj, upper_left[0], upper_left[1])
        x_bottom, y_bottom = transform(in_proj, out_proj, bottom_right[0], bottom_right[1])

        return rasterio.windows.from_bounds(left=x_up, bottom=y_bottom, right=x_bottom, top=y_up,
                                            transform=self.meta['transform'])

    def update_meta_data(self, width, height, transform, dtypes, crs):
        if self.meta == dict():
            self.meta.update({"width": width,
                              "height": height,
                              "transform": transform,
                              "dtypes": dtypes,
                              "crs": crs})
        else:
            for meta_info in ['transform', 'crs', 'width', 'height']:
                if not self.meta[meta_info] == self.__getattribute__(meta_info):
                    raise ValueError(f"Can't load the data due to differing {meta_info} meta information.")


class S1_RasterData(RasterData):
    def __init__(self):
        super().__init__()
        self.amplitudes = None

        self.vv_arr = None
        self.vh_arr = None
        self.hh_arr = None
        self.hv_arr = None

    def transform_window(self, upper_left: tuple, bottom_right: tuple, reference_crs='epsg:4326'):
        new_window = self.get_window(upper_left, bottom_right, reference_crs)
        return new_window

        for polarisation in ['vv', 'vh', 'hh', 'hv']:
            self.__setattr__(polarisation + '_arr', getattr(self, ...).read(1)) # Methode um die arrays zu clippen

    def load_from_tiff(self, file_path):
        for polarisation in ['vv', 'vh', 'hh', 'hv']:
            if re.search(r'(?<=-)'+polarisation, file_path):
                # polarisation = re.search(r'(?<=-)'+polarisation, file_path).group(0)
                amplitude_data = rasterio.open(file_path, driver='Gtiff')
                self.__setattr__(polarisation + '_arr', amplitude_data.read(1))

                self.update_meta_data(amplitude_data.width, amplitude_data.height, amplitude_data.transform,
                                      amplitude_data.dtypes, amplitude_data.crs)
        return self


class S2_RasterData(RasterData):
    def __init__(self):
        super().__init__()
        self.B02 = None
        self.B03 = None
        self.B04 = None
        self.src = None

        self.B02_arr = None
        self.B03_arr = None
        self.B04_arr = None

        self.cloud_mask = None

    def transform_window(self, upper_left: tuple, bottom_right: tuple, reference_crs='epsg:4326'):
        window = self.get_window(upper_left, bottom_right, reference_crs)

        if self.B04:
            # self.B02_arr = self.B02.read(1, window=window)
            # self.B03_arr = self.B03.read(1, window=window)
            self.B04_arr = self.B04.read(1, window=window)

        elif self.src:
            # self.B02_arr = self.src.read(3, window=window)
            # self.B03_arr = self.src.read(2, window=window)
            self.B04_arr = self.src.read(1, window=window)
        else:
            raise ValueError('No input data has been read.')

        self.meta.update({"window": window,
                          "width": self.B02_arr.shape[1],
                          "height": self.B02_arr.shape[0]})

    def load_bands(self, file_list):
        # data_obj = cls()

        for i_file in range(len(file_list)):
            file_name, file_extension = splitext(file_list[i_file])
            if file_extension == '.jp2':
                driver = "JP2OpenJPEG"
            else:
                raise ValueError(f"{file_list[i_file]} does not feature a supported format.")

            band = rasterio.open(file_list[i_file], driver=driver)
            file_key = file_name.split('\\')[-1]

            if re.search(r'(?<=_)B\d\d', file_key):
                band_name = re.search(r'(?<=_)B\d\d', file_key).group(0)
            elif re.search(r'(?<=_)B\d', file_key):
                band_str = re.search(r'(?<=_)B\d', file_key).group(0)
                band_name = band_str[:1] + '0' + band_str[1:]  # insert 0 for consistent 2 digit band naming: BXX
            else:
                raise ValueError("The given file list does not contain consistent band naming (keys must feature "
                                 "consistent band naming: either \"_BX\" or \"_BXX\").")

            self.__setattr__(band_name, band)
            self.__setattr__(band_name + '_arr', getattr(self, band_name).read(1))

            self.update_meta_data(band.width, band.height, band.transform, band.dtypes, band.crs)

        return self

    def load_from_tiff(self, file_path):
        file_name, file_extension = splitext(file_path)
        if file_extension == '.tif' or file_extension == '.tiff':
            driver = "GTiff"
        else:
            raise ValueError(f"{file_path} does not feature a supported format.")

        band = rasterio.open(file_path, driver=driver)
        file_key = file_name.split('\\')[-1]

        if re.search(r'(?<=_)B\d\d', file_key):
            band_name = re.search(r'(?<=_)B\d\d', file_key).group(0)
        elif re.search(r'(?<=_)B\d', file_key):
            band_str = re.search(r'(?<=_)B\d', file_key).group(0)
            band_name = band_str[:1] + '0' + band_str[1:]  # insert 0 for consistent 2 digit band naming: BXX
        else:
            raise ValueError("The given file list does not contain consistent band naming (keys must feature "
                             "consistent band naming: either \"_BX\" or \"_BXX\").")

        self.__setattr__(band_name, band)
        self.__setattr__(band_name + '_arr', getattr(self, band_name).read(1))

        self.update_meta_data(band.width, band.height, band.transform, band.dtypes, band.crs)
        return self

    def load_true_color_data(self, file_name):  # noch nicht getestet!
        file_path = file_name + '.tiff'

        with rasterio.open(file_path) as src:
            self.meta.update({"width": src.width,
                              "height": src.height,
                              "transform": src.transform,
                              "dtypes": src.dtypes,
                              "crs": src.crs})

            self.B02_arr = src.read(1, window=self.window)
            self.B03_arr = src.read(2, window=self.window)
            self.B04_arr = src.read(3, window=self.window)

    def clip_to_shape(self, shp_file, show=False):
        with fiona.open(shp_file, "r") as shp:
            self.shapes = [feature["geometry"] for feature in shp]

        if self.src:
            out_img, out_transform = rasterio.mask.mask(self.src, self.shapes, crop=True)
        else:
            raise ValueError(r'No data source available for clipping.')

        self.meta.update({"width": out_img.shape[2],
                          "height": out_img.shape[1],
                          "transform": out_transform})

    def get_cloud_probability(self, mask_file, show=False, cmap='blues', prb_threshold=50):
        with rasterio.open(mask_file) as mask:
            cloud_prb_arr = mask.read(1, window=self.window)

        cld_probability = cloud_prb_arr[cloud_prb_arr > prb_threshold].shape[0] / (cloud_prb_arr.shape[0] *
                                                                                   cloud_prb_arr.shape[1])
        if show:
            rplot.show(self.cloud_mask, transform=self.meta['transform'], cmap=cmap)
        return round(cld_probability, 2)

    def true_color_img(self, file_name, show=True, cmap='Greys'):
        file_path = file_name + '.tiff'
        with rasterio.open(file_path, 'w', driver='Gtiff',
                           width=self.meta['width'], height=self.meta['height'],
                           count=3, crs=self.meta['crs'], transform=self.meta['transform'],
                           dtype=self.meta['dtypes'][0]) as true_color_img:
            print('Creating .tiff-file...')
            true_color_img.write(self.B04_arr, 1)  # red
            true_color_img.write(self.B03_arr, 2)  # green
            true_color_img.write(self.B02_arr, 3)  # blue

        if show:
            print('Reading .tiff-file for plotting...')
            fig = pyplot.figure()
            src = rasterio.open(file_path)
            rplot.show(src, transform=self.meta['transform'], cmap=cmap)
