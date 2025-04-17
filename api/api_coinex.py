# -*- coding: utf-8 -*-
import hashlib
import json
import time
from datetime import datetime, timedelta
import hmac
from urllib.parse import urlparse
import pandas as pd
import numpy as np
import sys
import os

# اضافه کردن مسیر ریشه پروژه به sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import coinex_api

import requests
pd.set_option('display.max_columns', None)
pd.set_option('display.precision', 10)
access_id = coinex_api['apiKey']  # Replace with your access id
secret_key = coinex_api['secret']  # Replace with your secret key


class RequestsClient(object):
    HEADERS = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "X-COINEX-KEY": "",
        "X-COINEX-SIGN": "",
        "X-COINEX-TIMESTAMP": "",
    }

    def __init__(self):
        self.access_id = access_id
        self.secret_key = secret_key
        self.url = "https://api.coinex.com/v2"
        self.headers = self.HEADERS.copy()

    # Generate your signature string
    def gen_sign(self, method, request_path, body, timestamp):
        prepared_str = f"{method}{request_path}{body}{timestamp}"
        signature = hmac.new(
            bytes(self.secret_key, 'latin-1'),
            msg=bytes(prepared_str, 'latin-1'),
            digestmod=hashlib.sha256
        ).hexdigest().lower()
        return signature

    def get_common_headers(self, signed_str, timestamp):
        headers = self.HEADERS.copy()
        headers["X-COINEX-KEY"] = self.access_id
        headers["X-COINEX-SIGN"] = signed_str
        headers["X-COINEX-TIMESTAMP"] = timestamp
        headers["Content-Type"] = "application/json; charset=utf-8"
        return headers

    def request(self, method, url, params={}, data=""):
        req = urlparse(url)
        request_path = req.path

        timestamp = str(int(time.time() * 1000))
        if method.upper() == "GET":
            # If params exist, query string needs to be added to the request path
            if params:
                query_params = []
                for item in params:
                    if params[item] is None:
                        continue
                    query_params.append(item + "=" + str(params[item]))
                query_string = "?{0}".format("&".join(query_params))
                request_path = request_path + query_string

            signed_str = self.gen_sign(
                method, request_path, body="", timestamp=timestamp
            )
            response = requests.get(
                url,
                params=params,
                headers=self.get_common_headers(signed_str, timestamp),
            )

        else:
            signed_str = self.gen_sign(
                method, request_path, body=data, timestamp=timestamp
            )
            response = requests.post(
                url, data, headers=self.get_common_headers(signed_str, timestamp)
            )

        if response.status_code != 200:
            raise ValueError(response.text)
        return response


request_client = RequestsClient()

def time_coinex():
    request_path = "/time"
    response = request_client.request(
        "GET",
        "{url}{request_path}".format(url=request_client.url, request_path=request_path))
    json_data = response.json()
    data = json.loads(json.dumps(json_data))
    df2 = pd.json_normalize(data['data'])
    return df2

# Get Market Status
def get_market_status(market='BTCUSDT'):
    request_path = "/futures/market"
    params = {'market': str(market)}  
    response = request_client.request(
        "GET",
        f"{request_client.url}{request_path}",
        params=params
    )
    
    # Check if response is successful
    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}")
    
    try:
        response_data = response.json()
        # print("Raw response:", response_data)  # Debug print
        
        # Check if response contains data
        if not response_data:
            raise Exception("Empty response received")
            
        # If the data structure is different than expected, adjust accordingly
        if 'data' not in response_data:
            # Maybe the entire response is the data?
            data = response_data
        else:
            data = response_data['data']

        if isinstance(data, list) and len(data) > 0:
            return data[0]  
        else:
            return data  
        
    except Exception as e:
        print(f"Error processing response: {e}")
        raise

# Market Information
def get_market_info():
    request_path = "/futures/ticker"
    response = request_client.request(
        "GET",
        "{url}{request_path}".format(url=request_client.url, request_path=request_path),
    )
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    return df2
# Get Market Depth
def get_market_depth(name="BTCUSDT", limit=10):
    request_path = "/futures/depth"
    params = {'market': name, 'limit': limit, 'interval': '0'}
    try:
        response = request_client.request(
            "GET",
            f"{request_client.url}{request_path}",
            params=params
        )
        data = response.json()

        # Safely extract and format the depth data
        depth_data = data.get('data', {}).get('depth', {})

        # Process asks
        asks = []
        raw_asks = depth_data.get('asks', [])
        if isinstance(raw_asks, list):
            for item in raw_asks:
                if isinstance(item, list) and len(item) >= 2:
                    try:
                        asks.append([float(item[0]), float(item[1])])
                    except (ValueError, TypeError):
                        continue

        # Process bids
        bids = []
        raw_bids = depth_data.get('bids', [])
        if isinstance(raw_bids, list):
            for item in raw_bids:
                if isinstance(item, list) and len(item) >= 2:
                    try:
                        bids.append([float(item[0]), float(item[1])])
                    except (ValueError, TypeError):
                        continue

        return {
            'asks': sorted(asks, key=lambda x: x[0]),
            'bids': sorted(bids, key=lambda x: x[0], reverse=True)
        }
    except Exception as e:
        print(f"Error getting market depth: {e}")
        return {'asks': [], 'bids': []}

def get_dataframe(market='BTCUSDT', limit=20, period="1min"):
    request_path = "/futures/kline"
    params = {'market': market, 'limit': limit, 'period': period}
    response = request_client.request(
        "GET",
        "{url}{request_path}".format(url=request_client.url, request_path=request_path), params=params
    )
    pd.set_option('display.max_columns', None)
    pd.set_option('display.precision', 10)
    pd.options.display.float_format = '{:.10f}'.format
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    # اضافه کردن ستون‌های ضروری با مقادیر معتبر
    df2['symbol'] = market
    df2['timeframe'] = period
    df2['time'] = pd.to_datetime(df2['created_at'], unit='ms')
    
    # حذف ستون‌های تکراری
    df2 = df2.loc[:, ~df2.columns.duplicated()]
    
    # تبدیل نوع داده‌ها
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        df2[col] = pd.to_numeric(df2[col], errors='coerce')
    
    # مرتب کردن ستون‌ها
    columns = ['symbol', 'timeframe', 'time', 'open', 'high', 'low', 'close', 'volume']
    df2 = df2.reindex(columns=columns)
    
    return df2

# ohlc = get_dataframe('SHIBUSDT', 2 , '3min')

# print(ohlc)

# print(ohlc)
# Get Current Position
def get_position(market = "BTUSDT"):
    request_path = "/futures/pending-position"
    params = {'market': market, 'market_type': 'FUTURES', 'page': 1, 'limit': 100 }
    response = request_client.request(
        "GET", "{url}{request_path}".format(url=request_client.url,
                                            request_path=request_path), params=params, )
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    return df2

# Get Historical Position
def get_Historical_position(market = "BTUSDT",start_time ="970391096000"):
    request_path = "/futures/finished-position"
    params = {'market': market, 'market_type': 'FUTURES', 'start_time': start_time, 'page': 1, 'limit': 100 }
    response = request_client.request(
        "GET", "{url}{request_path}".format(url=request_client.url,
                                            request_path=request_path), params=params, )
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    return df2

# open position

def open_position(market="BTUSDT",side = "buy" ,amount = "8"):
    request_path = "/futures/order"
    data = {
        "market": market,
        "market_type": "FUTURES",
        "side": side,
        "type": "market",
        "amount": amount,
        "client_id": "Vbot1",
            }
    data = json.dumps(data)
    response = request_client.request(
        "POST",
        "{url}{request_path}".format(url=request_client.url, request_path=request_path),
        data=data)
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    return json_string

#Set Position Stop Loss
def set_sl(market="BTUSDT",stop_loss_price = "0.059" ,):
    request_path = "/futures/set-position-stop-loss"
    params = {
        "market": market,
        "market_type": "FUTURES",
        "stop_loss_type": "mark_price",
        "stop_loss_price": stop_loss_price
            }
    response = request_client.request(
        "POST", "{url}{request_path}".format(url=request_client.url,
                                            request_path=request_path), params=params, )
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    return json_data

#Set Position Take Profit
def set_tp(market="BTUSDT",take_profit_price = "0.059" ,):
    request_path = "/futures/set-position-take-profit"
    params = {
        "market": market,
        "market_type": "FUTURES",
        "take_profit_type": "mark_price",
        "take_profit_price": take_profit_price
            }
    response = request_client.request(
        "POST", "{url}{request_path}".format(url=request_client.url,
                                            request_path=request_path), params=params, )
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    return json_data

# Close all position

def close_position(market="BTUSDT", ):
    request_path = "/futures/close-position"
    params = {
            "market": "CETUSDT",
            "market_type": "FUTURES",
            "type": "market",
            "price": "0.056",
            "amount": "10000",
            "client_id": "user1",
            # "is_hide": true
            }
    response = request_client.request(
        "GET", "{url}{request_path}".format(url=request_client.url,
                                            request_path=request_path), params=params, )
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    return json_data

def get_futures_balance():
    request_path = "/assets/futures/balance"
    response = request_client.request(
        "GET",
        "{url}{request_path}".format(url=request_client.url, request_path=request_path),
    )
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    return df2



def market_fee(name="BTCUSDT"):
    request_path = "/account/trade-fee-rate?"
    params = {'market_type': 'SPOT', 'market': name}
    response = request_client.request(
        "GET", "{url}{request_path}".format(url=request_client.url,
                                            request_path=request_path), params=params, )
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    return json_data


def get_spot_market(name="BTCUSDT"):
    request_path = "/spot/market?"
    params = {"market": name}
    response = request_client.request(
        "GET",
        "{url}{request_path}".format(url=request_client.url, request_path=request_path), params=params)
    json_data = response.json()
    json_string = json.dumps(json_data)
    data = json.loads(json_string)
    df2 = pd.json_normalize(data['data'])
    return df2


def get_spot_balance():
    request_path = "/assets/spot/balance"
    response = request_client.request(
        "GET",
        "{url}{request_path}".format(url=request_client.url, request_path=request_path),
    )
    return response





def get_deposit_address():
    request_path = "/assets/deposit-address"
    params = {"ccy": "USDT", "chain": "CSC"}

    response = request_client.request(
        "GET",
        "{url}{request_path}".format(url=request_client.url, request_path=request_path),
        params=params,
    )
    return response


def put_limit():
    request_path = "/spot/order"
    data = {
        "market": "BTCUSDT",
        "market_type": "SPOT",
        "side": "buy",
        "type": "limit",
        "amount": "10000",
        "price": "1",
        "client_id": "user1",
        "is_hide": True,
    }
    data = json.dumps(data)
    response = request_client.request(
        "POST",
        "{url}{request_path}".format(url=request_client.url, request_path=request_path),
        data=data,
    )
    return response


# def run_code():
#     try:
#         response_1 = get_spot_market().json()
#         print(response_1)
#
#         response_2 = get_spot_balance().json()
#         print(response_2)
#
#         response_3 = get_deposit_address().json()
#         print(response_3)
#
#         response_4 = put_limit().json()
#         print(response_4)
#
#     except Exception as e:
#         print("Error:" + str(e))
#         time.sleep(3)
#         run_code()


if __name__ == "__main__":
    pass
