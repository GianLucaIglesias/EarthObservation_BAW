import requests
import pandas as pd
import re

from http_api_utils import make_url_request, append_timestamp
from DataPlot import plot_pegel

BASE_URL = r"https://www.pegelonline.wsv.de/webservices/rest-api/v2"
USER_URL = r"https://username:password@www.pegelonline.wsv.de/webservices/nutzer/rest-api/v2"

class PegelIO:
    def __init__(self, nutzer=None, passwort=None):
        self.URL_BASE = BASE_URL.replace('nutzer/', '')

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
                                           river_name=pegel_station['water']['shortname'])

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
                station.waterlevel = station.load_pegel_for_station(self.USER_URL, start=start, end=end)

            if measurement == 'current' or measurement == 'all' or measurement == 'discharge':
                station.discharge = station.load_discharge_for_station(self.USER_URL, start=start, end=end)
            print(f'Measurements loaded for {station_name}.')

    def get_pegel(self, station_name):
        station = self.fetch_station(station_name)
        return station.waterlevel

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
    def __init__(self, station_name, station_number, coordinate, km, river_name):
        self.station_name = station_name
        self.station_number = station_number
        self.longitude, self.latitude = coordinate
        self.km = km
        self.river_name = river_name

        self.waterlevel = None
        self.waterlevel_png = None  # pd.DataFrame(columns=['timestamp','measurement'])
        self.discharge = None
        self.discharge_png = None

    @staticmethod
    def _load_measurement_from_url(url):
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

    def load_discharge_for_station(self, url_base, start=None, end=None):
        """
        Set a discharge measurement inquiry for the given period in time. Returns pandas dataframe with the measured
        water levels.
        :param start: either timestamp as datetime type or timestamp string lateral in the format
        'yyyy-mm-ddThh:mm+hh:mm' or iso time period (e.g. 'P15D'), indicating the start date of the pegel time series
        :param end: either datetime or timestamp string later in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the end date of the pegel time series
        """
        url = url_base + '/stations/' + self.station_name + r'/W/currentmeasurement.json'
        url = append_timestamp(start, end, base_url=url+'?', api='pegel')

        df = self._load_measurement_from_url(url)
        return df.rename({'value': 'Abfluss [m^3]'}, axis=1)

    def load_pegel_for_station(self, url_base, start=None, end=None, png=False):
        """
        Set a pegel inquiry (measurement) for the given period in time. Returns pandas dataframe with the measured water levels.

        :param start: either datetime or timestamp string lateral in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the start date of the pegel time series
        :param end: either datetime or timestamp string later in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the end date of the pegel time series
        """
        url = url_base + '/stations/' + self.station_name + r'/W/measurements.json'
        url = append_timestamp(start, end, base_url=url+'?', api='pegel')
        df = self._load_measurement_from_url(url)
        return df.rename({'value': 'Wasserstand [m ü.NN]'}, axis=1)
