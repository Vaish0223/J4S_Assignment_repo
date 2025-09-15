import React, { useState, useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

// --- Configuration ---
const API_BASE_URL = 'http://127.0.0.1:5000';

// --- Helper Components ---

// Displays a single metric card
const MetricCard = ({ title, value, change, isCurrency = false }) => (
  <div className="bg-gray-800 p-4 rounded-lg shadow-lg text-center transform hover:scale-105 transition-transform duration-300">
    <h3 className="text-sm text-gray-400 font-medium">{title}</h3>
    <p className="text-2xl font-bold text-white mt-1">
      {isCurrency ? `₹${value}` : value}
    </p>
    {change && (
      <p className={`text-xs mt-1 ${change.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
        {change}
      </p>
    )}
  </div>
);

// Navigation tabs to switch between different chart views
const NavigationTabs = ({ activeTab, setActiveTab }) => {
  const tabs = ['Price (OHLCV)', 'Order Flow', 'Indicators', 'Heatmap'];
  return (
    <div className="mb-4 flex space-x-2 bg-gray-900 p-2 rounded-lg">
      {tabs.map(tab => (
        <button
          key={tab}
          onClick={() => setActiveTab(tab)}
          className={`px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200 ${
            activeTab === tab 
            ? 'bg-blue-600 text-white shadow-md' 
            : 'text-gray-300 hover:bg-gray-700'
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
};


// --- Charting Component ---

const ChartComponent = ({ data, chartType }) => {
    const chartContainerRef = useRef();
    const chartRef = useRef();

    useEffect(() => {
        if (!data || data.length === 0) return;

        // Clean up previous chart instance before creating a new one
        if (chartRef.current) {
            chartRef.current.remove();
            chartRef.current = null;
        }

        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 400,
            layout: {
                backgroundColor: '#1f2937', // gray-800
                textColor: 'rgba(255, 255, 255, 0.9)',
            },
            grid: {
                vertLines: { color: '#374151' }, // gray-700
                horzLines: { color: '#374151' },
            },
            crosshair: { mode: 0 },
            rightPriceScale: { borderColor: '#4b5563' }, // gray-600
            timeScale: { borderColor: '#4b5563' },
        });
        chartRef.current = chart;

        let series;
        let formattedData;

        switch (chartType) {
            case 'Price (OHLCV)':
                series = chart.addCandlestickSeries({
                    upColor: '#22c55e', // green-500
                    downColor: '#ef4444', // red-500
                    borderDownColor: '#ef4444',
                    borderUpColor: '#22c55e',
                    wickDownColor: '#ef4444',
                    wickUpColor: '#22c55e',
                });
                const volumeSeries = chart.addHistogramSeries({
                    color: '#3b82f6',
                    priceFormat: { type: 'volume' },
                    priceScaleId: 'volume_scale',
                });
                chart.priceScale('volume_scale').applyOptions({
                    scaleMargins: { top: 0.7, bottom: 0 },
                });
                
                formattedData = data.map(d => ({ time: d.timestamp, open: d.open, high: d.high, low: d.low, close: d.close }));
                const volumeData = data.map(d => ({ time: d.timestamp, value: d.volume, color: d.close > d.open ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)' }));
                
                series.setData(formattedData);
                volumeSeries.setData(volumeData);
                break;
            
            case 'Order Flow':
                series = chart.addHistogramSeries({ color: '#8b5cf6' }); // violet-500
                formattedData = data.map(d => ({ time: d.timestamp, value: d.order_flow_imbalance, color: d.order_flow_imbalance > 0 ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)' }));
                series.setData(formattedData);
                break;
            
            case 'Indicators':
                const rsiSeries = chart.addLineSeries({ color: '#eab308', lineWidth: 2, priceScaleId: 'rsi_scale' }); // yellow-500
                const vwapSeries = chart.addLineSeries({ color: '#3b82f6', lineWidth: 2 }); // blue-500
                 
                chart.priceScale('rsi_scale').applyOptions({
                    scaleMargins: { top: 0.8, bottom: 0 },
                });

                const rsiData = data.map(d => ({ time: d.timestamp, value: d.rsi }));
                const vwapData = data.map(d => ({ time: d.timestamp, value: d.vwap }));
                
                rsiSeries.setData(rsiData);
                vwapSeries.setData(vwapData);
                break;

            case 'Heatmap':
                // Note: Lightweight-charts doesn't have a native heatmap. 
                // This is a simplified bar chart representation of volume.
                series = chart.addHistogramSeries({ color: '#14b8a6' }); // teal-500
                formattedData = data.map(d => ({ time: d.timestamp, value: d.volume }));
                series.setData(formattedData);
                break;

            default:
                break;
        }

        chart.timeScale().fitContent();

        const handleResize = () => chart.resize(chartContainerRef.current.clientWidth, 400);
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };

    }, [data, chartType]);

    return <div ref={chartContainerRef} className="w-full h-[400px]" />;
};


// --- Main Dashboard Layout ---

const Dashboard = ({ summary, timeseries, orderbook, indicators }) => {
  const [activeTab, setActiveTab] = useState('Price (OHLCV)');

  const getChartData = () => {
    switch (activeTab) {
      case 'Price (OHLCV)':
        return timeseries;
      case 'Order Flow':
        return orderbook;
      case 'Indicators':
        return indicators;
      case 'Heatmap':
        // Using timeseries data's volume for the heatmap representation
        return timeseries;
      default:
        return [];
    }
  };

  return (
    <div className="p-4 md:p-6">
      <h1 className="text-3xl font-bold text-white mb-2">Reliance Industries (RELIANCE)</h1>
      <p className="text-md text-gray-400 mb-6">High-Frequency Trading Analysis</p>
      
      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <MetricCard title="Last Price" value={summary.avg_price?.toFixed(2)} isCurrency={true} />
        <MetricCard title="Total Ticks" value={summary.total_ticks?.toLocaleString()} />
        <MetricCard title="Avg. Spread" value={summary.avg_bid_ask_spread?.toFixed(4)} isCurrency={true} />
        <MetricCard title="Volatility (Ann.)" value={`${(summary.daily_volatility_annualized * 100)?.toFixed(2)}%`} />
        <MetricCard title="Avg. Volume/Min" value={Math.round(summary.avg_volume_per_min)?.toLocaleString()} />
        <MetricCard title="Order Flow Imbalance" value={summary.avg_order_flow_imbalance?.toFixed(2)} />
      </div>

      {/* Main Charting Area */}
      <div className="bg-gray-900 p-4 rounded-lg shadow-2xl">
        <NavigationTabs activeTab={activeTab} setActiveTab={setActiveTab} />
        <div className="mt-4">
            <ChartComponent data={getChartData()} chartType={activeTab} />
        </div>
      </div>
    </div>
  );
};


// --- App Entry Point ---

function App() {
  // State for all our data from the backend
  const [summaryData, setSummaryData] = useState({});
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [orderbookData, setOrderbookData] = useState([]);
  const [indicatorsData, setIndicatorsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // useEffect to fetch data when the component mounts
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [summaryRes, timeseriesRes, orderbookRes, indicatorsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/stock/summary`),
          fetch(`${API_BASE_URL}/api/stock/timeseries/5Min`), // Default timeframe
          fetch(`${API_BASE_URL}/api/stock/orderbook`),
          fetch(`${API_BASE_URL}/api/stock/indicators`)
        ]);

        if (!summaryRes.ok || !timeseriesRes.ok || !orderbookRes.ok || !indicatorsRes.ok) {
            throw new Error('Network response was not ok for one or more endpoints.');
        }

        const summary = await summaryRes.json();
        const timeseries = await timeseriesRes.json();
        const orderbook = await orderbookRes.json();
        const indicators = await indicatorsRes.json();

        setSummaryData(summary);
        setTimeSeriesData(timeseries);
        setOrderbookData(orderbook);
        setIndicatorsData(indicators);
        setError(null);

      } catch (err) {
        console.error("Failed to fetch data:", err);
        setError("Failed to connect to the backend. Please ensure the Python Flask server is running and accessible.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []); // Empty dependency array means this runs once on mount

  return (
    <div className="bg-gray-900 min-h-screen text-gray-100 font-sans">
      <main>
        {loading && (
          <div className="flex justify-center items-center h-screen">
            <div className="text-center">
                <p className="text-xl font-semibold">Loading Dashboard...</p>
                <p className="text-gray-400 mt-2">Connecting to analysis backend...</p>
            </div>
          </div>
        )}
        {error && (
            <div className="flex justify-center items-center h-screen">
                <div className="bg-red-900 border border-red-400 text-red-100 px-4 py-3 rounded-lg relative max-w-md text-center">
                    <strong className="font-bold block">Error!</strong>
                    <span className="block sm:inline">{error}</span>
                </div>
            </div>
        )}
        {!loading && !error && (
          <Dashboard 
            summary={summaryData}
            timeseries={timeSeriesData}
            orderbook={orderbookData}
            indicators={indicatorsData}
          />
        )}
      </main>
    </div>
  );
}

export default App;

