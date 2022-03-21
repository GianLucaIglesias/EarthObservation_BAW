from Pegel_IO import PegelIO, PegelStation
from DataPlot import plot_pegel
from datetime import datetime
from http_api_utils import get_date_time_from_iso_timestamp

# Search Settings
point_coordinate = (6.7, 49.5)  # coordinate(longitude, latitude)
start = datetime(year=2021, month=3, day=2)
end = datetime(year=2022, month=3, day=12)
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # #   PEGEL - DEMO - SECTION
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Schreibweise für die vergangenen letzen Tage
# start = 'P15D'  # P15D, P6DT10H15M
# start = 'P40DT0H0M'

# # Initialisation of client
# pegel_io = PegelIO(nutzer='florianlindenberger', passwort='BlauesBand3000!')

# pegel_io.find_station_along_river('Rhein')
# pegel_io.find_station_around_coordinates(longitude=point_coordinate[0], latitude=coordinate[1],
#                                           radius=20, show=True)

# pegel_io.show_accessible_time_series()

# # Get Pegel Station from client
# pegel_speyer = pegel_io.load_station('SPEYER')

# alternatively just initialize pegel object without loading metadata from pegelonline
pegel_speyer = PegelStation('SPEYER')
# #online ressources Section
# pegel_io.load_measurement(['Speyer', 'Mainz', 'Emmerich'], start=start, end=None, measurement='pegel')
# pegel_io.plot_pegel(['Speyer', 'Mainz', 'Emmerich'])
# pegel_speyer = pegel_io.get_pegel_station('Speyer')
# discharge_speyer = pegel_speyer.get_discharge('speyer')
# print(discharge_speyer)
# print(type(discharge_speyer))

# # Discharge section
discharge_archive = r"C:\Users\gian_\Desktop\Q_O_m³_s_23700600_2016_03_14_2022_03_18.zip"
pegel_speyer.load_timeseries_from_zip(discharge_archive, start=start, end=end)
# plot_pegel([pegel_speyer], measure='discharge')
max_discharge = pegel_speyer.get_maximum_discharge()

# # Waterlevel Section
# waterlevel_archive = r"C:\Users\gian_\Downloads\W_O_cm_23700600_2016_03_01_2018_03_17.zip" #doesn't work with r"C:\Users\gian_\Downloads\W_O_cm_23700600_2021_09_18_2022_03_18.zip"
# pegel_speyer.load_timeseries_from_zip(waterlevel_archive, start=start, end=end)
# plot_pegel([pegel_speyer], measure='waterlevel')
# max_waterlevel = pegel_speyer.get_maximum_water_level()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # #    Finder - API - DEMO
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
from Sentinel_IO import SentinelIOClient

# access CODE-DE S3 endpoint
access_key = 'SMAETRKMLRHWZBEIELIB'
secret_key = 'HNgfzFKqfLGzKnNxCNuhfLBVopmEUHSxMpGeXXLr'

upper_left = (8.41330, 49.34067)
bottom_right = (8.50788, 49.26702)
monsterloch_coordinates = (upper_left, bottom_right)

# convert max_discharge in python datetime format
days_tolerance = 2
api_start, api_end = get_date_time_from_iso_timestamp(max_discharge['timestamp'], days_tolerance=days_tolerance)

finder_client = SentinelIOClient(access_key, secret_key)
finder_client.find(collection='S2', processing_level=1, start_date=api_start, completion_date=api_end,
                   aoi=point_coordinate, show_list=True)

# # Parameter definition
# date = '2021/09/21'
# window_identifier = '_T32UMV'
# resolution = '10m'
# bands = ['B02', 'B03', 'B04']




