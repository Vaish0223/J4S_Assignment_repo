from flask import Flask, jsonify, request
import os
from flask_cors import CORS
from data_processor import StockDataProcessor
import json

#To initialize flask app
app = Flask(__name__)
''' Used to perform enable cross-origin resource sharing to allow requests from
React file for api endpoints.'''
CORS(app)
# ~~~~~~~~ Initializing Data Processor ~~~~~~~~~~
# to avoid any trouble while data reloading and reviewing while requesting
print("Starting the server... Please wait it's not too long!")
script_dir= os.path.dirname(__file__)      # to ensure file is found and there is no error.
csv_path = os.path.join(script_dir, 'reliance_data.csv')  # to ensure file is found and there is no error.

try:
    processor = StockDataProcessor(csv_path)
    print("Data Processor initializing succeeded.")
except FileNotFoundError:
    print(f"MASSIVE ERROR: the data file {csv_path} was not found. Please ensure the file path is correct.")
    exit()

# ~~~~~~~ Initializing API Endpoints ~~~~~~~~
@app.route('/api/stock/summary', methods=['GET'])
def get_stock_summary():
    # this will return statistics and data from the data file
    summary_data = processor.get_summary()
    return jsonify(summary_data)

# this will return the data for the specified timeframe.
# for timeframes = 1min, 5min, 15min
@app.route('/api/stock/timeseries/<timeframe>', methods=['GET'])
def get_timeseries_data(timeframe):
    allowed_timeframes = ['1Min', '5Min', '15Min', '1H']
    if timeframe not in allowed_timeframes:
        return jsonify({"error": f"Invalid timeframe. Allowed values: {allowed_timeframes}"}), 400
            
    timeseries_data = processor.get_timeseries_data(timeframe)
    return jsonify(timeseries_data)

# API Endpoint to return order book analysis.
@app.route('/api/stock/orderbook', methods=['GET'])
def get_orderbook_analysis():
    orderbook_data = processor.get_orderbook_analysis()
    return jsonify(orderbook_data)

# Endpoint to return calculated technical indicators in different timeframes
@app.route('/api/stock/indicators', methods=['GET'])
def get_technical_indicators():
    indicators_data = processor.get_technical_indicators()
    return jsonify(indicators_data)

# ~~~~~~ Main Part: Running the Flask App ~~~~~~~
"""Here, fask app will run at port 5000 and 
    debug=True indicates that server will be automatically reloaded if the 
        code changes while live streaming the app."""
if __name__ == "__main__":
    app.run(debug=True, port=5000)
    
## COMPLETED 