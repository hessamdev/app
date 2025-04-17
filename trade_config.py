CONFIG = {
        'db_host': 'localhost',
        'db_port': 3306,
        'db_name': 'hessam',
        'db_user': 'root',
        'db_password': '',

        'namebot': 'shib-bot',
        'symbol': 'DOGEUSDT',
        'timeframe': '3min',


        'length': 14,
        'multipliers': [3, 1.5, 2],
        'wicks': False,
        'ema_periods': {
            'short': 9,
            'long': 50},
      
        'leverage' : 50 ,
        'initial_balance': 1000,
        'risk_per_trade': 0.5,  # 100% risk per trade
        'sl_multiplier': 0.3,  

        #dashbord
        'num_candel': 100  
    }