
import web

import pandas as pd
import numpy as np

from threading import Thread, Event

import datetime as dt

import sys
from urllib2 import URLError

from als.exchange.client.PoloniexLender import PoloniexLenderImpl

urls = (
   '/show_data', 'show_data'
)

db_table_name = 'lending_rate'
time_format = '%Y-%m-%d %H:%M:%S'

class Retriever:
    
    def __init__(self, exchange_name):
        if exchange_name == 'poloniex':
            self.exchange = PoloniexLenderImpl.unauthorized()
    
    def get_data(self):
        data = self.exchange.returnLoanOrders()
        data = data['offers']
        df = pd.DataFrame.from_dict(data, dtype=float)
        weighted = np.average(df.rate, weights=df.amount)
        min_rate = np.min(df.rate)
        max_rate = np.max(df.rate)
        result = {}
        result["weighted_rate"] = weighted
        result["min_rate"] = min_rate
        result["max_rate"] = max_rate
        return result
    
class Saver:
    
    def __init__(self, db_username, db_password, db_name, exchange_name):
        self.db_username = db_username
        self.db_password = db_password
        self.db_name = db_name
        self.exchange_name = exchange_name
    
    def save_data(self, data):
        now = dt.datetime.utcnow()
        now.strftime(time_format)

        db = web.database(dbn='mysql', db=self.db_name, user=self.db_username, pw=self.db_password)
        db.insert(db_table_name,
                  min_rate=data['min_rate'],
                  max_rate=data['max_rate'],
                  weighted_rate=data['weighted_rate'],
                  date_time=now,
                  exchange=self.exchange_name)

class TimerThread(Thread):

    def __init__(self, delay, retriever, saver, event):
        Thread.__init__(self)
        self.delay = delay
        self.stopped = event
        self.retriever = retriever
        self.saver = saver

    def run(self):
        while not self.stopped.wait(self.delay):
            try:
                data = self.retriever.get_data()
                self.saver.save_data(data)
            except URLError as urle:
                print urle
            else: 
                print 'Other exception'

import json

class ExtendedEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, dt.datetime):             
            # If it's a date, convert to a string
            # Replace this with whatever your preferred date format is
            return o.strftime(time_format)  

        # Defer to the superclass method
        return json.JSONEncoder(self, o)

def parse_argv():
    required_args = ['-dbu', '-dbp', '-dbn', '-d', '-en']
    
    args = sys.argv[2:]
    args_dict = {}
    for arg in args:
        if arg in required_args:
            a = arg
            args_dict[a] = ''
        else:
            args_dict[a] = arg

    assert len(args_dict) == len(required_args)
    return args_dict

# TODO: add exchange param
class show_data:
    def GET(self):
        args_dict = parse_argv()
        db_name = args_dict['-dbn']
        db_password = args_dict['-dbp']
        db_username = args_dict['-dbu']
        db = web.database(dbn='mysql', db=db_name, user=db_username, pw=db_password)
        results = db.select(db_table_name, limit=100)
        
        dicts = {}
        for result in results:
            date_time = result['date_time']
            date_time = date_time.strftime(time_format)
            del result['date_time']
            dicts[date_time] = result
        
        json_string = json.dumps(dicts)
        return json_string

if __name__ == "__main__":
    args_dict = parse_argv()
    db_name = args_dict['-dbn']
    db_password = args_dict['-dbp']
    db_username = args_dict['-dbu']
    delay = int(args_dict['-d'])
    exchange_name = args_dict['-en']

    r = Retriever(exchange_name)
    s = Saver(db_username, db_password, db_name, exchange_name)

    TimerThread(delay, r, s, Event()).start()
   
    app = web.application(urls, globals())
    app.run()
