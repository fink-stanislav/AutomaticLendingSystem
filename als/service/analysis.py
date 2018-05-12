
import web
import math
import datetime as dt
import pandas as pd
import numpy as np

from als.exchange.client.poloniex_lender import PoloniexLenderImpl
from als.exchange import keys

import als.util.date_utils as du

from als.util import custom_config as cc, custom_logging

logger = custom_logging.get_logger('als.core')

class Analyzer:

    def __init__(self):
        
        exchange_name = cc.get_exchange_name()
        exchange_api_key = keys.get_api_key(name=exchange_name)
        exchange_secret = keys.get_secret(name=exchange_name)
        db_engine = cc.get_db_engine()
        db_name = cc.get_db_name()
        db_username = cc.get_db_username()
        db_password = cc.get_db_password()
        user_id = 1

        self.exchange_name = exchange_name
        if exchange_name == 'polo':
            self.exchange = PoloniexLenderImpl.authorized(exchange_api_key, exchange_secret)
            self.min_loan = 0.01
        self.db = web.database(dbn=db_engine, db=db_name, user=db_username, pw=db_password)
        self.user_id = user_id

        self._adjusted_loans = {}
        self._latest_rate = 0.0

    def adjust_loans(self):
        on_offers = self.exchange.returnOpenLoanOffers()
        if 'BTC' in on_offers:
            on_offers = on_offers['BTC']
        else:
            on_offers = []

        on_orders = self.exchange.returnActiveLoans()

        availables = self.exchange.returnBalances()

        total = 0.0
        available = 0.0
        for on_order in on_orders:
            total += float(on_order['amount'])

        for on_offer in on_offers:
            total += float(on_offer['amount'])
            available += float(on_offer['amount'])

        if 'BTC' in availables:
            total += float(availables['BTC'])
            available += float(availables['BTC'])

        possible_loans = math.floor(available / self.min_loan)
        loan_size = 0
        if possible_loans > 0:
            #loan_size = available / possible_loans
            #loan_size = float(format(loan_size, '.8f'))
            loan_size = self.min_loan

        result = {}
        result['total'] = total
        result['loan_size'] = loan_size
        result['possible_loans'] = possible_loans
        return result

    def past_loans_metadata(self):
        end_ts = du.date_to_ts(dt.datetime.utcnow())
        start_ts = end_ts - 3600 * 24 * 30
        latest_loans = self.exchange.returnLendingHistory(start_ts, end_ts)
        df = pd.DataFrame.from_dict(latest_loans)
        df = df[df['currency'] == 'BTC']
        df = df.head(10)
        avg_duration = df['duration'].astype('float').mean() * 86400
        avg_rate = df['rate'].astype('float').mean()
        
        latest = df.head(1)
        close_of_latest = latest['close']
        close_of_latest = close_of_latest.get_values()[0]
        
        result = {}
        result['avg_duration'] = avg_duration
        result['avg_rate'] = avg_rate
        result['close_of_latest'] = close_of_latest
        
        return result

    def running_loans_metadata(self):
        active_loans = self.exchange.returnActiveLoans()
        if active_loans:
            df = pd.DataFrame.from_dict(active_loans)
            df['date'] = pd.to_datetime(df['date'])
            latest = df.sort_values(['date'], ascending=True).tail(1)
            latest_ts = du.np_date_to_ts(latest['date'].get_values()[0])

            avg_rate = latest.mean()
            avg_rate = avg_rate['rate']
            
            result = {}
            result['latest_ts'] = latest_ts
            result['avg_rate'] = avg_rate
            
            return result
            
        return None

    def latest_rate(self):
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
    
    def store_latest_rate(self, data):
        now = dt.datetime.utcnow()
        now.strftime(du.date_time_format)

        self.db.insert(cc.get_lending_rate_table_name(),
                  min_rate=data['min_rate'],
                  max_rate=data['max_rate'],
                  weighted_rate=data['weighted_rate'],
                  date_time=now,
                  exchange=self.exchange_name)

    def evaluate_state(self, adjusted):
        self._adjusted_loans = adjusted
        possible_loans = adjusted['possible_loans']
        if possible_loans < 1.0:
            possible_loans = 0.0

        total_possible_loans = math.floor(adjusted['total'] / self.min_loan)
        placing_index = float(possible_loans) / total_possible_loans 

        past_loans_metadata = self.past_loans_metadata()
        avg_duration = past_loans_metadata['avg_duration']
        avg_time_between_loans = avg_duration / total_possible_loans
        now_ts = du.date_to_ts(dt.datetime.utcnow())
        running_loans_metadata = self.running_loans_metadata()
        duration_index = 0.0
        if running_loans_metadata:
            duration_index = (now_ts - running_loans_metadata['latest_ts']) / avg_time_between_loans
            avg_rate = running_loans_metadata['avg_rate']
        else:
            close_of_latest_ts = du.date_to_ts(dt.datetime.strptime(past_loans_metadata['close_of_latest'], du.date_time_format))
            duration_index = (now_ts - close_of_latest_ts) / avg_time_between_loans
            avg_rate = past_loans_metadata['avg_rate']

        latest_rate = self.latest_rate()
        weighted_rate = latest_rate['weighted_rate']
        self._latest_rate = weighted_rate
        rate_index = weighted_rate / avg_rate

        self.db.insert(cc.get_lending_market_state_table_name(),
                  duration_index=duration_index,
                  rate_index=rate_index,
                  placing_index=placing_index,
                  date_time=dt.datetime.utcfromtimestamp(now_ts),
                  exchange_name=self.exchange_name, 
                  user_id=self.user_id)
        self.store_latest_rate(latest_rate)
        
        # add other data if needed
        return {'avg_time_between_loans': avg_time_between_loans}


    def ema(self, time_series, column_name, new_column_name, window):
        ema = time_series[[column_name]]
        ema = ema.ewm(span=window).mean()
        ema.rename(columns = {column_name:new_column_name}, inplace = True)
        return ema


    def signal_to_place(self):
        if self._adjusted_loans['possible_loans'] < 1:
            return False
        minutes = 26 * cc.get_check_interval()
        now = du.date_to_ts(dt.datetime.utcnow())
        min_date_ts = now - minutes
        min_date = dt.datetime.utcfromtimestamp(min_date_ts)
        iterator = self.db.select(cc.get_lending_market_state_table_name(), where='date_time>"' + str(min_date) + '"')
        
        data_source = {}
        for row in iterator:
            date_time = row['date_time']
            date_time = date_time.strftime(du.date_time_format)
            del row['date_time']
            data_source[date_time] = row
            
        df = pd.DataFrame.from_dict(data_source, orient='index')
        df['sum'] = df['placing_index'] + df['rate_index'] + df['duration_index']
        
        slow = self.ema(df, 'sum', 'slow', 26)
        fast = self.ema(df, 'sum', 'fast', 12)
        
        diff = pd.DataFrame(fast['fast'] - slow['slow'], columns=['diff'])
        diff['diff'] = diff['diff'].apply(lambda x: 1 if x > 0 else -1)
        result = pd.concat([fast, slow, diff], axis=1)
        
        signal = result.tail(1)
        signal = signal['diff']
        signal = signal.get_values()[0]
        signal = False if signal == -1 else True
        return signal


class Placer:
    
    def __init__(self, analyzer):
        self.exchange_name = analyzer.exchange_name
        self.exchange = analyzer.exchange
        self.db = analyzer.db
        self.latest_rate = analyzer._latest_rate
        self.adjusted_loans = analyzer._adjusted_loans
        self.min_loan = analyzer.min_loan
    
    def cancel_all_offers(self):
        on_offers = self.exchange.returnOpenLoanOffers()
        if 'BTC' in on_offers:
            on_offers = on_offers['BTC']
        else:
            on_offers = []
        
        for loan in on_offers:
            self.exchange.cancelLoanOffer(loan['id'])
    
    def place(self):
        loan_size = self.adjusted_loans['loan_size']
        try:
            if loan_size >= self.min_loan:
                self.exchange.createLoanOffer('BTC', loan_size, self.latest_rate)
        except:
            try:
                logger.warn("Trying to place minimal loan due to error")
                self.exchange.createLoanOffer('BTC', self.min_loan, self.latest_rate)
            except:
                logger.error("Error on placing loan")
