import requests
import pandas as pd
from zipfile import ZipFile

from http_api_utils import make_url_request, append_timestamp
from DataPlot import plot_pegel

BASE_URL = r"https://www.pegelonline.wsv.de/webservices/rest-api/v2"
USER_URL = r"https://username:password@www.pegelonline.wsv.de/webservices/nutzer/rest-api/v2"


def _is_iso_format(ts):
    if type(ts) == str:
        if len(ts) == 19 and len(ts.split('T')) == 2 and len(ts.split(':')) == 3 and len(ts.split('-')) == 3:
            return True

    return False


def get_iso_timestamp(raw_ts):
    return raw_ts[:4] + '-' + raw_ts[4:6] + '-' + raw_ts[6:8] + 'T' + raw_ts[8:10] + ':' + raw_ts[10:12] + ':' + raw_ts[12:14]


def load_dataframe_from_zip_archive(archive_path):
    if not archive_path.endswith('.zip'):
        raise ValueError("Archive is expected to be a .zip-archive")

    abo_name = archive_path.split('\\')[-1][:-4]
    data_file = abo_name + ".dat"
    print(f"Reading {data_file}")

    with ZipFile(archive_path, 'r') as zip:
        data_file_str = zip.read(data_file).decode()

    data_file_lines = data_file_str.split('\r\n')
    c_name = data_file_lines[1].split('|CNAME')[1][0]
    unit = data_file_lines[1].split('*')[3].lstrip('|CUNIT')[:-1]
    if c_name == 'Q':
        measurement = 'discharge'
        unit
    elif c_name == 'W':
        measurement = 'waterlevel'
    else:
        print(f"An unknown measurement type CNAME{c_name} can't be read.")
        exit()

    timestamps, values = list(), list()
    for line in data_file_lines[3:-1]:
        timestamps.append(get_iso_timestamp(line.split(' ')[0]))
        values.append(line.split(' ')[1])

    if measurement == 'discharge':
        df = pd.DataFrame({'timestamp': timestamps, f"Abfluss [{unit}]": values})
    elif measurement == 'waterlevel':
        df = pd.DataFrame({'timestamp': timestamps, f"Wasserstand [{unit}]": values})
    return df, measurement


def _load_dataframe_from_url(url):
    """
    Set a pegel inquiry for the given period in time. Returns pandas dataframe with the measured water levels.
    :param url: either datetime or timestamp string lateral in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
    the start date of the pegel time series
    :type url: str
    """
    try:
        json_resp = make_url_request(url).json()
    except ValueError as err:
        raise ValueError(err)
    if type(json_resp) == list:
        df = pd.DataFrame(json_resp)
    elif type(json_resp) == dict:
        df = pd.DataFrame(json_resp, index=[0])
    else:
        raise ValueError(f"An unexpected json response was received from {url}. The data could not be converted "
                         f"into a pandas dataframe.")
    return df


class PegelIO:
    def __init__(self, nutzer=None, passwort=None):
        self.URL_BASE = BASE_URL.replace('nutzer/', '')
        self.user = nutzer
        if nutzer and passwort:
            self.USER_URL = USER_URL.replace('username', nutzer).replace('password', passwort)
        else:
            self.USER_URL = BASE_URL
            print('No user was set. Data may only be accessible within the last 30 days.')
        self.stations = []

    def fetch_station(self, station_name):
        for station in self.stations:
            if station_name.upper() == station.station_name:
                return station
        print(f'{station_name} has not been loaded yet.')
        return None

    def load_station(self, station, is_id_number=False):
        """
        Function loading the gauging station supplied by the PegelOnline Service . When given station name was
        found in the list, the meta information is found.
        :param station: either station id number (xxxxxxx) or short name of gauging station as string.
        :param is_id_number: tag whether the given station parameter indicates a number or not
        :type is_id_number: bool
        """
        station_list = requests.get(self.URL_BASE + '/stations.json').json()
        if is_id_number:
            id_key = 'number'
            id_station = str(station)
        else:
            id_key = 'shortname'
            id_station = station.upper()

        for pegel_station in station_list:
            if pegel_station[id_key].startswith(id_station):
                print(f"Pegel {pegel_station[id_key]} has been loaded.")
                      # f"Number: {pegel_station['number']}, Longname: {pegel_station['longname']}, uuid: {pegel_station['uuid']}")

                station_obj = PegelStation(station_name=pegel_station['shortname'],
                                           station_number=str(pegel_station['number']),
                                           coordinate=(pegel_station['longitude'], pegel_station['latitude']),
                                           km=pegel_station['km'],
                                           river_name=pegel_station['water']['shortname'],
                                           base_url=self.URL_BASE)

                self.stations.append(station_obj)
                return station_obj

        raise ValueError(f'The given gauge ({station}) is not listed in the pegelonline web services. Have a look for '
                         f'all available gauges at: https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json')

    def find_station_around_coordinates(self, latitude, longitude, radius, show=True):
        """
        Looks for gauging station in a certain radius [km] from a geografic location.
        :param latitude: latitude of location of interest
        :type latitude: float
        :param longitude: longitude of location of interest
        :type longitude: float
        """
        url = self.URL_BASE + r'/stations.json?latitude=' + str(latitude) + r'&longitude=' +str(longitude) + '&radius=' + \
              str(radius)
        response = make_url_request(url)

        if type(response.json()) == list:
            stations_list = response.json()
        print(f"{len(stations_list)} gauging stations were found in the given radius.")

        if show:
            for i in range(len(stations_list)):
                print(stations_list[i]['shortname'])
        return stations_list

    def find_station_along_river(self, river_name, km=None, radius=None, show=True):
        url = self.URL_BASE + r'/stations.json?waters=' + river_name.upper()
        if km and radius:
            url += '&km=' + str(km) + '&radius=' + str(radius)
        response = make_url_request(url)

        if type(response.json()) == list:
            stations_list = response.json()
        print(f"{len(stations_list)} gauging stations were found along the {river_name} radius.")

        if show:
            for i in range(len(stations_list)):
                print(stations_list[i]['shortname'])
        return stations_list

    def load_measurement(self, station_names, start=None, end=None, measurement='all'):
        if type(station_names) == str:
            if station_names == 'all':
                station_names = [s.station_name for s in self.stations]
            else:
                station_names = [station_names]

        for station_name in station_names:
            station = self.fetch_station(station_name)
            if not station:
                station = self.load_station(station_name)

            if measurement == 'pegel' or measurement == 'all':
                station.load_waterlevel_measurement(start=start, end=end)

            if measurement == 'current' or measurement == 'all' or measurement == 'discharge':
                station.load_discharge_measurement(start=start, end=end)
            print(f'Measurements loaded for {station_name}.')

    def show_accessible_time_series(self):
        if self.USER_URL == BASE_URL:
            print("No user was set. No Times Series can be plotted.")
            return
        url = self.USER_URL + r'/stations.json?includeTimeseries=true'
        df = _load_dataframe_from_url(url)
        print(f"{len(df)} time series have been found for user {self.user}:")
        for i in range(len(df)):
            station_name = df['shortname'][i]
            print(f"{station_name}".ljust(22), end='')
            for j in range(len(df['timeseries'][i])):
                time_series_type = df['timeseries'][i][j]['longname']
                start_time = df['timeseries'][i][j]['start']
                end_time = df['timeseries'][i][j]['end']
                if j > 0:
                    print(f" ".ljust(22), end='')  # Platzhalter
                print(f"{time_series_type}".ljust(21), end='')
                print(f"from:  {start_time[:9]} - {end_time[:9]}")
            print("")

    def get_pegel_station(self, station_name):
        station = self.fetch_station(station_name)
        return station

    def get_discharge(self, station_name):
        station = self.fetch_station(station_name)
        return station.discharge

    def plot_pegel(self, stations='all'):
        if stations == 'all':
            plot_pegel_list = self.stations
        else:
            plot_pegel_list = [self.fetch_station(name) for name in stations]
        plot_pegel(plot_pegel_list)


class PegelStation:
    def __init__(self, station_name, station_number=None, coordinate=(None, None), km=None, river_name=None, base_url=BASE_URL):
        self.station_name = station_name.upper()
        self.station_number = station_number
        self.longitude, self.latitude = coordinate
        self.km = km
        self.river_name = river_name

        self.waterlevel = None
        self.waterlevel_png = None  # pd.DataFrame(columns=['timestamp','measurement'])
        self.discharge = None
        self.discharge_png = None

        self._url_base = base_url

    def get_waterlevel(self):
        return self.waterlevel

    def get_maximum_water_level(self):
        col_name = self.waterlevel.columns[1]
        max_waterlevel = self.waterlevel[col_name].max()
        max_df = self.waterlevel.loc[self.waterlevel[col_name] == max_waterlevel]
        print(f"{len(max_df)} maximal discharges have been found.")
        print(max_df)
        return max_df

    def get_maximum_discharge(self):
        col_name = self.discharge.columns[1]
        max_discharge = self.discharge[col_name].max()
        max_df = self.discharge.loc[self.discharge[col_name] == max_discharge]
        print(f"{len(max_df)} maximal discharges have been found.")
        print(max_df)
        return max_df

    def get_discharge(self):

        return self.discharge

    def load_discharge_measurement(self, start=None, end=None):
        """
        Set a discharge measurement inquiry for the given period in time. Returns pandas dataframe with the measured
        water levels.
        :param start: either timestamp as datetime type or timestamp string lateral in the format
        'yyyy-mm-ddThh:mm+hh:mm' or iso time period (e.g. 'P15D'), indicating the start date of the pegel time series
        :param end: either datetime or timestamp string later in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the end date of the pegel time series
        """
        url = self._url_base + '/stations/' + self.station_name + r'/W/currentmeasurement.json'
        url = append_timestamp(start, end, base_url=url+'?', api='pegel')
        df = _load_dataframe_from_url(url)
        self.discharge = df.rename({'value': 'Abfluss [m^3/s]'}, axis=1)
        return self.discharge

    def load_waterlevel_measurement(self, start=None, end=None, png=False):
        """
        Set a pegel inquiry (measurement) for the given period in time. Returns pandas dataframe with the measured water levels.

        :param start: either datetime or timestamp string lateral in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the start date of the pegel time series
        :param end: either datetime or timestamp string later in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the end date of the pegel time series
        """
        url = self._url_base + '/stations/' + self.station_name + r'/W/measurements.json'
        url = append_timestamp(start, end, base_url=url+'?', api='pegel')
        df = _load_dataframe_from_url(url)
        self.waterlevel = df.rename({'value': 'Wasserstand [m ü.NN]'}, axis=1)
        return self.waterlevel

    def load_timeseries_from_zip(self, archive_path, start=None, end=None, png=False):
        """
        Set a pegel inquiry (measurement) for the given period in time. Returns pandas dataframe with the measured water levels.

        :param start: either datetime or timestamp string lateral in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the start date of the pegel time series
        :param end: either datetime or timestamp string later in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the end date of the pegel time series
        """
        try:
            df, measurement = load_dataframe_from_zip_archive(archive_path)
        except ValueError as err:
            print(f"Could not load time series for {self.station_name} because of error: \n{err}")
            exit(0)

        if _is_iso_format(start):
            if start[-8:] == "00:00:00":
                start = start[:-5] + "15:00"
            start_idx = df.loc[df['timestamp'] == start].index[0]
        else:
            start_idx = 0

        if _is_iso_format(end):
            if end[-8:] == "00:00:00":
                end = end[:-5] + "15:00"
            end_idx = df.loc[df['timestamp'] == end].index[0]
        else:
            end_idx = len(df)

        if measurement == 'waterlevel':
            print(f"Waterlevels have been loaded for pegel {self.station_name}.")
            self.waterlevel = df.iloc[start_idx:end_idx-1]
        elif measurement == 'discharge':
            print(f"Discharge measurements have been loaded for pegel {self.station_name}.")
            self.discharge = df.iloc[start_idx:end_idx - 1]
        else:
            print("Measurements could not be loaded from df due to unknown measurement type.")
