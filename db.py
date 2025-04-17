import sys
import os

# اضافه کردن مسیر ریشه پروژه به sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
import pandas as pd
import time
from datetime import datetime
from api.api_coinex import get_dataframe
import trade_config





class OHLC_DB:
    def __init__(self, config):
        """Connecting to MySQL database with provided configuration"""
        try:
            self.conn = pymysql.connect(
                host=config['db_host'],
                user=config['db_user'],
                password=config['db_password'],
                database=config['db_name']
            )
            print("Database connection established.")
        except pymysql.MySQLError as e:
            print(f"Error connecting to database: {e}")
            raise

    def create_ohlc_table(self, columns):
        """Create the OHLC table in the database with dynamic structure"""
        cols_def = [f"`{col}` DOUBLE" if col not in ['time', 'symbol', 'timeframe'] 
                    else f"`{col}` VARCHAR(20)" if col != 'time' else "`time` DATETIME" 
                    for col in columns]
        try:
            self.execute(f"""
                CREATE TABLE IF NOT EXISTS ohlc (
                    {','.join(cols_def)},
                    PRIMARY KEY (symbol, timeframe, time)
            )""")
            print("Table 'ohlc' created in the database.")
        except pymysql.MySQLError as e:
            print(f"Error creating table: {e}")
            raise

    def insert_or_update_ohlc(self, df):
        """Insert or update the data into the OHLC table"""
        cols = ','.join([f'`{c}`' for c in df.columns])
        vals = ','.join(['%s']*len(df.columns))
        sql = f"INSERT INTO ohlc ({cols}) VALUES ({vals}) ON DUPLICATE KEY UPDATE "
        sql += ','.join([f"`{c}`=VALUES(`{c}`)" for c in df.columns[3:]])
        try:
            self.executemany(sql, df.values.tolist())
            print(f"{len(df)} record(s) added or updated in the 'ohlc' table.")
        except pymysql.MySQLError as e:
            print(f"Error inserting/updating data: {e}")
            raise

    def execute(self, query):
        """Execute the SQL query"""
        with self.conn.cursor() as cur:
            cur.execute(query)
            self.conn.commit()

    def executemany(self, query, values):
        """Execute multiple SQL queries at once"""
        with self.conn.cursor() as cur:
            cur.executemany(query, values)
            self.conn.commit()


class OhlcUpdater:
    def __init__(self, config, symbols_timeframes):
        """
        Initial setup: connecting to the database and receiving symbols and timeframes
        symbols_timeframes: A dictionary that associates symbols with timeframes
        """
        self.db = OHLC_DB(config)
        self.symbols_timeframes = symbols_timeframes

    def update_ohlc_data(self):
        """Update OHLC data for each symbol and timeframe"""
        for symbol, timeframe in self.symbols_timeframes.items():
            # Create the table if it doesn't exist
            columns = ['symbol', 'timeframe', 'time', 'open', 'high', 'low', 'close', 'volume']
            self.db.create_ohlc_table(columns)

            # Fetch initial 1000 candles for each symbol and timeframe
            print(f"Fetching 1000 candles for {symbol} with timeframe {timeframe}")
            df = get_dataframe(market=symbol, limit=1000, period=timeframe)
            if df is not None and not df.empty:
                self.db.insert_or_update_ohlc(df)
            else:
                print(f"No data returned for {symbol} with timeframe {timeframe}.")
                continue  # Skip if no data is returned

            # Then update every 2 seconds with the latest candle
            while True:
                time.sleep(2)  # Wait for 2 seconds
                print(f"Fetching new candle for {symbol} with timeframe {timeframe}")
                df_last = get_dataframe(market=symbol, limit=1, period=timeframe)
                if df_last is not None and not df_last.empty:
                    self.db.insert_or_update_ohlc(df_last)
                else:
                    print(f"No new data for {symbol} with timeframe {timeframe}. Skipping.")


# تنظیمات دیتابیس
config = trade_config.CONFIG

# دیکشنری از سیمبول‌ها و تایم‌فریم‌های آن‌ها
symbols_timeframes = {
    'BTCUSDT': '1min',
    'DOGEUSDT': '5min',
}

# شروع فرآیند آپدیت
updater = OhlcUpdater(config, symbols_timeframes)
updater.update_ohlc_data()
