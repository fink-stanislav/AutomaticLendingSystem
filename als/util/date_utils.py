
import numpy as np
import datetime as dt

global date_time_format
date_time_format = '%Y-%m-%d %H:%M:%S'

def date_to_ts(date):
    return int((date - dt.datetime(1970, 1, 1)).total_seconds())

def np_date_to_ts(date):
    return int((date - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's'))
