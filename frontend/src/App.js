import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Upload, TrendingUp, Download, BarChart3, AlertCircle } from 'lucide-react';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [uploadedData, setUploadedData] = useState(null);
  const [predictionResult, setPredictionResult] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isPredicting, setIsPredicting] = useState(false);
  const [forecastDays, setForecastDays] = useState(14);
  const [stockSymbol, setStockSymbol] = useState('BNP');
  const { toast } = useToast();

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      toast({
        title: "Invalid File Type",
        description: "Please upload a CSV file.",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('symbol', stockSymbol);

    try {
      const response = await axios.post(`${API}/upload-stock-data`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setUploadedData(response.data);
      setPredictionResult(null);
      toast({
        title: "Upload Successful",
        description: `Uploaded ${response.data.data_points} data points for ${response.data.symbol}`,
      });
    } catch (error) {
      toast({
        title: "Upload Failed",
        description: error.response?.data?.detail || "Error uploading file",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handlePredict = async () => {
    if (!uploadedData) return;

    setIsPredicting(true);
    try {
      const response = await axios.post(`${API}/predict`, {
        data_id: uploadedData.data_id,
        forecast_days: forecastDays,
      });
      
      setPredictionResult(response.data);
      toast({
        title: "Prediction Complete",
        description: `Generated ${forecastDays}-day forecast with RMSE: ${response.data.rmse}`,
      });
    } catch (error) {
      toast({
        title: "Prediction Failed",
        description: error.response?.data?.detail || "Error generating predictions",
        variant: "destructive",
      });
    } finally {
      setIsPredicting(false);
    }
  };

  const handleDownload = async () => {
    if (!predictionResult) return;

    try {
      const response = await axios.get(`${API}/download-forecast/${predictionResult.id}`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `forecast_${predictionResult.id}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast({
        title: "Download Complete",
        description: "Forecast data downloaded successfully",
      });
    } catch (error) {
      toast({
        title: "Download Failed",
        description: "Error downloading forecast data",
        variant: "destructive",
      });
    }
  };

  const createChart = () => {
    if (!predictionResult) return null;

    const { historical, forecast, symbol } = predictionResult.chart_data;
    
    // Combine historical and forecast data for the chart
    const chartData = [];
    
    // Add historical data
    historical.dates.forEach((date, index) => {
      chartData.push({
        date: date,
        actual: historical.actual[index],
        type: 'historical'
      });
    });
    
    // Add forecast data
    forecast.dates.forEach((date, index) => {
      chartData.push({
        date: date,
        forecast: forecast.forecast[index],
        upper: forecast.upper_bound[index],
        lower: forecast.lower_bound[index],
        type: 'forecast'
      });
    });

    return (
      <ResponsiveContainer width="100%" height={500}>
        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip 
            labelFormatter={(value) => `Date: ${value}`}
            formatter={(value, name) => [
              value ? value.toFixed(2) : 'N/A', 
              name === 'actual' ? 'Historical Price' : 
              name === 'forecast' ? 'Forecast Price' :
              name === 'upper' ? 'Upper Bound' : 'Lower Bound'
            ]}
          />
          <Legend />
          
          {/* Historical prices */}
          <Line 
            type="monotone" 
            dataKey="actual" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={false}
            name="Historical Price"
            connectNulls={false}
          />
          
          {/* Forecast line */}
          <Line 
            type="monotone" 
            dataKey="forecast" 
            stroke="#ef4444" 
            strokeWidth={2}
            dot={false}
            name="Forecast"
            connectNulls={false}
          />
          
          {/* Upper bound line */}
          <Line 
            type="monotone" 
            dataKey="upper" 
            stroke="rgba(239, 68, 68, 0.3)" 
            strokeWidth={1}
            dot={false}
            name="Upper Bound"
            connectNulls={false}
          />
          
          {/* Lower bound line */}
          <Line 
            type="monotone" 
            dataKey="lower" 
            stroke="rgba(239, 68, 68, 0.3)" 
            strokeWidth={1}
            dot={false}
            name="Lower Bound"
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-2">
            BNP Paribas Stock Price Predictor
          </h1>
          <p className="text-slate-600 text-lg">
            Advanced time series forecasting using Prophet ML model
          </p>
        </div>

        <Tabs defaultValue="upload" className="w-full max-w-6xl mx-auto">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload size={16} />
              Upload Data
            </TabsTrigger>
            <TabsTrigger value="predict" className="flex items-center gap-2">
              <TrendingUp size={16} />
              Forecast
            </TabsTrigger>
            <TabsTrigger value="results" className="flex items-center gap-2">
              <BarChart3 size={16} />
              Results
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload size={20} />
                  Upload Stock Data
                </CardTitle>
                <CardDescription>
                  Upload a CSV file with columns: Date, Open, Higher, Lower, Last, Volume
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="symbol">Stock Symbol</Label>
                  <Input
                    id="symbol"
                    value={stockSymbol}
                    onChange={(e) => setStockSymbol(e.target.value)}
                    placeholder="Enter stock symbol (e.g., BNP)"
                    className="max-w-xs"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="file">CSV File</Label>
                  <Input
                    id="file"
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    disabled={isUploading}
                    className="max-w-md"
                  />
                </div>

                {isUploading && (
                  <div className="flex items-center gap-2 text-blue-600">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
                    Uploading and processing file...
                  </div>
                )}

                {uploadedData && (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <h3 className="font-semibold text-green-800 mb-2">Upload Successful!</h3>
                    <div className="space-y-1 text-sm text-green-700">
                      <p><strong>Symbol:</strong> {uploadedData.symbol}</p>
                      <p><strong>Data Points:</strong> {uploadedData.data_points}</p>
                      <p><strong>Date Range:</strong> {uploadedData.date_range.start_date} to {uploadedData.date_range.end_date}</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="predict" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp size={20} />
                  Generate Forecast
                </CardTitle>
                <CardDescription>
                  Configure and generate stock price predictions using Prophet
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {!uploadedData ? (
                  <div className="flex items-center gap-2 text-amber-600 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <AlertCircle size={20} />
                    Please upload stock data first before generating forecasts
                  </div>
                ) : (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="days">Forecast Days (7-30)</Label>
                      <Input
                        id="days"
                        type="number"
                        min="7"
                        max="30"
                        value={forecastDays}
                        onChange={(e) => setForecastDays(parseInt(e.target.value))}
                        className="max-w-xs"
                      />
                    </div>

                    <Button 
                      onClick={handlePredict} 
                      disabled={isPredicting}
                      className="w-full sm:w-auto"
                    >
                      {isPredicting ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                          Generating Forecast...
                        </>
                      ) : (
                        <>
                          <TrendingUp size={16} className="mr-2" />
                          Generate Forecast
                        </>
                      )}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="results" className="space-y-6">
            {!predictionResult ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <BarChart3 size={48} className="mx-auto text-slate-400 mb-4" />
                  <p className="text-slate-600">No forecast results yet. Generate a prediction first.</p>
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">RMSE</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{predictionResult.rmse}</div>
                      <p className="text-xs text-slate-600">Root Mean Square Error</p>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">MAPE</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{predictionResult.mape}%</div>
                      <p className="text-xs text-slate-600">Mean Absolute Percentage Error</p>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">Forecast Days</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{predictionResult.forecast_days}</div>
                      <p className="text-xs text-slate-600">Days predicted</p>
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>Forecast Chart</span>
                      <Button onClick={handleDownload} variant="outline" size="sm">
                        <Download size={16} className="mr-2" />
                        Download CSV
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {createChart()}
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>
        </Tabs>
      </div>
      <Toaster />
    </div>
  );
}

export default App;