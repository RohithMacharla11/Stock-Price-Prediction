from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import io
import tempfile
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import plotly.graph_objects as go
import plotly.utils
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StockData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    filename: str
    upload_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_points: int
    date_range: dict

class PredictionRequest(BaseModel):
    data_id: str
    forecast_days: int = Field(ge=7, le=30)
    
class PredictionResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data_id: str
    forecast_days: int
    created_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rmse: float
    mape: float
    chart_data: dict

def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
            elif isinstance(value, list):
                data[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
    return data

def parse_from_mongo(data):
    """Parse ISO string dates back to datetime objects"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and 'timestamp' in key:
                try:
                    data[key] = datetime.fromisoformat(value)
                except:
                    pass
            elif isinstance(value, dict):
                data[key] = parse_from_mongo(value)
    return data

@api_router.post("/upload-stock-data")
async def upload_stock_data(file: UploadFile = File(...), symbol: str = "BNP"):
    try:
        # Read the uploaded CSV file
        contents = await file.read()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.csv') as temp_file:
            temp_file.write(contents)
            temp_file_path = temp_file.name
        
        # Read CSV with pandas  
        df = pd.read_csv(temp_file_path)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        # Validate required columns
        required_columns = ['Date', 'Open', 'Higher', 'Lower', 'Last', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Convert Date column to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Validate data
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        if len(df) < 30:
            raise HTTPException(status_code=400, detail="Need at least 30 data points for meaningful predictions")
        
        # Create stock data record
        stock_data = StockData(
            symbol=symbol,
            filename=file.filename,
            data_points=len(df),
            date_range={
                "start_date": df['Date'].min().isoformat(),
                "end_date": df['Date'].max().isoformat()
            }
        )
        
        # Store the dataframe data in MongoDB
        df_dict = df.to_dict('records')
        # Convert datetime objects to strings for MongoDB
        for record in df_dict:
            record['Date'] = record['Date'].isoformat()
        
        stock_dict = prepare_for_mongo(stock_data.dict())
        stock_dict['data'] = df_dict
        
        await db.stock_data.insert_one(stock_dict)
        
        return {
            "message": "File uploaded successfully",
            "data_id": stock_data.id,
            "symbol": symbol,
            "data_points": len(df),
            "date_range": stock_data.date_range
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@api_router.post("/predict")
async def predict_stock_prices(request: PredictionRequest):
    try:
        # Retrieve stock data from MongoDB
        stock_record = await db.stock_data.find_one({"id": request.data_id})
        if not stock_record:
            raise HTTPException(status_code=404, detail="Stock data not found")
        
        # Convert back to DataFrame
        df_data = stock_record['data']
        df = pd.DataFrame(df_data)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Prepare data for Prophet (rename columns to 'ds' and 'y')
        prophet_df = df[['Date', 'Last']].copy()
        prophet_df.columns = ['ds', 'y']
        prophet_df = prophet_df.sort_values('ds')
        
        # Split data for validation (use last 20% for testing)
        split_idx = int(len(prophet_df) * 0.8)
        train_df = prophet_df.iloc[:split_idx]
        validation_df = prophet_df.iloc[split_idx:]
        
        # Initialize and fit Prophet model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        
        model.fit(train_df)
        
        # Create future dataframe for validation period
        validation_future = model.make_future_dataframe(periods=len(validation_df))
        validation_forecast = model.predict(validation_future)
        
        # Calculate metrics on validation data
        validation_predictions = validation_forecast.tail(len(validation_df))
        rmse = np.sqrt(mean_squared_error(validation_df['y'], validation_predictions['yhat']))
        mape = mean_absolute_percentage_error(validation_df['y'], validation_predictions['yhat']) * 100
        
        # Now make future predictions
        future = model.make_future_dataframe(periods=request.forecast_days)
        forecast = model.predict(future)
        
        # Prepare chart data
        historical_data = {
            'dates': prophet_df['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'actual': prophet_df['y'].tolist()
        }
        
        # Get forecast data (only future predictions)
        future_forecast = forecast.tail(request.forecast_days)
        forecast_data = {
            'dates': future_forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'forecast': future_forecast['yhat'].tolist(),
            'lower_bound': future_forecast['yhat_lower'].tolist(),
            'upper_bound': future_forecast['yhat_upper'].tolist()
        }
        
        # Create chart data for frontend
        chart_data = {
            'historical': historical_data,
            'forecast': forecast_data,
            'symbol': stock_record['symbol']
        }
        
        # Create prediction result
        result = PredictionResult(
            data_id=request.data_id,
            forecast_days=request.forecast_days,
            rmse=round(rmse, 4),
            mape=round(mape, 4),
            chart_data=chart_data
        )
        
        # Store forecast results for download
        forecast_df = future_forecast.copy()
        forecast_df['ds'] = forecast_df['ds'].dt.strftime('%Y-%m-%d')
        forecast_dict = forecast_df.to_dict('records')
        
        result_dict = prepare_for_mongo(result.dict())
        result_dict['forecast_data'] = forecast_dict
        
        await db.predictions.insert_one(result_dict)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error making predictions: {str(e)}")

@api_router.get("/download-forecast/{prediction_id}")
async def download_forecast(prediction_id: str):
    try:
        # Retrieve prediction from MongoDB
        prediction = await db.predictions.find_one({"id": prediction_id})
        if not prediction:
            raise HTTPException(status_code=404, detail="Prediction not found")
        
        # Convert forecast data to CSV
        forecast_df = pd.DataFrame(prediction['forecast_data'])
        
        # Create CSV string
        csv_buffer = io.StringIO()
        forecast_df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Return as downloadable file
        return StreamingResponse(
            io.BytesIO(csv_content.encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=forecast_{prediction_id}.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading forecast: {str(e)}")

@api_router.get("/predictions")
async def get_predictions():
    """Get all predictions for listing"""
    try:
        predictions = await db.predictions.find().to_list(100)
        return [parse_from_mongo(pred) for pred in predictions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving predictions: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()