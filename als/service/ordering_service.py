
import web
import json

from als.util.threads import RepeatThread
from als.service.analysis import Analyzer, Placer

from als.util import custom_config as cc, custom_logging
from als.util import date_utils as du

logger = custom_logging.get_logger('als.core')

urls = (
   '/rates_history', 'rates_history',
   '/stats', 'stats',
   '/show_data', 'show_data'
)


def place_order():
    analyzer = Analyzer()
    analyzer.evaluate_state(analyzer.adjust_loans())
    signal = analyzer.signal_to_place()
    placer = Placer(analyzer)
    placer.cancel_all_offers()
    if signal:
        logger.info('Order is going to be placed')
        placer.place()
    else:
        logger.info('Order won\'t be placed')

class show_data:
    def GET(self):
        db_name = cc.get_db_name()
        db_password = cc.get_db_password()
        db_username = cc.get_db_username()
        db = web.database(dbn=cc.get_db_engine(), db=db_name, user=db_username, pw=db_password)
        results = db.select(cc.get_lending_rate_table_name(), limit=100)
        
        dicts = {}
        for result in results:
            date_time = result['date_time']
            date_time = date_time.strftime(du.date_time_format)
            del result['date_time']
            dicts[date_time] = result
        
        json_string = json.dumps(dicts)
        return json_string

class rates_history:
    def GET(self):
        return 'rates_history'

class stats:
    def GET(self):
        return 'stats'

if __name__ == "__main__":
    thread = RepeatThread(cc.get_check_interval(), place_order)
    thread.start()
    app = web.application(urls, globals())
    app.run()
