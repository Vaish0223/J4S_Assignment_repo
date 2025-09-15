# Stock Market Data Analysis Assignment
**Reliance Industries Trading Data Visualization**

Developed a comprehensive stock market analysis system using both Python and React to analyze high-frequency trading data from Reliance Industries (NSE: RELIANCE). 
The dataset contains 22,618 rows of tick-by-tick trading data with 113 different metrics including price movements, order book data, and trading volumes.

**What project comprises:**

*A backend folder comprising the "data_processor" and "api.py" files which have all the code:*
 - data_processor.py file basically contains a class StockDataProcessor which has fuctions: _load_csv, _clean_data, _calculate_technical_indicators, _perform_statistical_analysis.
 - These functions perform loading, cleaning, fixing missing values, VWAP validations, Price volatility, other calculations.
 - Rest of the functions perform statistical analysis and the necessary commands used to function the API file.
 - api.py file structured to include all the endpoints.
 - csv file used is "reliance_data.csv". 

*The frontend/src/visualized folder contains React-app to visualize our data and track its live changes and the trends it take between a specified timeframe*
 - src/App.js file constitute the entire code required for building a react-app to visualize the data fetched from the backend server(i.e.Flask server).
 - 'lightweight-charts' is the charting library imported to the file to display the data fetched from backend into charts in the app.
 -  These charts shows the Open, High, Low, and Close (OHLC) prices for a period from Candlestick Chart.

## How to Run

### 1. Backend (Flask API)

- Navigate to the `data` folder:
  ```bash
  cd data
  python api.py # for flask api file to execute via terminal
The API will be available at "http://127.0.0.1:5000". *Warning:* Ensure the flask server to run efficiently for react app to execute efficiently.

### 2. Frontend (React-app)

- Navigate to the `frontend/src/visualized` folder:
  ```bash
  cd src #as the main executable file App.js is inside src folder
  npm start #this will initialize the react app
The application will open in your browser at "http://localhost:3000".


**Assignment by Vaishnavi Dixit**
