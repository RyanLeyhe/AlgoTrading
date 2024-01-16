from config import ALPACA_CONFIG
import time
import requests
import alpaca_trade_api as tradeapi
from datetime import datetime
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies import Strategy
from lumibot.traders import Trader
import numpy as np
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.stream import TradingStream
import requests

API_KEY = 'PKJM5Z6YB09J0AR2BYO8'
API_SECRET_KEY = 'NTTjWZYoU9rwW6uNJWuntScAP5LO2cEgdi0e59ug'

# trend following algorithm for gold

class AlpacaHelper:
    def __init__(self, API_KEY, API_SECRET_KEY, base_url='https://paper-api.alpaca.markets'):
        self.api = tradeapi.REST(API_KEY, API_SECRET_KEY, base_url, api_version='v2')

    def get_market_clock(self):
        url = "https://paper-api.alpaca.markets/v2/clock"

        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": f"{API_KEY}",
            "APCA-API-SECRET-KEY": f"{API_SECRET_KEY}"
        }

        response = requests.get(url, headers=headers)
        return response.json()

    def is_market_open(self):
        clock = self.api.get_clock()
        return clock.is_open

    def wait_for_market_open(self):
        clock_response = self.get_market_clock()
        next_open = datetime.fromisoformat(clock_response['next_open'])
        now = datetime.now()

        if now < next_open:
            wait_time = (next_open - now).total_seconds()
            hours, remainder = divmod(wait_time, 3600)
            minutes, seconds = divmod(remainder, 60)

            print(f"The market is closed. Waiting for it to open in {int(hours)} hours and {int(minutes)} minutes...")

            # Sleep until the market opens
            time.sleep(wait_time)

        print("The market is now open. Proceeding with trading...")


class Trend(Strategy):

    def initialize(self):
        signal = None
        # start = "2022-01-01"

        self.signal = signal # signal is whether or not to place order
        # self.start = start
        self.sleeptime = "1D" # how often to run
    # minute bars, make functions    

    def on_trading_iteration(self):
        bars = self.get_historical_prices("GLD", 22, "day") # get historical prices from alpaca going back 22 days
        gld = bars.df
        #gld = pd.DataFrame(yf.download("GLD", self.start)['Close'])
        gld['9-day'] = gld['close'].rolling(9).mean() # 9 day moving average
        gld['21-day'] = gld['close'].rolling(21).mean() # 21 day moving average
        gld['Signal'] = np.where(np.logical_and(gld['9-day'] > gld['21-day'], # check if 9 day above 21 day
                                                gld['9-day'].shift(1) < gld['21-day'].shift(1)), # was it below on the previous day
                                "BUY", None)
        gld['Signal'] = np.where(np.logical_and(gld['9-day'] < gld['21-day'], # check if 9 day below 21 day
                                                gld['9-day'].shift(1) > gld['21-day'].shift(1)), # was it above on the previous day
                                "SELL", gld['Signal'])
        self.signal = gld.iloc[-1].Signal
        
        symbol = "GLD"
        quantity = 200
        if self.signal == 'BUY':
            pos = self.get_position(symbol) # check to see that we don't already have a position
            if pos is not None: # if you already have a position, sell it
                self.sell_all()
                
            order = self.create_order(symbol, quantity, "buy") # create order
            self.submit_order(order) # submit order
            print("BUY")

        elif self.signal == 'SELL': # if sell signal
            pos = self.get_position(symbol) # do we already have a position
            if pos is not None:
                self.sell_all()
                
            order = self.create_order(symbol, quantity, "sell") # create order
            self.submit_order(order) # submit order
            print("SELL")


if __name__ == "__main__":
    broker = Alpaca(ALPACA_CONFIG)
    strategy = Trend(broker=broker)
    bot = Trader()
    bot.add_strategy(strategy)
    bot.run_all()


# backtesting
if __name__ == "__main__":
    trade = False
    if trade:
        broker = Alpaca(ALPACA_CONFIG)
        strategy = Trend(broker=broker)
        bot = Trader()
        bot.add_strategy(strategy)
        bot.run_all()
    else:
        start = datetime(2022, 4, 15)
        end = datetime(2023, 4, 15)
        Trend.backtest(
            YahooDataBacktesting,
            start,
            end
        )

# buy and hold algorithm

class BuyHold(Strategy):

    def initialize(self):
        self.sleeptime = "10S"

    def on_trading_iteration(self):
        if self.first_iteration:
            symbol = "GOOG"
            price = self.get_last_price(symbol)
            quantity = self.cash // price
            if quantity <= 0.0:
                quantity = 1.0
            order = self.create_order(symbol, quantity, "buy")
            self.submit_order(order)

if __name__ == "__main__":
    trade = True
    if trade:
        broker = Alpaca(ALPACA_CONFIG)
        strategy = BuyHold(broker=broker)
        trader = Trader()
        trader.add_strategy(strategy)
        trader.run_all()


# momentum algorithm

class SwingHigh(Strategy):
    data = []
    order_number = 0
    def initialize(self):
        self.sleeptime = "10S"


    def on_trading_iteration(self):
        symbol ="GOOG"
        entry_price = self.get_last_price(symbol)
        self.log_message(f"Position: {self.get_position(symbol)}")
        self.data.append(self.get_last_price(symbol))

        if len(self.data) > 3:
            temp = self.data[-3:]
            if temp[-1] > temp[1] > temp[0]:
                self.log_message(f"Last 3 prints: {temp}")
                order = self.create_order(symbol, quantity = 10, side = "buy")
                self.submit_order(order)
                self.order_number += 1
                if self.order_number == 1:
                    self.log_message(f"Entry price: {temp[-1]}")
                    entry_price = temp[-1] # filled price
            if self.get_position(symbol) and self.data[-1] < entry_price * .995:
                self.sell_all()
                self.order_number = 0
            elif self.get_position(symbol) and self.data[-1] >= entry_price * 1.015:
                self.sell_all()
                self.order_number = 0

        order_details = MarketOrderRequest(
        symbol="SPY", # symbol to trade (e.g. AAPL)
        qty=5, # number of shares
        side=OrderSide.BUY, # buy or sell
        time_in_force=TimeInForce.DAY # day, gtc, opg, cls, ioc, fok.
        )

        trading_client = TradingClient(f'{API_KEY}', f'{API_SECRET_KEY}', paper=True)

        # Submit the order
        order = trading_client.submit_order(order_data=order_details)

        # message from the order
        trades = TradingStream(f'{API_KEY}', f'{API_SECRET_KEY}', paper=True)
        async def trade_status(data):
            print(data)

        trades.subscribe_trade_updates(trade_status)
        trades.run()


    def before_market_closes(self):
        self.sell_all()


if __name__ == "__main__":
    broker = Alpaca(ALPACA_CONFIG)
    strategy = SwingHigh(broker=broker)
    trader = Trader()
    trader.add_strategy(strategy)
    trader.run_all()
