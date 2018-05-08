
import time
import urllib2
import json
import urllib
import hashlib
import hmac


def createTimeStamp(datestr, f="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, f))

class PoloniexLenderImpl():
    
    def __init__(self, APIKey, Secret):
        self.APIKey = APIKey
        self.Secret = Secret
        self.endPoint = "https://poloniex.com/tradingApi"
        self.publicEndPoint = "https://poloniex.com/public"

    @classmethod
    def authorized(cls, APIKey, Secret):
        return cls(APIKey, Secret)
    
    @classmethod
    def unauthorized(cls):
        return cls(None, None)

    def post_process(self, before):
        after = before

        # Add timestamps if there isn't one but is a datetime
        if('return' in after):
            if(isinstance(after['return'], list)):
                for x in xrange(0, len(after['return'])):
                    if(isinstance(after['return'][x], dict)):
                        if('datetime' in after['return'][x] and 'timestamp' not in after['return'][x]):
                            after['return'][x]['timestamp'] = float(createTimeStamp(after['return'][x]['datetime']))
                            
        return after

    def api_query(self, command, req={}):
        if command == "returnLoanOrders":
            ret = urllib2.urlopen(urllib2.Request(self.publicEndPoint + '?command=' + command + '&currency=' + str(req['currency'])))
            return json.loads(ret.read())
        else:
            req['command'] = command
            req['nonce'] = int(time.time()*1000)
            post_data = urllib.urlencode(req)
    
            sign = hmac.new(self.Secret, post_data, hashlib.sha512).hexdigest()
            headers = {
                'Sign': sign,
                'Key': self.APIKey
            }
    
            ret = urllib2.urlopen(urllib2.Request(self.endPoint, post_data, headers))
            jsonRet = json.loads(ret.read())
            return self.post_process(jsonRet)


    """
    Returns the list of loan offers and demands for a given currency, specified by the "currency" GET parameter. Sample output:
    
    Response:
    {"offers":[{"rate":"0.00200000","amount":"64.66305732","rangeMin":2,"rangeMax":8}, ... ],"demands":[{"rate":"0.00170000","amount":"26.54848841","rangeMin":2,"rangeMax":2}, ... ]}
    """
    def returnLoanOrders(self, currency='BTC'):
        return self.api_query("returnLoanOrders", {'currency': currency})

    """
    Creates a loan offer for a given currency. Required POST parameters are "currency", "amount", "duration", "autoRenew" (0 or 1),
    and "lendingRate". Sample output:
    
    Response
    {"success":1,"message":"Loan order placed.","orderID":10590}
    """
    def createLoanOffer(self, currency, amount, lendingRate, duration=2, autoRenew=0):
        return self.api_query("createLoanOffer", {"currency":currency, "amount":amount, "lendingRate":lendingRate,
                                                   "duration":duration, "autoRenew":autoRenew})

    """
    Cancels a loan offer specified by the "orderNumber" POST parameter. Sample output:

    Response
    {"success":1,"message":"Loan offer canceled."}
    """
    def cancelLoanOffer(self, orderNumber):
        return self.api_query("cancelLoanOffer", {"orderNumber":orderNumber})

    """
    Returns your open loan offers for each currency. Sample output:
    
    Response
    {"BTC":[{"id":10595,"rate":"0.00020000","amount":"3.00000000","duration":2,"autoRenew":1,"date":"2015-05-10 23:33:50"}],
    "LTC":[{"id":10598,"rate":"0.00002100","amount":"10.00000000","duration":2,"autoRenew":1,"date":"2015-05-10 23:34:35"}]}
    """
    def returnOpenLoanOffers(self):
        return self.api_query("returnOpenLoanOffers")

    """
    Returns your active loans for each currency. Sample output:
    
    {"provided":[{"id":75073,"currency":"LTC","rate":"0.00020000","amount":"0.72234880","range":2,"autoRenew":0,"date":"2015-05-10 23:45:05","fees":"0.00006000"},
    {"id":74961,"currency":"LTC","rate":"0.00002000","amount":"4.43860711","range":2,"autoRenew":0,"date":"2015-05-10 23:45:05","fees":"0.00006000"}],"used":[{"id":75238,"currency":"BTC","rate":"0.00020000","amount":"0.04843834","range":2,"date":"2015-05-10 23:51:12","fees":"-0.00000001"}]}
    """
    def returnActiveLoans(self):
        active_loans = self.api_query("returnActiveLoans")
        if 'provided' in active_loans:
            active_loans = active_loans['provided']
        else:
            active_loans = []
        return active_loans

    """
    Returns your lending history within a time range specified by the "start" and "end" POST parameters as UNIX timestamps.
    "limit" may also be specified to limit the number of rows returned. Sample output:
    
    Response
    [{ "id": 175589553, "currency": "BTC", "rate": "0.00057400", "amount": "0.04374404", "duration": "0.47610000",
    "interest": "0.00001196", "fee": "-0.00000179", "earned": "0.00001017", "open": "2016-09-28 06:47:26", "close": "2016-09-28 18:13:03" }]
    """
    def returnLendingHistory(self, start, end, limit=100):
        return self.api_query("returnLendingHistory", {"start":start, "end":end, "limit":limit})

    """
    Toggles the autoRenew setting on an active loan, specified by the "orderNumber" POST parameter.
    If successful, "message" will indicate the new autoRenew setting. Sample output:

    Response
    {"success":1,"message":0}
    """
    def toggleAutoRenew(self, orderNumber):
        return self.api_query("toggleAutoRenew", {"orderNumber":orderNumber})

    """
    Returns your balances sorted by account. You may optionally specify the "account" POST parameter if you wish to fetch only the
    balances of one account. Please note that balances in your margin account may not be accessible if you have any open margin positions
    or orders.
    
    {"exchange":{"BTC":"1.19042859","BTM":"386.52379392","CHA":"0.50000000","DASH":"120.00000000","STR":"3205.32958001", "VNL":"9673.22570147"},
    "margin":{"BTC":"3.90015637","DASH":"250.00238240","XMR":"497.12028113"},
    "lending":{"DASH":"0.01174765","LTC":"11.99936230"}}
    """
    def returnBalances(self):
        balances = self.api_query("returnAvailableAccountBalances")
        if 'lending' in balances:
            return balances['lending']
        else:
            return []
