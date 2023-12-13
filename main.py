import polars as ps
from datetime import datetime, timedelta, time
import pytz
from pytz import timezone

import variables



morning_commute = {'Monday': [], 'Tuesday':[], 'Wednesday':[], 'Thursday':[], 'Friday':[]}
morning_averages = {'Monday': None, 'Tuesday': None, 'Wednesday' : None, 'Thursday': None, 'Friday': None}

afternoon_commute = {'Monday': [], 'Tuesday':[], 'Wednesday':[], 'Thursday':[], 'Friday':[]}
afternoon_averages = {'Monday': None, 'Tuesday': None, 'Wednesday' : None, 'Thursday': None, 'Friday': None}


def calculate_date_average(storage, average):

    fake_sum = 0
    for times, time_values in storage.items():
        for val in time_values:
            fake_sum += sum(val.values())
        average[times] = fake_sum/(len(time_values)*60)
        fake_sum = 0


def convert_to_datetime_object(date_string):
    datetime_object = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S +0000')
    return datetime_object


def convert_to_central_time(date_time):
    central = timezone('US/Central')
    utc = pytz.utc
    cleaned_date = convert_to_datetime_object(date_time)
    utc_conversion = utc.localize(cleaned_date)
    central_conversion = utc_conversion.astimezone(central)
    return central_conversion.time()


def day_check(date_time):
    current_day_datetime_object = convert_to_datetime_object(variables.current_day)
    checking_date_object = convert_to_datetime_object(date_time)
    checking_date = datetime(checking_date_object.year, checking_date_object.month, checking_date_object.day)
    if checking_date > current_day_datetime_object:
        reset()


def reset():
    variables.start_time = None
    variables.end_time = None
    variables.end_location = None
    variables.end_search_time = None


def add_to_list(time_difference):
    if variables.end_location == 'work':
        morning_commute[variables.start_time.strftime('%A')].append({variables.start_time.strftime('%c'): time_difference})
    if variables.end_location == 'home':
        afternoon_commute[variables.start_time.strftime('%A')].append({variables.start_time.strftime('%c'): time_difference})
    reset()


def time_difference(time_1, time_2):
    diff = time_1 - time_2
    return diff.total_seconds()
    

def check_start_or_end(current_location, time_stamp):
    if time.hour < 20 and current_location == 'home' or current_location == 'UST':
        variables.current_day = variables.start_time = time
        variables.end_search_time = time_stamp + timedelta(hours=2)
        variables.end_location = 'work'

    if time.hour > 20 and current_location == 'work':
        variables.end_location = 'home'
        variables.end_search_time = variables.start_time + timedelta(hours=2)


def search_for_end_location(current_location, time_stamp):
    if variables.end_location == current_location and time <= variables.end_search_time:
        variables.end_time = time_stamp
        diff = time_difference(variables.end_time, variables.start_time)
        add_to_list(diff)


def latitude_and_longitude_variance(latitude, longitude, timestamp):
    for location in variables.locations_map:
        location_latitude = variables.locations_map[location][0]
        location_longitude = variables.locations_map[location][1]
        variance = .0010
        if (location_latitude - variance) <= latitude <= (location_latitude + variance) \
            and (location_longitude - variance) <= longitude <= (location_longitude + variance):
            time_stamp = convert_to_datetime_object(timestamp)
            day_check(timestamp)
            if variables.start_time is None:
                check_start_or_end(location, time_stamp)
            search_for_end_location(location, time_stamp)


def run_spreadsheet():
    gps_data = r'New.csv'
    gps_sheet = ps.read_csv(gps_data, separator = ';')
    latitude_and_longitude_df = gps_sheet.select(ps.col('latitude', 'longitude', 'timestamp'))
    for time in latitude_and_longitude_df.rows():
        latitdue = time[0]
        longitude = time[1]
        timestamp = time[2]
        latitude_and_longitude_variance(latitdue, longitude, timestamp)   


if __name__ == '__main__':
    run_spreadsheet()
    calculate_date_average(morning_commute, morning_averages)
    calculate_date_average(afternoon_commute, afternoon_averages)
