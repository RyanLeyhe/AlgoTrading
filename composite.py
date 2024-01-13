import requests
import time
from scipy import stats
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.stream import TradingStream

ALPHA_VANTAGE_API_KEY = "9JHZZHG5ITOP86SG"
API_KEY = 'PKD9TTQPDEOBX4FAR06U'
API_SECRET_KEY = 'vnbC7oAw6tm7x1yZLrq30pUtgRFR9fIutgDj7yvS'

def get_alpha_vantage_data(symbol, function):
    print(f"Getting data for {symbol} from Alpha Vantage API...")
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }

    if 'X-RateLimit-Remaining' in response.headers:
        remaining_requests = int(response.headers['X-RateLimit-Remaining'])
        reset_time = int(response.headers['X-RateLimit-Reset'])
        current_time = time.time()

        if remaining_requests == 0:
            time_to_reset = reset_time - current_time
            print(f"Rate limit reached. Waiting for {time_to_reset} seconds.")
            time.sleep(time_to_reset + 1)  # Wait for the rate limits to reset

    response = requests.get(base_url, params=params)

    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.content}")
    print(f"Response Headers: {response.headers}")

    data = response.json()

    return data

def get_stock_metrics(symbol):
    print(f"Getting stock metrics for {symbol}...")
    overview_data = get_alpha_vantage_data(symbol, "OVERVIEW")
    balance_sheet_data = get_alpha_vantage_data(symbol, "BALANCE_SHEET")

    pe_ratio = float(overview_data.get('PERatio', 0))
    pb_ratio = float(overview_data.get('PriceToBookRatio', 0))
    ps_ratio = float(overview_data.get('PriceToSalesRatioTTM', 0))

    market_cap = float(overview_data.get('MarketCapitalization', 0))
    annual_reports = balance_sheet_data.get('annualReports', [])
    total_debt = float(annual_reports[0].get('shortLongTermDebtTotal', 0)) if len(annual_reports) > 0 else 0
    cash = float(annual_reports[1].get('cashAndCashEquivalentsAtCarryingValue', 0)) if len(annual_reports) > 1 else 0

    enterprise_value = market_cap + total_debt - cash

    ebitda = float(overview_data.get('EBITDA', 0))
    ev_to_ebitda = float(overview_data.get('EVToEBITDA', 0))
    gross_profit = float(overview_data.get('GrossProfitTTM', 0))
    ev_to_gross_profit = float(overview_data.get('EVToGrossProfitTTM', 0))

    return {
        'Symbol': symbol,
        'PERatio': pe_ratio,
        'PriceToBookRatio': pb_ratio,
        'PriceToSalesRatioTTM': ps_ratio,
        'EnterpriseValue': enterprise_value,
        'EBITDA': ebitda,
        'EVToEBITDA': ev_to_ebitda,
        'GrossProfitTTM': gross_profit,
        'EVToGrossProfitTTM': ev_to_gross_profit,
    }

def get_sp500_symbols():
    print("Getting S&P 500 symbols...")
    url = f'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url)
    data = response.json()

    sp500_symbols = [stock['symbol'] for stock in data.get('data', []) if stock.get('indexName') == 'S&P 500']
    return sp500_symbols

sp500_stocks = get_sp500_symbols()

all_stock_data = []

for symbol in sp500_stocks:
    stock_metrics = get_stock_metrics(symbol)
    all_stock_data.append(stock_metrics)
    
metrics = [
    'PERatio',
    'PriceToBookRatio',
    'PriceToSalesRatioTTM',
    'EVToEBITDA',
    'EVToGrossProfitTTM',
]

# calculate percentiles (added to all_stock_data)
for metric in metrics:
    values = [stock[metric] for stock in all_stock_data]
    percentiles = [stats.percentileofscore(values, value) / 100 for value in values]
    
    for i, stock in enumerate(all_stock_data):
        stock[f'{metric} Percentile'] = percentiles[i]

# calculate  mean of percentiles
for stock in all_stock_data:
    mean_percentile = sum(stock[f'{metric} Percentile'] for metric in metrics) / len(metrics)
    stock['Mean Percentile'] = mean_percentile

# Sort the stocks based on mean percentile in descending order
sorted_stocks = sorted(all_stock_data, key=lambda x: x['Mean Percentile'], reverse=True)

# Keep only the top 50 stocks
top_50_stocks = sorted_stocks[:50]

def portfolio_input():
    while True:
        try:
            portfolio_size = float(input("Enter the value of your portfolio: "))
            if portfolio_size <= 0:
                raise ValueError("Portfolio size must be a positive number.")
            break  # Exit the loop if valid input is provided
        except ValueError:
            print("Invalid input! Please enter a valid numeric value for the portfolio size.")

    return portfolio_size

portfolio_size = portfolio_input()
print(f"Portfolio size: {portfolio_size}")

trading_client = TradingClient(f'{API_KEY}', f'{API_SECRET_KEY}', paper=True)
trades = TradingStream(f'{API_KEY}', f'{API_SECRET_KEY}', paper=True)

# Calculate the number of stocks to buy for each stock in the top 50
for stock in top_50_stocks:
    weight_in_portfolio = stock['Mean Percentile'] / 100 
    stock_price = trading_client.get_last_trade(stock['Symbol']).price
    number_of_stocks = len(top_50_stocks)
    
    shares_to_buy = (portfolio_size * weight_in_portfolio) / (stock_price * number_of_stocks)
    
    stock['Shares to Buy'] = shares_to_buy

for stock in top_50_stocks:
    symbol = stock['Symbol']
    shares_to_buy = int(stock['Shares to Buy'])

    # placing the order
    order_details = MarketOrderRequest(
        symbol=symbol, 
        qty=shares_to_buy, 
        side=OrderSide.BUY, 
        time_in_force=TimeInForce.DAY 
    )

    # Submiting the order
    order = trading_client.submit_order(order_data=order_details)

    # message from the order
    print(f"Order placed for {shares_to_buy} shares of {symbol}.\n")

trades.run()