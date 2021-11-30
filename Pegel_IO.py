import requests
import pandas as pd
import re

from datetime import datetime


URL_BASE = r"https://www.pegelonline.wsv.de/webservices/rest-api/v2"
TEST_URL = URL_BASE + r'/stations.json'


def make_url_request(url: str):
    """
    Function performing an url request. Returns the requests response.
    :param url: http address from which the information will be requested.
    :type url: str
    """


    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        raise ConnectionError('There is no connection to the pegelonline server. Please check your internet '
                              'connection.')

    if not response.ok:
        error = dict_from_response_text(response.text)['message']
        raise ValueError(error)
    return response


def append_timestamp(start=None, end=None, base_url='', measurement_interval='01:00'):
    """
    Function parsing the datetime date indications to a string lateral. Appends the date request to the base_url and
    returns it as a string.

    :param start: start date or iso standard time gauging period
    :type start: datetime
    :param end: date to be included as the end time of a time series
    :type end: datetime
    :param measurement_interval: 5 lateral string in the format <hh:ss>
    """
    if type(start) == datetime and type(end) == datetime:
        inquiry_url = base_url + '?start'
        if start:
            inquiry_url = inquiry_url + start.year + '-' + start.month + '-' + start.day + 'T' + start.hour + ':' \
                          + start.minute + ':' + start.second + '+' + measurement_interval

        if end:
            inquiry_url = inquiry_url.rstrip('&end=') + '&end=' + end.year + '-' + end.month + '-' + end.day + 'T' + \
                          end.hour + ':' + end.minute + ':' + end.second + '+' + measurement_interval

    elif type(start) == str:
        inquiry_url = base_url + '?start=' + start
        if type(end) == str:
            inquiry_url += '&end=' + end
    elif not start and not end:
        inquiry_url = base_url
    else:
        raise ValueError(f"start and end are expected to follow the same format. Type(start): {type(start)} and "
                         f"type(end): {type(end)} were given.")
    return inquiry_url


def dict_from_response_text(response_text:str):
    pattern = r'(?<=\").+?(?=\")'
    parameter_list = re.findall(pattern, response_text)

    response_dict = dict()
    i = 0
    while i < len(parameter_list):
        if parameter_list[i].strip(':'):
            key = parameter_list[i].strip(':').strip(',')
            i += 1
            while i < len(parameter_list):
                if parameter_list[i].strip(':'):
                    value = parameter_list[i].strip(':').strip(',')
                    break
                i+=1
        i+=1
        response_dict[key] = value
    return response_dict


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
            self.station_name, self.station_nr, coordinates, self.river, self.km = None, None, (None,None), None, None

        self.longitude, self.latitude = coordinates
        self.measurements = None
        self.measurements_png = None# pd.DataFrame(columns=['timestamp','measurement'])
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
                print(f"Pegel for {pegel_station[id_key]} has been found.")

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
        url = append_timestamp(start, end, base_url=url)

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
        url = append_timestamp(start, end, base_url=url)
        df = self._load_measurement_from_url(url)
        self.measurements = df.rename({'value': 'Wasserstand [m ü.NN]'}, axis=1)
        return self.measurements
