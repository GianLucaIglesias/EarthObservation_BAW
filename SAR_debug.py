from sentinel_io_utils import get_time_stamp_from_filename
from eolearn.core import EOPatch, FeatureType
from EOPatch_IO import ImportTimeFeatureFromTiffTask
from sentinelhub.geometry import BBox, CRS

from DataPlot import plot_data_array, true_color_img, compare_tiff_files

# from numpy import sqrt

# import matplotlib.pyplot as plt

# import otbApplication as otb
#
# print("Available applications : ")
# print(str(otb.Registry.GetAvailableApplications()))
#
# SAR_folder = r"D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\measurement"
#
# time_stamp = get_time_stamp_from_filename(SAR_folder)
# upper_left = (49.34067, 8.41330)
# bottom_right = (49.26702, 8.50788)
# monsterloch = BBox([upper_left, bottom_right], crs=CRS('4263'))
#
# feature_name = 'vv_amplitudes'
#
# patch = EOPatch()
# patch.set_bbox(monsterloch)
# patch = ImportTimeFeatureFromTiffTask(data_feature=feature_name, folder=SAR_folder).execute(file_name=r"s1a-iw-grd-vv-20210927t053448-20210927t053513-039863-04b74d-001.tiff",
#                                                                                  time_stamps=[time_stamp],
#                                                                                  manifest_file=r"..\manifest.safe",
#                                                                                  eopatch=patch)
#
#
# print(f"The patch data is of size: {patch.data[feature_name].shape}")
#
# plot_data_array(patch.data[feature_name][0, :, :, 0], save=r'sar_test_tif.tiff', crs=str(patch.bbox.crs),
#                 transform=patch.meta_info['transform'], dtype=patch.data[feature_name].dtype)





# PEGEL - SECTION

from Pegel_IO import PegelIO
from DataPlot import plot_pegel

pegel = PegelIO('speyer')
# pegel_speyer = pegel.load_pegel_for_station(start='2021-12-13T09:15:00+01:00', end="2021-12-18T08:15:00+01:00")

# pegel_speyer = pegel.load_pegel_for_station(start='P8D')
# current_speyer = pegel.load_current_for_station(start='P15D')

# gauging_station = pegel.find_station_around_coordinates(longitude=13.57, latitude=52.44, radius=20, show=True)
# gauging_stations_rhein = pegel.find_station_along_river('saale', show=True)

# plot_pegel(pegel_speyer, save=False)














# access_key = 'SMAETRKMLRHWZBEIELIB'
# secret_key = 'HNgfzFKqfLGzKnNxCNuhfLBVopmEUHSxMpGeXXLr'
#
# product_id_S1 = r"D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE"
# product_id_S2 = r"C:\Users\gian_\Desktop\Masterarbeit\CODE-DE\S2B_MSIL2A_20210921T102639_N0301_R108_T32UMV_20210921T133332\S2B_MSIL2A_20210921T102639_N0301_R108_T32UMV_20210921T133332.SAFE"

# client = SentinelIOClient('SMAETRKMLRHWZBEIELIB', 'HNgfzFKqfLGzKnNxCNuhfLBVopmEUHSxMpGeXXLr')
# coordinates = client.read_feature_from_manifest(product_id_S2, 'measurementFrameSet', 'coordinates')
# print(f"Point in bounding box: {point_in_bounding_box(coordinates,[(45, 9.05)])}")

# sentinel_1 = S1_RasterData().load_from_tiff(file_path=r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\measurement\s1a-iw-grd-vh-20210927t053448-20210927t053513-039863-04b74d-002.tiff')

file_name = r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\measurement\s1a-iw-grd-vh-20210927t053448-20210927t053513-039863-04b74d-002.tiff'
bigS2_scene = r'C:\Users\gian_\Desktop\Masterarbeit\SENTINEL2A_20210906-103717-884_L2A_T32UMV_C_V1-0\SENTINEL2A_20210906-103717-884_L2A_T32UMV_C_V1-0\SENTINEL2A_20210906-103717-884_L2A_T32UMV_C_V1-0_QKL_ALL.tiff'
cloud_filesystem = r'C:\Users\gian_\Desktop\Masterarbeit\CODE-DE\SENTINEL2B_20210921-103714-671_L2A_T32UMV_C_V1-0\SENTINEL2B_20210921-103714-671_L2A_T32UMV_C_V1-0\DATA\SENTINEL2B_20210921-103714-671_L2A_T32UMV_C_V1-0_PVD_ALL'
cloud_file = r'CLD.tif'

#
# app = otb.Registry.CreateApplication("Smoothing")

# speckle = r"D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\measurement\s1a-iw-grd-vv-20210927t053448-20210927t053513-039863-04b74d-001.tiff"
# de_speckle = r"C:/Users/gian_/Desktop/Despeckle_s1a-iw-grd-vv-20210927t053448-20210927t053513-039863-04b74d-001.tif".replace('/', '\\')
#
# compare_tiff_files([speckle, de_speckle], ['Speckle', 'Despeckle'])



# time_stamp = [get_time_stamp_from_filename(file_name)]
#
# monsterloch_bounding_box = BBox([(49.34067, 8.41330), (49.26702, 8.50788)], crs=CRS('4326'))
#
# patch_orig = EOPatch()
# patch_orig.set_bbox(monsterloch_bounding_box)
#
# patch_self = EOPatch()
# patch_self.set_bbox(monsterloch_bounding_box)
#


# patch = ImportFromTiffTask(('data', 'amplitudes_vh'), folder=r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\measurement\s1a-iw-grd-vh-20210927t053448-20210927t053513-039863-04b74d-002.tiff').execute(eopatch=patch)
# patch = ImportFromTiffTask(('data', 'amplitudes_vh'), folder=r'C:\Users\gian_\Desktop\Masterarbeit\CODE-DE\L2A_TrueColor_L2A_Monsterloch.tiff').execute(eopatch=patch)

# patch = ImportTimeFeatureFromTiffTask(feature=('data', 'band02'), timestamp=time_stamp).execute(eopatch=patch, file_name=bigS2_scene, time_stamps=time_stamp)
# patch_self = ImportTimeFeatureFromTiffTask(feature=('data', 'CLD'),
#                                       folder=cloud_filesystem,
#                                       timestamp=time_stamp).execute(eopatch=patch_self,
#                                                                     file_name=r'CLD.tif',
#                                                                     time_stamps=time_stamp)

# patch_self = ImportTimeFeatureFromTiffTask(feature=('data', 'bands'),
#                                            folder=r'C:\Users\gian_\Desktop\Masterarbeit\CODE-DE',
#                                            timestamp=time_stamp).execute(eopatch=patch_self,
#                                                                     file_name='TrueColor_L2A.tiff',
#                                                                     time_stamps=time_stamp)
#
# true_color_img(r_band=patch_self.data['bands'][0, :, :, 0],
#                g_band=patch_self.data['bands'][0, :, :, 1],
#                b_band=patch_self.data['bands'][0, :, :, 2],
#                crs=str(patch_self.bbox.crs), transform=patch_self.meta_info['transform'], dtype=patch_self.data['bands'].dtype)


# patch_orig = ImportFromTiffTask(feature=('data', 'bands'),
#                                 folder=r'C:\Users\gian_\Desktop\Masterarbeit\CODE-DE').execute(eopatch=patch_orig,
#                                                                     filename='TrueColor_L2A.tiff')

# patch_self = ImportTimeFeatureFromTiffTask(feature=('data', 'amplitudes_vh'), folder=r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE').\
#     execute(eopatch=patch_self,
#             file_name=r'measurement\s1a-iw-grd-vh-20210927t053448-20210927t053513-039863-04b74d-002.tiff',
#             time_stamps=time_stamp,
#             manifest_file=r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\manifest.safe')

# patch = ImportTimeFeatureFromTiffTask(feature=('data', 'amplitudes_vv'), path=r'D:\SAR\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B\S1A_IW_GRDH_1SDV_20210927T053448_20210927T053513_039863_04B74D_943B.SAFE\measurement').execute(eopatch=patch, file_name=r's1a-iw-grd-vv-20210927t053448-20210927t053513-039863-04b74d-001.tiff', time_stamps=time_stamp)

# plot_data_array(patch_self.data['amplitudes_vh'][0, :, :, 0])
