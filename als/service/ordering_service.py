
import web
import json
import sys

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


def parse_argv():
    required_args = ['-dbu', '-dbp', '-dbn', '-d', '-en', '-eak', '-es', '-uid']
    
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


def create_analyzer():
    args = parse_argv()
    exchange_name = args['-en']
    exchange_api_key = args['-eak']
    exchange_secret = args['-es']
    db_name = args['-dbn']
    db_username = args['-dbu']
    db_password = args['-dbp']
    user_id = args['-uid']
    analyzer = Analyzer(exchange_name, exchange_api_key, exchange_secret, db_name, db_username, db_password, user_id)
    return analyzer


def place_order():
    analyzer = create_analyzer()
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
        args_dict = parse_argv()
        db_name = args_dict['-dbn']
        db_password = args_dict['-dbp']
        db_username = args_dict['-dbu']
        db = web.database(dbn='mysql', db=db_name, user=db_username, pw=db_password)
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
