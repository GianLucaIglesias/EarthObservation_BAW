"""
Module containing tasks used for reading and writing to disk

Credits:
Copyright (c) 2017-2019 Matej Aleksandrov, Matej Batič, Andrej Burja, Eva Erzin (Sinergise)
Copyright (c) 2017-2019 Grega Milčinski, Matic Lubej, Devis Peresutti, Jernej Puc, Tomislav Slijepčević (Sinergise)
Copyright (c) 2017-2019 Blaž Sovdat, Nejc Vesel, Jovan Višnjić, Anže Zupanc, Lojze Žust (Sinergise)
Copyright (c) 2018-2019 William Ouellette (TomTom)
Copyright (c) 2019 Drew Bollinger (DevelopmentSeed)

This source code is licensed under the MIT license found in the LICENSE
file in the root directory of this source tree.
"""
import datetime
import logging
import warnings
from abc import abstractmethod
import dateutil
import fs
import rasterio
import numpy as np
from sentinelhub import CRS, BBox
from pyproj import Proj, transform


from RasterData import get_footprint_from_manifest
from eolearn.core import EOTask, EOPatch
from filesystem_utils import get_base_filesystem_and_path
# from eolearn.core.utilities import renamed_and_deprecated

LOGGER = logging.getLogger(__name__)


def get_distance_point_to_line(A: tuple, B: tuple, P: tuple):
    AB = (B[0] - A[0], B[1] - A[1])
    AP = (P[0] - A[0], P[1] - A[1])
    return abs(AB[0] * AP[1] - AB[1] * AP[0]) / np.sqrt(AB[0] ** 2 + AB[1] ** 2)


def get_window(upper_left: tuple, bottom_right: tuple, crs_transform, ref_crs='epsg:4326', out_crs='epsg:32632'):
    print('Transforming window...')
    in_proj = Proj(ref_crs)
    out_proj = Proj(out_crs)
    x_up, y_up = transform(in_proj, out_proj, upper_left[0], upper_left[1])
    x_bottom, y_bottom = transform(in_proj, out_proj, bottom_right[0], bottom_right[1])

    return rasterio.windows.from_bounds(left=x_up, bottom=y_bottom, right=x_bottom, top=y_up,
                                            transform=crs_transform)


class AddFeatureTask(EOTask):
    """Adds a feature to the given EOPatch.
    """
    def __init__(self, feature):
        """
        :param feature: Feature to be added
        :type feature: (FeatureType, feature_name) or FeatureType
        """
        self.feature_type, self.feature_name = next(self._parse_features(feature)())

    def execute(self, eopatch, data):
        """Returns the EOPatch with added features.

        :param eopatch: input EOPatch
        :type eopatch: EOPatch
        :param data: data to be added to the feature
        :type data: object
        :return: input EOPatch with the specified feature
        :rtype: EOPatch
        """
        if self.feature_name is None:
            eopatch[self.feature_type] = data
        else:
            eopatch[self.feature_type][self.feature_name] = data

        return eopatch


class IOTask(EOTask):
    """ An abstract Input/Output task that can handle a path and a filesystem object
    """
    def __init__(self, path, filesystem=None, create=False, config=None):
        """
        :param path: root path where all EOPatches are saved
        :type path: str
        :param filesystem: An existing filesystem object. If not given it will be initialized according to the EOPatch
            path. If you intend to run this task in multiprocessing mode you shouldn't specify this parameter.
        :type filesystem: fs.base.FS or None
        :param create: If the filesystem path doesn't exist this flag indicates to either create it or raise an error
        :type create: bool
        :param config: A configuration object with AWS credentials. By default is set to None and in this case the
            default configuration will be taken.
        :type config: SHConfig or None
        """
        self.path = path
        self._filesystem = filesystem
        self._create = create
        self.config = config

        self.filesystem_path = '/' if self._filesystem is None else self.path

    @property
    def filesystem(self):
        """ A filesystem property that either initializes a new object or returns an existing one
        """
        if self._filesystem is None:
            return get_filesystem(self.path, create=self._create, config=self.config)

        return self._filesystem

    @abstractmethod
    def execute(self, *eopatches, **kwargs):
        """ Implement execute function
        """
        raise NotImplementedError


class SaveTask(IOTask):
    """ Saves the given EOPatch to a filesystem
    """
    def __init__(self, path, filesystem=None, config=None, **kwargs):
        """
        :param path: root path where all EOPatches are saved
        :type path: str
        :param filesystem: An existing filesystem object. If not given it will be initialized according to the EOPatch
            path. If you intend to run this task in multiprocessing mode you shouldn't specify this parameter.
        :type filesystem: fs.base.FS or None
        :param features: A collection of features types specifying features of which type will be saved. By default
            all features will be saved.
        :type features: an object supported by the :class:`FeatureParser<eolearn.core.utilities.FeatureParser>`
        :param overwrite_permission: A level of permission for overwriting an existing EOPatch
        :type overwrite_permission: OverwritePermission or int
        :param compress_level: A level of data compression and can be specified with an integer from 0 (no compression)
            to 9 (highest compression).
        :type compress_level: int
        :param config: A configuration object with AWS credentials. By default is set to None and in this case the
            default configuration will be taken.
        :type config: SHConfig or None
        """
        self.kwargs = kwargs
        super().__init__(path, filesystem=filesystem, create=True, config=config)

    def execute(self, eopatch, *, eopatch_folder=''):
        """Saves the EOPatch to disk: `folder/eopatch_folder`.

        :param eopatch: EOPatch which will be saved
        :type eopatch: EOPatch
        :param eopatch_folder: name of EOPatch folder containing data
        :type eopatch_folder: str
        :return: The same EOPatch
        :rtype: EOPatch
        """
        path = fs.path.combine(self.filesystem_path, eopatch_folder)

        eopatch.save(path, filesystem=self.filesystem, **self.kwargs)
        return eopatch


class BaseLocalIoTask(EOTask):
    """ Base abstract class for local IO tasks
    """
    def __init__(self, feature, folder=None, *, image_dtype=None, no_data_value=0, config=None):
        """
        :param feature: Feature which will be exported or imported
        :type feature: (FeatureType, str)
        :param folder: A directory containing image files or a folder of an image file
        :type folder: str
        :param image_dtype: Type of data to be exported into tiff image or imported from tiff image
        :type image_dtype: numpy.dtype
        :param no_data_value: Value of undefined pixels
        :type no_data_value: int or float
        :param config: A configuration object containing AWS credentials
        :type config: SHConfig
        """
        self.feature = self._parse_features(feature)
        self.folder = folder
        self.image_dtype = image_dtype
        self.no_data_value = no_data_value
        self.config = config

    def _get_filesystem_and_paths(self, filename, timestamps, create_paths=False):
        """ It takes location parameters from init and execute methods, joins them together, and creates a filesystem
        object and file paths relative to the filesystem object.
        """

        if isinstance(filename, str) or filename is None:
            filesystem, relative_path = get_base_filesystem_and_path(self.folder, filename, config=self.config)
            filename_paths = self._generate_paths(relative_path, timestamps)
        elif isinstance(filename, list):
            filename_paths = []
            for timestamp_index, path in enumerate(filename):
                filesystem, relative_path = get_base_filesystem_and_path(self.folder, path, config=self.config)
                if len(filename) == len(timestamps):
                    filename_paths.append(*self._generate_paths(relative_path, [timestamps[timestamp_index]]))
                elif not timestamps:
                    filename_paths.append(*self._generate_paths(relative_path, timestamps))
                else:
                    raise ValueError('The number of provided timestamps does not match '
                                     'the number of provided filenames.')
        else:
            raise TypeError(f"The 'filename' parameter must either be a list or a string, but {filename} found")

        if create_paths:
            paths_to_create = {fs.path.dirname(filename_path) for filename_path in filename_paths}
            for filename_path in paths_to_create:
                filesystem.makedirs(filename_path, recreate=True)

        return filesystem, filename_paths

    @staticmethod
    def _generate_paths(path_template, timestamps):
        """ Uses a filename path template to create a list of actual filename paths
        """
        if not (path_template.lower().endswith('.tif') or path_template.lower().endswith('.tiff')):
            path_template = f'{path_template}.tif'

        if not timestamps:
            return [path_template]

        if '*' in path_template:
            path_template = path_template.replace('*', '%Y%m%dT%H%M%S')

        if timestamps[0].strftime(path_template) == path_template:
            return [path_template]

        return [timestamp.strftime(path_template) for timestamp in timestamps]

    @abstractmethod
    def execute(self, eopatch, **kwargs):
        """ Execute of a base class is not implemented
        """
        raise NotImplementedError


class ImportFromTiffTask(BaseLocalIoTask):
    """ Task for importing data from a Geo-Tiff file into an EOPatch

    The task can take an existing EOPatch and read the part of Geo-Tiff image, which intersects with its bounding
    box, into a new feature. But if no EOPatch is given it will create a new EOPatch, read entire Geo-Tiff image into a
    feature and set a bounding box of the new EOPatch.

    Note that if Geo-Tiff file is not completely spatially aligned with location of given EOPatch it will try to fit it
    as best as possible. However it will not do any spatial resampling or interpolation on Geo-TIFF data.
    """
    def __init__(self, feature, folder=None, *, timestamp_size=None, **kwargs):
        """
        :param feature: EOPatch feature into which data will be imported
        :type feature: (FeatureType, str)
        :param folder: A directory containing image files or a path of an image file
        :type folder: str
        :param timestamp_size: In case data will be imported into time-dependant feature this parameter can be used to
            specify time dimension. If not specified, time dimension will be the same as size of FeatureType.TIMESTAMP
            feature. If FeatureType.TIMESTAMP does not exist it will be set to 1.
            When converting data into a feature channels of given tiff image should be in order
            T(1)B(1), T(1)B(2), ..., T(1)B(N), T(2)B(1), T(2)B(2), ..., T(2)B(N), ..., ..., T(M)B(N)
            where T and B are the time and band indices.
        :type timestamp_size: int
        :param image_dtype: Type of data of new feature imported from tiff image
        :type image_dtype: numpy.dtype
        :param no_data_value: Values where given Geo-Tiff image does not cover EOPatch
        :type no_data_value: int or float
        :param config: A configuration object containing AWS credentials
        :type config: SHConfig
        """
        super().__init__(feature, folder=folder, **kwargs)

        self.timestamp_size = timestamp_size

    @staticmethod
    def _get_reading_window(width, height, data_bbox, eopatch_bbox):
        """ Calculates a window in pixel coordinates for which data will be read from an image
        """
        if eopatch_bbox.crs is not data_bbox.crs:
            eopatch_bbox = eopatch_bbox.transform(data_bbox.crs)

        # The following will be in the future moved to sentinelhub-py
        data_ul_x, data_lr_y = data_bbox.lower_left
        data_lr_x, data_ul_y = data_bbox.upper_right

        res_x = abs(data_ul_x - data_lr_x) / width
        res_y = abs(data_ul_y - data_lr_y) / height

        ul_x, lr_y = eopatch_bbox.lower_left
        lr_x, ul_y = eopatch_bbox.upper_right

        # If these coordinates wouldn't be rounded here, rasterio.io.DatasetReader.read would round
        # them in the same way
        top = round((data_ul_y - ul_y) / res_y)
        left = round((ul_x - data_ul_x) / res_x)
        bottom = round((data_ul_y - lr_y) / res_y)
        right = round((lr_x - data_ul_x) / res_x)

        return (top, bottom), (left, right)

    @staticmethod
    def _get_reading_window_from_geometry(width, height, gcps: list, data_footprint, eopatch_bbox):
        """ Calculates a window in pixel coordinates from a footprint geometry for which data will be read from an image.
        """
        if eopatch_bbox.crs is not data_footprint.crs:
            eopatch_bbox = eopatch_bbox.transform(data_footprint.crs)

        data_ul_x, data_lr_y = data_footprint.bbox.lower_left
        data_lr_x, data_ul_y = data_footprint.bbox.upper_right

        res_x = abs(data_ul_x - data_lr_x) / width
        res_y = abs(data_ul_y - data_lr_y) / height

        aoi_x_min, aoi_y_min = eopatch_bbox.lower_left
        aoi_x_max, aoi_y_max = eopatch_bbox.upper_right

        if aoi_x_min < data_ul_x or aoi_x_max > data_lr_x or aoi_y_max > data_ul_y or aoi_y_min < data_lr_y:
            raise Warning('The given bounding box is not fully covered by the data boundings.')

        for gcp in gcps[0]:
            if gcp.col == 0 and gcp.row == 0:
                upper_right = (gcp.y, gcp.x)
            # elif gcp.col == 0 and gcp.row == height - 1:
            #     lower_right = (gcp.y, gcp.x)
            elif gcp.col == width - 1 and gcp.row == 0:
                upper_left = (gcp.y, gcp.x)
            elif gcp.col == width-1 and gcp.row == height - 1:
                lower_left = (gcp.y, gcp.x)

# dieser Ansatz nimmt an, dass die aoi leicht  gg den Uhrzeiger rotiert ist
        bottom = round(get_distance_point_to_line(upper_right, upper_left, (aoi_x_min, aoi_y_max)) / res_y)
        top = round(get_distance_point_to_line(upper_right, upper_left, (aoi_x_max, aoi_y_min)) / res_y)
        left = round(get_distance_point_to_line(upper_left, lower_left, (aoi_x_min, aoi_y_min)) / res_x)
        right = round(get_distance_point_to_line(upper_left, lower_left, (aoi_x_max, aoi_y_max)) / res_x)

        return (top, bottom), (left, right)

    def execute(self, eopatch=None, *, filename=None):
        """ Execute method which adds a new feature to the EOPatch

        :param eopatch: input EOPatch or None if a new EOPatch should be created
        :type eopatch: EOPatch or None
        :param filename: filename of tiff file or None if entire path has already been specified in `folder` parameter
            of task initialization.
        :type filename: str, list of str or None
        :return: New EOPatch with added raster layer
        :rtype: EOPatch
        """
        feature_type, feature_name = next(self.feature())
        if eopatch is None:
            eopatch = EOPatch()

        filesystem, filename_paths = self._get_filesystem_and_paths(filename, eopatch.timestamp, create_paths=False)

        with filesystem:
            data = []
            for path in filename_paths:
                with filesystem.openbin(path, 'r') as file_handle:
                    with rasterio.open(file_handle) as src:

                        data_bbox = BBox(src.bounds, CRS(src.crs.to_epsg()))
                        if eopatch.bbox is None:
                            eopatch.bbox = data_bbox

                        read_window = self._get_reading_window(src.width, src.height, data_bbox, eopatch.bbox)

                        data.append(src.read(window=read_window, boundless=True, fill_value=self.no_data_value))

        data = np.concatenate(data, axis=0)

        if self.image_dtype is not None:
            data = data.astype(self.image_dtype)

        if not feature_type.is_spatial():
            data = data.flatten()

        if feature_type.is_timeless():
            data = np.moveaxis(data, 0, -1)
        else:
            channels = data.shape[0]

            times = self.timestamp_size
            if times is None:
                times = len(eopatch.timestamp) if eopatch.timestamp else 1

            if channels % times != 0:
                raise ValueError('Cannot import as a time-dependant feature because the number of tiff image channels '
                                 'is not divisible by the number of timestamps')

            data = data.reshape((times, channels // times) + data.shape[1:])
            data = np.moveaxis(data, 1, -1)

        eopatch[feature_type][feature_name] = data

        return eopatch


class ImportTimeFeatureFromTiffTask(ImportFromTiffTask):
    """ Adds a raster scene to the specified data feature array."""
    def __init__(self, feature, folder=None, **kwargs):
        """
        :param data_feature: Feature to which the data will be added to
        :type data_feature: (FeatureType, str)
        :param filesystem: An existing filesystem object. If not given it will be initialized according to the EOPatch
            path. If you intend to run this task in multiprocessing mode you shouldn't specify this parameter.
        :type filesystem: fs.base.FS or None
        :param features: A collection of features types specifying features of which type will be saved. By default
            all features will be saved.
        :type features: an object supported by the :class:`FeatureParser<eolearn.core.utilities.FeatureParser>`
        :param overwrite_permission: A level of permission for overwriting an existing EOPatch
        :type overwrite_permission: OverwritePermission or int
        :param compress_level: A level of data compression and can be specified with an integer from 0 (no compression)
            to 9 (highest compression).
        :type compress_level: int
        :param config: A configuration object with AWS credentials. By default is set to None and in this case the
            default configuration will be taken.
        :type config: SHConfig or None
        """
        self.kwargs = kwargs
        super().__init__(feature=feature, folder=folder)

    def execute(self, file_name, time_stamps, eopatch=None, manifest_file=None):
        """ Adds another time stamp to the given data feature.

        :param path: Path of an image file (.tiff)
        :type path: str
        :param eopatch: EOPatch which will be saved
        :type eopatch: EOPatch
        :param data_feature: name of EOPatch folder containing data
        :type data_feature: (FeatureType, str)


        :return: The same EOPatch
        :rtype: EOPatch
        """
        feature_type, feature_name = next(self.feature())
        if eopatch is None:
            eopatch = EOPatch()

        filesystem, filename_paths = self._get_filesystem_and_paths(file_name, eopatch.timestamp, create_paths=False)

        with filesystem:
            for path in filename_paths:
                with filesystem.openbin(path, 'r') as file_handle:
                    with rasterio.open(file_handle, driver='Gtiff') as src:
                        if not src.crs:  # as common for GRD Sentinel-1 data
                            if not manifest_file:
                                raise ValueError(f"The given tiff-file {path} (at: {filesystem.root_path})does not "
                                                 f"feature any reference bounding box. Please state a manifest file.")

                            data_footprint = get_footprint_from_manifest(manifest_file.rstrip('manifest.safe')+'\\manifest.safe')


                            # data_bbox = data_footprint.bbox
                            # exploit the array edges from the src.gcps[0][0], so to define the data_bbox
                            data_bbox = BBox(..., src.gcps[1])
                            data_crs = str(src.gcps[1])
                            data_transform = rasterio.transform.from_gcps(src.gcps[0])

                        else:
                            data_bbox = BBox(src.bounds, CRS(src.crs.to_epsg()))
                            data_crs = str(src.crs)
                            data_transform = src.transform

                        if eopatch.bbox is None:
                            eopatch.bbox = data_bbox

                        data_ul_x, data_lr_y = eopatch.bbox.lower_left
                        data_lr_x, data_ul_y = eopatch.bbox.upper_right

                        read_window = get_window((data_lr_x, data_lr_y), (data_ul_x, data_ul_y),
                                                 crs_transform=data_transform,
                                                 ref_crs=str(eopatch.bbox.crs), out_crs=data_crs)

                        eopatch.meta_info['transform'] = data_transform

                        scene_data = src.read(window=read_window, boundless=True, fill_value=self.no_data_value)

        # scene_data = np.concatenate(scene_data, axis=0)

        if self.image_dtype is not None:
            scene_data = scene_data.astype(self.image_dtype)

        if not feature_type.is_spatial():
            scene_data = scene_data.flatten()  # flatten 2d array into one single axis

        if feature_type.is_timeless():
            scene_data = np.moveaxis(scene_data, 0, -1)  # moves the first axis one to the back
        else:
            channels = scene_data.shape[0]

            # times = self.timestamp_size
            # if times is None:
                # times = len(eopatch.timestamp) if eopatch.timestamp else 1
            times = len(time_stamps)
            if times == 0:
                times = len(time_stamps) if time_stamps else 1

            if channels % times != 0:
                raise ValueError('Cannot import as a time-dependant feature because the number of tiff image channels '
                                 'is not divisible by the number of timestamps')

            data = scene_data.reshape((times, channels // times) + scene_data.shape[1:])
            data = np.moveaxis(data, 1, -1)

            eopatch[feature_type][feature_name] = data
            for i in range(times):
                eopatch.timestamp.append(time_stamps[i])

        return eopatch