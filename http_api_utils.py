import requests
import re

from datetime import datetime


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

        # geometry=POLYGON((8.433843920508753+49.33187542041324%2C8.48548511004929+49.33222597490638%2C8.488174755337859+49.30417372646539%2C8.437071494855036+49.30627819935006%2C8.433843920508753+49.33187542041324))
        # geometry=POLYGON((8.405333680449916+49.27470166786608%2C8.404257822334488+49.33853552890449%2C8.497319549318995+49.33853552890449%2C8.497857478376709+49.275403588302424%2C8.405333680449916+49.27470166786608))
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

        if type(date) == datetime:

            if api == 'code-de':
                date_list = [('year', date.year), ('month', date.month), ('day', date.day)]
                time_list = [('hour', date.hour), ('minute', date.minute), ('second', date.second)]

                for i_date in range(len(date_list)):
                    if date_list[i_date]:
                        if not i_date == 0:
                            inquiry_url += '-'
                        inquiry_url += str(date_list[i_date][1])
                    else:
                        raise ValueError(f'The date requires the statement of a {date_list[i_date][0]} ')

                for i_time in range(len(time_list)):
                    if time_list[i_time]:
                        if i_date == 0:
                            inquiry_url += 'T'
                        else:
                            inquiry_url += ':'
                        time_str = str(time_list[i_time][1])
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
