import requests
import re
import wget
from os import path as os_path
from datetime import datetime, timedelta
from datetime import date as date_typ


## Project: iAI   Author: aimuch   File: yolov3_to_onnx.py    License: MIT License
def download_file(local_path, link):
    """Checks if a local file is present and downloads it from the specified path otherwise.
    If checksum_reference is specified, the file's md5 checksum is compared against the
    expected value.

    Keyword arguments:
    local_path -- path of the file whose checksum shall be generated
    link -- link where the file shall be downloaded from if it is not found locally
    """
    if not os_path.exists(local_path):
        print(f"Downloading from {link} to {local_path}..")
        wget.download(link, local_path) # wget --http-user="ihr_login" --http-password="ihr_passwort" --no-check-certificate "https://pegelonline.wsv.de/webservices/nutzer/files/testdatei.txt"
        return local_path

    else:
        print(f"File not downloaded. The target already exists: {local_path}")
        return


def make_url_request(url: str):
    """
    Function performing an url request. Returns the requests response.
    :param url: http address from which the information will be requested.
    :type url: str
    """
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        raise ConnectionError('There is no connection to the api server. Please check your internet '
                              'connection.')

    if not response.ok:
        try:
            error = dict_from_response_text(response.text)['message']
        except KeyError:
            error = "The URL response was not ok. No error message could be delivered. "
        raise ValueError(error)
    return response


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


def append_directory(url, dir_names):
    if type(dir_names) == str:
        dir_names = [dir_names]

    for dir in dir_names:
        url = url.rstrip('/') + r'/' + dir
    return url


def append_aoi(url, lower_left, upper_right):
    aoi_str = url.strip('&') + '&geometry=POLYGON(('

    coordinates = [(lower_left[0], lower_left[1]), (lower_left[0], upper_right[1]), (upper_right[0], upper_right[1]),
                   (upper_right[0], lower_left[1])]
    for i in range(len(coordinates)):
        aoi_str += str(coordinates[i][0]) + '+' + str(coordinates[i][1]) + '%2C'
    aoi_str += str(coordinates[0][0]) + '+' + str(coordinates[0][1]) + '))'
    return aoi_str

# https://finder.code-de.org/resto/api/collections/Sentinel1/search.json?maxRecords=10&location=all&productType=GRD&processingLevel=LEVEL1&sensorMode=IW&sortParam=startDate&sortOrder=descending&status=all&geometry=POINT(8.570969624999998+49.42216920772617)&dataset=ESA-DATASET
def append_point(url, lon, lat):
    aoi_str = url.strip('&') + '&geometry=POINT('
    aoi_str += str(lon) + '+' + str(lat) + ')'
    return aoi_str


def append_search_parameter(url, search_params):
    if type(search_params) == tuple:
        search_params = [search_params]

    for param in search_params:
        url = url.rstrip('/&') + r'&' + param[0] + '=' + param[1]
    return url


def append_timestamp(start=None, end=None, base_url='', measurement_interval=None, api='pegel'):
    """
    Function parsing the datetime date indications to a string lateral. Appends the date request to the base_url and
    returns it as a string.

    :param start: start date or iso standard time gauging period
    :type start: datetime
    :param end: date to be included as the end time of a time series
    :type end: datetime
    :param measurement_interval: 5 lateral string in the format <hh:ss>
    :param api: string indicating the api for which the time stamp is appended in a request: either 'pegel' or 'code-de'
    :type api: str
    :param base_url: url to which the time stamp is appended to. By default this is an empty string.
    :type base_url: str

    """
    if api == 'pegel':
        param_keys = ['start', 'end']
        standard_format = 'yyyy-mm-ddThh:mm+hh:mm'
        measurement_interval = '01:00'
        iso_standard_periods = ['P8D', 'P15D']
    elif api == 'code-de':
        param_keys = ['startDate', 'completionDate']
        standard_format = 'yyyy-mm-ddT0hh:mm:ssZ'
    else:
        raise ValueError('api either has to indicate \'pegel\' or \'code-de\'')

    dates_list = [start, end]

    for i_dates in range(len(dates_list)):
        date = dates_list[i_dates]
        if start and end and i_dates == 1:
            inquiry_url = inquiry_url + '&' + param_keys[i_dates] + '='
        elif date:
            inquiry_url = base_url + param_keys[i_dates] + '='
        else:
            continue

        if type(date) == date_typ or type(date) == datetime:
# https://finder.code-de.org/resto/api/collections/Sentinel1/search.json?maxRecords=10&startDate=2022-03-02T00%3A00%3A00Z&completionDate=2022-03-14T23%3A59%3A59Z&location=all&productType=GRD&processingLevel=LEVEL1&sensorMode=IW&sortParam=startDate&sortOrder=descending&status=all&geometry=POINT(8.570969624999998+49.42216920772617)&dataset=ESA-DATASET
            if api == 'code-de':
                if type(date) == datetime:
                    date_list = [('year', date.year), ('month', date.month), ('day', date.day)]
                    time_list = [('hour', date.hour), ('minute', date.minute), ('second', date.second)]
                if type(date) == date_typ:
                    date_list = [('year', date.year), ('month', date.month), ('day', date.day)]
                    time_list = [('hour', 0), ('minute', 0), ('second', 0)]
# startDate=2022-03-02T00%3A00%3A00Z
# startDate=2021-03-02T00:00:0Z
            # 'https://finder.code-de.org/resto/api/collections/Sentinel2/search.json?&processingLevel=LEVEL1C&startDate=2021-3-2:0:0:0Z&completionDate=2022-3-12:0:0:0Z&geometry=POINT(6.7+49.5)'
                for i_date in range(len(date_list)):
                    if date_list[i_date]:
                        if not i_date == 0:
                            inquiry_url += '-'
                        inquiry_url += str(date_list[i_date][1]).zfill(2)
                    else:
                        raise ValueError(f'The date requires the statement of a {date_list[i_date][0]} ')

                for i_time in range(len(time_list)):
                    if i_time == 0:
                        inquiry_url += 'T'
                    else:
                        inquiry_url += '%3A'
                    if time_list[i_time]:
                        time_str = str(time_list[i_time][1]).zfill(2)
                    else:
                        time_str = '00'
                    inquiry_url += time_str
                inquiry_url += 'Z'

            elif api == 'pegel':
                inquiry_url += date.isoformat() + '+' + measurement_interval

        elif type(date) == str:
            # general format check
            if len(date.split('-')) == 3:
                if len(date.split('T')) == 1:
                    if api == 'pegel':
                        date += 'T00:00:00+' + measurement_interval
            elif date in iso_standard_periods:
                pass
            elif api == 'pegel' and (date[0] == 'P' and (date[-1] in 'M', 'H', 'D')):
                pass  # P10D5H20M - Format
            else:
                raise ValueError(f'A time stamp has to follow iso RFC-3339 standard: '
                                 f'api = {api} -> {standard_format}, {param_keys[i_dates]} = {dates_list[i_dates]} was '
                                 f'given.')

            inquiry_url = inquiry_url + date

        else:
            inquiry_url = base_url

    return inquiry_url


def get_date_time_from_iso_timestamp(ts, days_tolerance=0):
    date_time = date_typ.fromisoformat(ts[:10])
    if days_tolerance > 0:
        end = date_time + timedelta(days=days_tolerance)
        start = date_time - timedelta(days=days_tolerance)
    else:
        start, end = date_time, None
    return start, end
