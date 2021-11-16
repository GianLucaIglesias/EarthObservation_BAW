# from tomography_tutorial import start
#
# start(r'/TomoSAR_tutorial.ipynb')

# from pathlib import Path
# from Sentinel_IO import SentinelIOClient
from RasterData import S1_RasterData, get_time_stamp_from_filename
# from EOPatch import DataPatch
# from geometry import point_in_bounding_box
from eolearn.core import FeatureType, EOPatch
from EOPatch_IO import ImportFromTiffTask, ImportTimeFeatureFromTiffTask
from sentinelhub.geometry import BBox, CRS
from DataPlot import plot_data_array, true_color_img, show_rgb_from_tiff

from numpy import sqrt

import matplotlib.pyplot as plt

access_key = 'SMAETRKMLRHWZBEIELIB'
secret_key = 'HNgfzFKqfLGzKnNxCNuhfLBVopmEUHSxMpGeXXLr'

product_id_S1 = r"D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE"
product_id_S2 = r"C:\Users\gian_\Desktop\Masterarbeit\CODE-DE\S2B_MSIL2A_20210921T102639_N0301_R108_T32UMV_20210921T133332\S2B_MSIL2A_20210921T102639_N0301_R108_T32UMV_20210921T133332.SAFE"

# client = SentinelIOClient('SMAETRKMLRHWZBEIELIB', 'HNgfzFKqfLGzKnNxCNuhfLBVopmEUHSxMpGeXXLr')
# coordinates = client.read_feature_from_manifest(product_id_S2, 'measurementFrameSet', 'coordinates')
# print(f"Point in bounding box: {point_in_bounding_box(coordinates,[(45, 9.05)])}")
#
# sentinel_1 = S1_RasterData().load_from_tiff(file_path=r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\measurement\s1a-iw-grd-vh-20210927t053448-20210927t053513-039863-04b74d-002.tiff')

file_name = r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\measurement\s1a-iw-grd-vh-20210927t053448-20210927t053513-039863-04b74d-002.tiff'
bigS2_scene = r'C:\Users\gian_\Desktop\Masterarbeit\SENTINEL2A_20210906-103717-884_L2A_T32UMV_C_V1-0\SENTINEL2A_20210906-103717-884_L2A_T32UMV_C_V1-0\SENTINEL2A_20210906-103717-884_L2A_T32UMV_C_V1-0_QKL_ALL.tiff'
cloud_filesystem = r'C:\Users\gian_\Desktop\Masterarbeit\CODE-DE\SENTINEL2B_20210921-103714-671_L2A_T32UMV_C_V1-0\SENTINEL2B_20210921-103714-671_L2A_T32UMV_C_V1-0\DATA\SENTINEL2B_20210921-103714-671_L2A_T32UMV_C_V1-0_PVD_ALL'
cloud_file = 'CLD.tif'

time_stamp = [get_time_stamp_from_filename(file_name)]

monsterloch_bounding_box = BBox([(49.34067, 8.41330), (49.26702, 8.50788)], crs=CRS('4326'))

patch_orig = EOPatch()
patch_orig.set_bbox(monsterloch_bounding_box)

patch_self = EOPatch()
patch_self.set_bbox(monsterloch_bounding_box)



# patch = ImportFromTiffTask(('data', 'amplitudes_vh'), folder=r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\measurement\s1a-iw-grd-vh-20210927t053448-20210927t053513-039863-04b74d-002.tiff').execute(eopatch=patch)
# patch = ImportFromTiffTask(('data', 'amplitudes_vh'), folder=r'C:\Users\gian_\Desktop\Masterarbeit\CODE-DE\L2A_TrueColor_L2A_Monsterloch.tiff').execute(eopatch=patch)

# patch = ImportTimeFeatureFromTiffTask(feature=('data', 'band02'), timestamp=time_stamp).execute(eopatch=patch, file_name=bigS2_scene, time_stamps=time_stamp)
# patch = ImportTimeFeatureFromTiffTask(feature=('data', 'CLD'),
#                                       path=cloud_filesystem,
#                                       timestamp=time_stamp).execute(eopatch=patch,
#                                                                     file_name=r'CLD.tif',
#                                                                     time_stamps=time_stamp)

# patch_self = ImportTimeFeatureFromTiffTask(feature=('data', 'bands'),
#                                       folder=r'C:\Users\gian_\Desktop\Masterarbeit\CODE-DE',
#                                       timestamp=time_stamp).execute(eopatch=patch_self,
#                                                                     file_name='TrueColor_L2A.tiff',
#                                                                     time_stamps=time_stamp)

# patch_orig = ImportFromTiffTask(feature=('data', 'bands'),
#                                 folder=r'C:\Users\gian_\Desktop\Masterarbeit\CODE-DE').execute(eopatch=patch_orig,
#                                                                     filename='TrueColor_L2A.tiff')

patch_self = ImportTimeFeatureFromTiffTask(feature=('data', 'amplitudes_vh'), folder=r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE').\
    execute(eopatch=patch_self,
            file_name=r'measurement\s1a-iw-grd-vh-20210927t053448-20210927t053513-039863-04b74d-002.tiff',
            time_stamps=time_stamp,
            manifest_file=r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\manifest.safe')

# patch = ImportTimeFeatureFromTiffTask(feature=('data', 'amplitudes_vv'), path=r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\measurement').execute(eopatch=patch, file_name=r's1a-iw-grd-vv-20210927t053448-20210927t053513-039863-04b74d-001.tiff', time_stamps=time_stamp)
# weiter machen: fix the coordinate system
# true_color_img(r_band=patch_self.data['bands'][0, :, :, 0],
#                g_band=patch_self.data['bands'][0, :, :, 1],
#                b_band=patch_self.data['bands'][0, :, :, 2],
#                crs=str(patch_self.bbox.crs), transform=patch_self.meta_info['transform'], dtype=patch_self.data['bands'].dtype)

blub = 1




