import pandas as pd
import numpy as np

class StockDataProcessor:
    """
    A class to process and analyze high-frequency stock data.
    """
    def __init__(self, csv_path):
        """
        Initializes the processor, loads data, and runs all processing steps.
        
        Args:
            csv_path (str): The path to the stock data CSV file.
        """
        print("Initializing data processing...")
        self.data = self._load_data(csv_path)
        self._clean_data()
        self._calculate_technical_indicators()
        self._perform_statistical_analysis()
        print("Data processing complete.")
        
    def _load_data(self, csv_path):
        """Loads data, creates a timestamp, renames columns, and sets the index.
    This is a robust and highly compatible version with added debugging.
    """
        print(f"Loading data from {csv_path}...")
        df = pd.read_csv(csv_path)
        # Debug: Print columns to verify presence of required columns
        print("Columns in CSV:", df.columns.tolist())
        # Drop the extra unnamed column if it exists (from the CSV starting with a comma)
        if 'Unnamed: 0' in df.columns:
            df.drop('Unnamed: 0', axis=1, inplace=True)
        # Check if 'start_date' and 'start_time' columns exist
        if 'start_time' not in df.columns:
            raise KeyError("CSV file must contain 'start_time' column.")
        # Handle 'start_date' column: assign default if missing or zero/invalid
        if 'start_date' not in df.columns:
            print("Warning: 'start_date' column missing, assigning default date '2023-01-01'")
            df['start_date'] = '2023-01-01'
        else:
        # Replace zero or invalid dates with default date
            df['start_date'] = df['start_date'].astype(str).str.strip()
            df.loc[(df['start_date'] == '0') | (df['start_date'].isna()) | (df['start_date'] == ''), 'start_date'] = '2023-01-01'
        # Function to convert numeric HHMMSS to timedelta
        def hhmmss_to_timedelta(hhmmss):
            try:
                hhmmss_int = int(float(hhmmss))  # handle floats like 91401.9999
            except:
                return pd.NaT
            hours = hhmmss_int // 10000
            minutes = (hhmmss_int % 10000) // 100
            seconds = hhmmss_int % 100
            return pd.Timedelta(hours=hours, minutes=minutes, seconds=seconds)
        # Convert 'start_time' to timedelta
        df['start_time_timedelta'] = df['start_time'].map(hhmmss_to_timedelta)
            
        # Drop rows with invalid time conversion
        invalid_time_count = df['start_time_timedelta'].isna().sum()
        if invalid_time_count > 0:
            print(f"Warning: Dropping {invalid_time_count} rows due to invalid 'start_time' format.")
            df.dropna(subset=['start_time_timedelta'], inplace=True)
        
        # Combine 'start_date' and 'start_time_timedelta' into a single datetime column
        df['timestamp'] = pd.to_datetime(df['start_date'], errors='coerce') + df['start_time_timedelta']
        # Drop rows with invalid timestamps
        invalid_timestamp_count = df['timestamp'].isna().sum()
        if invalid_timestamp_count > 0:
            print(f"Warning: Dropping {invalid_timestamp_count} rows due to invalid combined timestamp.")
            df.dropna(subset=['timestamp'], inplace=True)
        if df.empty:
            raise ValueError("No valid timestamps found after processing 'start_date' and 'start_time'.")
        
        # Define the column mapping
        column_mapping = {
        'ltp': 'last_price',
        'l1_bid_vwap': 'buy_price',
        'l1_ask_vwap': 'sell_price',
        'l1_bid_vol': 'buy_quantity',
        'l1_ask_vol': 'sell_quantity',
        'volume': 'total_traded_volume'
        }
        df.rename(columns=column_mapping, inplace=True)
        # Select only the columns we need
        required_columns = [
            'timestamp', 'last_price', 'buy_price', 'sell_price',
            'buy_quantity', 'sell_quantity', 'total_traded_volume'
        ]
        df = df[required_columns].copy()
        # Ensure all key columns are numeric
        numeric_cols = [
        'last_price', 'buy_price', 'sell_price',
        'buy_quantity', 'sell_quantity', 'total_traded_volume'
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        # Set the timestamp as the index of the DataFrame
        df.set_index('timestamp', inplace=True)
        print("Data loaded and columns mapped successfully.")
        return df

    def _clean_data(self):
        """Handles missing values."""
        print("Cleaning data...")
        # Data types are now guaranteed to be correct from _load_data.
        # This function now only needs to handle missing values (NaNs).
        
        # Replace 0s with NaN in price columns, as 0 is not a valid price
        for col in ['buy_price', 'sell_price']:
            self.data[col].replace(0, np.nan, inplace=True)
        
        # Forward-fill all missing values (from coercion errors or original NaNs)
        self.data.ffill(inplace=True)
        
        # Drop any remaining NaN rows at the beginning of the dataset
        self.data.dropna(inplace=True)
        
        print(f"Data shape after cleaning: {self.data.shape}")

    def _calculate_technical_indicators(self):
        """Calculates and adds various technical indicators to the DataFrame."""
        print("Calculating technical indicators...")
        
        # 1. Price Volatility (Rolling Standard Deviation)
        self.data['volatility_20_period'] = self.data['last_price'].rolling(window=20).std()

        # 2. Moving Averages
        self.data['ma_5_period'] = self.data['last_price'].rolling(window=5).mean()
        self.data['ma_10_period'] = self.data['last_price'].rolling(window=10).mean()
        self.data['ma_20_period'] = self.data['last_price'].rolling(window=20).mean()

        # 3. Volume-Weighted Average Price (VWAP)
        self.data['price_volume'] = self.data['last_price'] * self.data['total_traded_volume']
        self.data['cumulative_volume'] = self.data['total_traded_volume'].cumsum()
        self.data['cumulative_price_volume'] = self.data['price_volume'].cumsum()
        epsilon = 1e-10  #define epsilon to prevent division by zero
        self.data['vwap'] = self.data['cumulative_price_volume'] / (self.data['cumulative_volume'] + epsilon)
        self.data.drop(columns=['price_volume', 'cumulative_price_volume'], inplace=True)

        # 4. Bid-Ask Spread
        self.data['bid_ask_spread'] = self.data['sell_price'] - self.data['buy_price']

        # 5. Market Momentum (RSI - Relative Strength Index)
        # --- NEW ROBUST IMPLEMENTATION ---
        # Step A: Create a clean, guaranteed-numeric series for the calculation.
        price = pd.to_numeric(self.data['last_price'], errors='coerce')
        
        # Step B: Calculate price changes (delta).
        delta = price.diff(1).astype(float)
        
        # Step C: Separate gains (positive changes) and losses (absolute negative changes).
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Step D: Calculate the average gain and loss using an Exponentially Weighted Moving Average.
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()

        # Step E: Calculate the Relative Strength (RS).
        # A small epsilon is added to the denominator to prevent division by zero.
        epsilon = 1e-10
        rs = avg_gain / (avg_loss + epsilon)

        # Step F: Calculate the RSI.
        self.data['rsi_14_period'] = 100 - (100 / (1 + rs))
        
        # --- FINAL STEP ---
        # Drop any rows with NaN values that were created by the rolling calculations.
        self.data.dropna(inplace=True)
        print("Technical indicators calculated.")

    def _perform_statistical_analysis(self):
        """
        Performs statistical analysis on the processed data.
        """
        print("Performing statistical analysis...")
        self.summary = {}
        
        # Daily Price Volatility (Annualized)
        # Resample to daily returns and calculate standard deviation
        daily_returns = self.data['last_price'].resample('D').last().pct_change()
        # Annualize by multiplying by the square root of trading days in a year (approx 252)
        self.summary['daily_volatility'] = daily_returns.std() * np.sqrt(252)
        
        # Trading Volume Patterns
        self.summary['avg_volume_per_min'] = self.data['total_traded_volume'].resample('1Min').sum().mean()
        
        # Order Flow Imbalance
        self.data['order_flow_imbalance'] = self.data['buy_quantity'] - self.data['sell_quantity']
        self.summary['avg_order_flow_imbalance'] = self.data['order_flow_imbalance'].mean()

        # Correlation Analysis - NOTE: 'volatility' column needs to exist
        # Renaming 'volatility_20_period' for the correlation matrix
        if 'volatility_20_period' in self.data.columns:
            self.data.rename(columns={'volatility_20_period': 'volatility'}, inplace=True)
        self.correlation_matrix = self.data[['last_price', 'total_traded_volume', 'bid_ask_spread', 'volatility', 'order_flow_imbalance']].corr()
        
        print("Statistical analysis complete.")

    def get_summary(self):
        """Returns a dictionary of key statistical measures."""
        return {
            'total_ticks': int(self.data.shape[0]),
            'avg_price': float(self.data['last_price'].mean()),
            'avg_bid_ask_spread': float(self.data['bid_ask_spread'].mean()),
            'daily_volatility_annualized': float(self.summary.get('daily_volatility', 0)),
            'avg_volume_per_min': float(self.summary.get('avg_volume_per_min', 0)),
            'avg_order_flow_imbalance': float(self.summary.get('avg_order_flow_imbalance', 0))
        }

    def get_timeseries_data(self, timeframe='1Min'):
        """Resamples tick data into OHLCV format for a given timeframe."""
        # Ensure columns exist before resampling
        if 'last_price' not in self.data.columns or 'total_traded_volume' not in self.data.columns:
            return []
            
        ohlcv = self.data['last_price'].resample(timeframe).ohlc()
        volume = self.data['total_traded_volume'].resample(timeframe).sum()
        
        ohlcv['volume'] = volume
        ohlcv.dropna(inplace=True)
        
        ohlcv.reset_index(inplace=True)
        # Convert timestamp to seconds for the charting library
        ohlcv['timestamp'] = ohlcv['timestamp'].astype(np.int64) // 10**9
        return ohlcv.to_dict(orient='records')

    def get_orderbook_analysis(self):
        """Returns data related to the order book."""
        cols = ['bid_ask_spread', 'order_flow_imbalance']
        if not all(c in self.data.columns for c in cols):
            return []

        order_flow_data = self.data[cols].resample('1Min').mean()
        order_flow_data.reset_index(inplace=True)
        order_flow_data['timestamp'] = order_flow_data['timestamp'].astype(np.int64) // 10**9
        return order_flow_data.to_dict(orient='records')

    def get_technical_indicators(self):
        """Returns key technical indicators over time."""
        cols = ['rsi_14_period', 'ma_5_period', 'ma_10_period', 'ma_20_period', 'vwap']
        if not all(c in self.data.columns for c in cols):
            return []

        indicators_data = self.data[cols].resample('1Min').mean()
        indicators_data.reset_index(inplace=True)
        indicators_data['timestamp'] = indicators_data['timestamp'].astype(np.int64) // 10**9
        return indicators_data.to_dict(orient='records')

