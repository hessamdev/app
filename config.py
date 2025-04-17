# Please go to README.md to set up tradex_config.py
import MetaTrader5 as mt5
from datetime import datetime, timedelta

mt5_credentials = {
    'login': 5027963680,
    'password': 'LvLfP*Y7',
    'server': 'MetaQuotes-Demo',
    'exe_path': None
}
coinex_api = {
    'apiKey': 'CDEE5647AFE1473DB2BE6AF985B9CD3C',
        'secret': 'ADADA9DCD67B760E5FC1C911F22D1DFB940567F48C4ED4C4'
}

coinex_api_b = {
    'apiKey': 'CC9D562A95304E898522B2927F3607F9',
    'secret': 'A84ED184826341662A56919AB87D790A8385A5B9F585E646'
}

def initialize_mt5():
    mt5.initialize(mt5_credentials['exe_path'])
    mt5.login(mt5_credentials['login'], mt5_credentials['password'], mt5_credentials['server'])
