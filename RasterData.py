import rasterio
import fiona
import matplotlib.pyplot as pyplot
import rasterio.plot as rplot
import rasterio.mask
import re

from os.path import splitext
from pyproj import Proj, transform


class S2_RasterData:
    def __init__(self):
        self.band02 = None
        self.band03 = None
        self.band04 = None
        self.src = None

        self.band02_arr = None
        self.band03_arr = None
        self.band04_arr = None

        self.cloud_mask = None

        self.meta = dict()
        self.window = None  # upper left and lower right corner coordinates
        self.shapes = None

    def transform_window(self, upper_left: tuple, bottom_right: tuple, reference_crs='epsg:4326'):
        print('Transforming window...')
        in_proj = Proj(reference_crs)
        out_proj = Proj('epsg:32632')
        x_up, y_up = transform(in_proj, out_proj, upper_left[0], upper_left[1])
        x_bottom, y_bottom = transform(in_proj, out_proj, bottom_right[0], bottom_right[1])

        self.window = rasterio.windows.from_bounds(left=x_up, bottom=y_bottom, right=x_bottom, top=y_up,
                                                   transform=self.meta['transform'])

        if self.band02:
            self.band02_arr = self.band02.read(1, window=self.window)
            self.band03_arr = self.band03.read(1, window=self.window)
            self.band04_arr = self.band04.read(1, window=self.window)

        elif self.src:
            self.band02_arr = self.src.read(3, window=self.window)
            self.band03_arr = self.src.read(2, window=self.window)
            self.band04_arr = self.src.read(1, window=self.window)
        else:
            raise ValueError('No input data has been read.')

        self.meta.update({"width": self.band02_arr.shape[1],
                          "height": self.band02_arr.shape[0]})

    @classmethod
    def load_bands(cls, file_list):
        data_obj = cls()
        bands, band_arrs = list(), list()

        for i_file in range(len(file_list)):
            file_name, file_extension = splitext(file_list[i_file])
            if file_extension == '.jp2':
                driver = "JP2OpenJPEG"
            elif file_extension == '.tif':
                driver = 'Gtiff'
            else:
                raise ValueError(f"{file_list[i_file]} does not feature a supported format.")

            band_data = rasterio.open(file_list[i_file], driver=driver)
            band_name = re.search(r'(?<=_)B\d\d', file_name.split('\\')[-1])

            data_obj.__setattr__(band_name, band_data)
            data_obj.__setattr__(band_name + '_arr', getattr(data_obj, band_name).read(1))

            if i_file == 0 and data_obj.meta == dict():
                data_obj.meta.update({"width": band_data.width,
                                      "height": band_data.height,
                                      "transform": band_data.transform,
                                      "dtype": band_data.dtypes,
                                      "crs": band_data.crs})
            else:
                for meta_info in ['transform', 'crs', 'width', 'height']:
                    if not data_obj.meta[meta_info] == band_data.__getattribute__(meta_info):
                        raise ValueError(f"The {meta_info} meta information of the loaded bands do not match.")
        return data_obj

    def load_true_color_data(self, file_name):  # noch nicht getestet!
        file_path = file_name + '.tiff'

        with rasterio.open(file_path) as src:
            self.meta.update({"width": src.width,
                              "height": src.height,
                              "transform": src.transform,
                              "dtype": src.dtypes,
                              "crs": src.crs})

            self.band02_arr = src.read(1, window=self.window)
            self.band03_arr = src.read(2, window=self.window)
            self.band04_arr = src.read(3, window=self.window)

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
                           dtype=self.meta['dtypes']) as true_color_img:
            print('Creating .tiff-file...')
            true_color_img.write(self.band04_arr, 1)  # red
            true_color_img.write(self.band03_arr, 2)  # green
            true_color_img.write(self.band02_arr, 3)  # blue

        if show:
            print('Reading .tiff-file for plotting...')
            fig = pyplot.figure()
            src = rasterio.open(file_path)
            rplot.show(src, transform=self.meta['transform'], cmap=cmap)
