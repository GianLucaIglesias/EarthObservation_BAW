import requests
import pandas as pd
import re

from http_api_utils import dict_from_response_text, make_url_request, append_timestamp

URL_BASE = r"https://www.pegelonline.wsv.de/webservices/rest-api/v2"
TEST_URL = URL_BASE + r'/stations.json'


class PegelIO:
    def __init__(self, station=None, station_nr=None):
        make_url_request(TEST_URL)

        if station_nr:
            self.station_name, self.station_nr, coordinates, self.river, self.km = self.load_station(station_nr,
                                                                                                     number=True)
        elif station:
            self.station_name, self.station_nr, coordinates, self.river, self.km = self.load_station(station,
                                                                                                     number=False)
        else:
            self.station_name, self.station_nr, coordinates, self.river, self.km = None, None, (None, None), None, None

        self.longitude, self.latitude = coordinates
        self.measurements = None
        self.measurements_png = None  # pd.DataFrame(columns=['timestamp','measurement'])
        self.current_measurement = None
        self.current_measurement_png = None

    @staticmethod
    def load_station(station, number=False):
        """
        Function loading the gauging station supplied by the PegelOnline Service . When given station name was
        found in the list, the meta information is found.
        :param station: either station id number (xxxxxxx) or short name of gauging station as string.
        :param number: tag whether the given station parameter indicates a number or not
        :type number: bool
        """
        station_list = requests.get(URL_BASE + '/stations.json').json()
        if number:
            id_key = 'number'
            id_station = str(number)
        else:
            id_key = 'shortname'
            id_station = station.upper()

        for pegel_station in station_list:
            if pegel_station[id_key].startswith(id_station):
                print(f"Pegel for {pegel_station[id_key]} has been found. "
                      f"Number: {pegel_station['number']}, Longname: {pegel_station['longname']}, uuid: {pegel_station['uuid']}")

                station_name = pegel_station['shortname']
                station_number = str(pegel_station['number'])
                coordinates = (pegel_station['longitude'], pegel_station['latitude'])
                km = pegel_station['km']
                river_name = pegel_station['water']['shortname']

                return station_name, station_number, coordinates, river_name, km

        raise ValueError(f'The given gauge ({station}) is not listed in the pegelonline web services. Have a look for '
                         f'all available gauges at: https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json')

    @staticmethod
    def find_station_around_coordinates(latitude, longitude, radius, show=False):
        """
        Looks for gauging station in a certain radius [km] from a geografic location.
        :param latitude: latitude of location of interest
        :type latitude: float
        :param longitude: longitude of location of interest
        :type longitude: float
        """
        url = URL_BASE + r'/stations.json?latitude=' + str(latitude) + r'&longitude=' +str(longitude) + '&radius=' + \
              str(radius)
        response = make_url_request(url)

        if type(response.json()) == list:
            stations_list = response.json()
        print(f"{len(stations_list)} gauging stations were found in the given radius.")

        if show:
            for i in range(len(stations_list)):
                print(stations_list[i]['shortname'])
        return stations_list

    @staticmethod
    def find_station_along_river(river_name, km=None, radius=None, show=False):
        url = URL_BASE + r'/stations.json?waters=' + river_name.upper()
        if km and radius:
            url += '&km='+ str(km) + '&radius=' + str(radius)
        response = make_url_request(url)

        if type(response.json()) == list:
            stations_list = response.json()
        print(f"{len(stations_list)} gauging stations were found along the {river_name} radius.")

        if show:
            for i in range(len(stations_list)):
                print(stations_list[i]['shortname'])
        return stations_list

    @staticmethod
    def _load_measurement_from_url(url):
        """
        Set a pegel inquiry for the given period in time. Returns pandas dataframe with the measured water levels.

        :param url: either datetime or timestamp string lateral in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the start date of the pegel time series
        :type url: str
        """
        json_resp = make_url_request(url).json()
        if type(json_resp) == list:
            df = pd.DataFrame(json_resp)
        elif type(json_resp) == dict:
            df = pd.DataFrame(json_resp, index=[0])
        else:
            raise ValueError(f"An unexpected json response was received from {url}. The data could not be converted "
                             f"into a pandas dataframe.")
        return df

    def load_current_for_station(self, start=None, end=None):
        """
        Set a current measurement inquiry for the given period in time. Returns pandas dataframe with the measured
        water levels.
        :param start: either timestamp as datetime type or timestamp string lateral in the format
        'yyyy-mm-ddThh:mm+hh:mm' or iso time period (e.g. 'P15D'), indicating the start date of the pegel time series
        :param end: either datetime or timestamp string later in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the end date of the pegel time series
        """
        url = URL_BASE + '/stations/' + self.station_name + r'/W/currentmeasurement.json'
        url = append_timestamp(start, end, base_url=url+'?', api='pegel')

        df = self._load_measurement_from_url(url)
        self.current_measurement = df.rename({'value': 'Wasserstand [m ü.NN]'}, axis=1)

        return self.current_measurement

    def load_pegel_for_station(self, start=None, end=None, png=False):
        """
        Set a pegel inquiry (measurement) for the given period in time. Returns pandas dataframe with the measured water levels.

        :param start: either datetime or timestamp string lateral in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the start date of the pegel time series
        :param end: either datetime or timestamp string later in the format 'yyyy-mm-ddThh:mm+hh:mm', indicating
        the end date of the pegel time series
        """
        url = URL_BASE + '/stations/' + self.station_name + r'/W/measurements.json'
        url = append_timestamp(start, end, base_url=url+'?', api='pegel')
        df = self._load_measurement_from_url(url)
        self.measurements = df.rename({'value': 'Wasserstand [m ü.NN]'}, axis=1)
        return self.measurements
