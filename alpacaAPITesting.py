from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.stream import TradingStream
import requests

API_KEY = 'PKSMEKVD6GXH88SHS3AI'
API_SECRET_KEY = 'Sai8vCc3bHbnoE8uTUimoqkqLxgTCD0OvrfiG0eF'

url = "https://paper-api.alpaca.markets/v2/clock"

headers = {
    "accept": "application/json",
    "APCA-API-KEY-ID": "PKSMEKVD6GXH88SHS3AI",
    "APCA-API-SECRET-KEY": "Sai8vCc3bHbnoE8uTUimoqkqLxgTCD0OvrfiG0eF"
}

response = requests.get(url, headers=headers)

print(response.text)



"""
# paper=True enables paper trading
trading_client = TradingClient(f'{API_KEY}', f'{API_SECRET_KEY}', paper=True)

# Get our account information
account = trading_client.get_account()
accountDict = dict(trading_client.get_account())
for k, v in accountDict.items():
    print(f"{k:30}{v}")

# placing an order
order_details = MarketOrderRequest(
    symbol="SPY", # symbol to trade (e.g. AAPL)
    qty=5, # number of shares
    side=OrderSide.BUY, # buy or sell
    time_in_force=TimeInForce.DAY # day, gtc, opg, cls, ioc, fok.
)

# Submit the order
order = trading_client.submit_order(order_data=order_details)

# message from the order
trades = TradingStream(f'{API_KEY}', f'{API_SECRET_KEY}', paper=True)
async def trade_status(data):
    print(data)

trades.subscribe_trade_updates(trade_status)
trades.run()

# list of all assets
assets = [asset for asset in trading_client.get_all_positions()]
positions = [(asset.symbol, asset.qty, asset.current_price) for asset in assets]
for position in positions:
    print(position)

# cancel all open orders
trading_client.close_all_positions(cancel_orders=True)



# Get assets
search_params = GetAssetsRequest(asset_class=AssetClass.CRYPTO)
assets = trading_client.get_all_assets(search_params)

# preparing orders
market_order_data = MarketOrderRequest(
                    symbol="SPY",
                    qty=0.023,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                    )

# Market order
market_order = trading_client.submit_order(
                order_data=market_order_data
               )

# Limit order
limit_order_data = LimitOrderRequest(
                    symbol="BTC/USD",
                    limit_price=17000,
                    notional=4000,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.FOK
                   )

# Limit order
limit_order = trading_client.submit_order(
                order_data=limit_order_data
              )

# attempt to cancel all open orders
cancel_statuses = trading_client.cancel_orders()

# get all positions
trading_client.get_all_positions()

# closes all position AND also cancels all open orders
trading_client.close_all_positions(cancel_orders=True)

# trading stream
trading_stream = TradingStream(f'{API_KEY}', f'{API_SECRET_KEY}', paper=True)

async def update_handler(data):
    # trade updates will arrive in our async handler
    print(data)

# subscribe to trade updates and supply the handler as a parameter
trading_stream.subscribe_trade_updates(update_handler)

# start our websocket streaming
trading_stream.run()

"""
 # 9JHZZHG5ITOP86SG