1. Project Structure Setup
Create the project directory:

mkdir bnp-stock-predictor
cd bnp-stock-predictor
Create the following folder structure:
```
bnp-stock-predictor/
├── backend/
├── frontend/
└── sample_bnp_data.csv
```
2. Backend Setup (FastAPI + Prophet)
# Create backend directory
mkdir backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.110.1
uvicorn==0.25.0
python-dotenv>=1.0.1
pymongo==4.5.0
pydantic>=2.6.4
motor==3.3.1
prophet>=1.1.4
scikit-learn>=1.4.0
plotly>=5.17.0
pandas>=2.2.0
numpy>=1.26.0
python-multipart>=0.0.9
EOF

# Install dependencies
pip install -r requirements.txt
Create backend/server.py - Copy the complete server.py code from the implementation above, or download it from the working app.

Create backend/.env:

cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=bnp_stock_predictor
CORS_ORIGINS=http://localhost:3000
EOF
3. Frontend Setup (React)
# Go back to root directory
cd ..

# Create React app
npx create-react-app frontend
cd frontend

# Install additional dependencies
npm install recharts axios lucide-react

# Install shadcn/ui components
npx shadcn-ui@latest init
npx shadcn-ui@latest add card button input label badge tabs toast toaster

# Or with yarn:
yarn add recharts axios lucide-react
Create frontend/.env:

cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
EOF
Replace frontend/src/App.js with the complete App.js code from the implementation above.

Replace frontend/src/App.css with the complete App.css code from the implementation above.

4. Database Setup (MongoDB)
Option A: Local MongoDB

# Install MongoDB locally (varies by OS)
# On macOS with Homebrew:
brew install mongodb-community

# Start MongoDB service
brew services start mongodb-community

# On Ubuntu/Debian:
sudo apt install mongodb
sudo systemctl start mongodb
Option B: MongoDB Atlas (Cloud)

Sign up at MongoDB Atlas
Create a free cluster
Get connection string
Update backend/.env with your Atlas connection string
5. Sample Data
Create sample_bnp_data.csv in the root directory:

Date,Open,Higher,Lower,Last,Volume
2024-01-01,65.50,66.20,65.10,65.80,1250000
2024-01-02,65.80,66.40,65.30,66.10,1180000
2024-01-03,66.10,66.50,65.70,66.20,1220000
2024-01-04,66.20,66.80,65.90,66.45,1300000
2024-01-05,66.45,67.10,66.20,66.90,1350000
2024-01-08,66.90,67.30,66.50,67.00,1100000
2024-01-09,67.00,67.60,66.80,67.25,1200000
2024-01-10,67.25,67.50,66.90,67.15,1150000
2024-01-11,67.15,67.70,66.85,67.40,1280000
2024-01-12,67.40,68.00,67.10,67.85,1320000
2024-01-15,67.85,68.20,67.50,68.10,1190000
2024-01-16,68.10,68.40,67.80,68.25,1240000
2024-01-17,68.25,68.60,67.95,68.30,1210000
2024-01-18,68.30,68.70,68.00,68.50,1330000
2024-01-19,68.50,69.10,68.20,68.95,1410000
2024-01-22,68.95,69.30,68.60,69.15,1200000
2024-01-23,69.15,69.50,68.85,69.20,1350000
2024-01-24,69.20,69.40,68.90,69.05,1180000
2024-01-25,69.05,69.60,68.75,69.35,1290000
2024-01-26,69.35,69.80,69.10,69.55,1320000
2024-01-29,69.55,70.00,69.25,69.75,1250000
2024-01-30,69.75,70.20,69.40,69.90,1380000
2024-01-31,69.90,70.30,69.60,70.10,1400000
2024-02-01,70.10,70.50,69.80,70.25,1300000
2024-02-02,70.25,70.60,70.00,70.40,1220000
2024-02-05,70.40,70.80,70.15,70.55,1340000
2024-02-06,70.55,70.90,70.25,70.70,1280000
2024-02-07,70.70,71.10,70.45,70.85,1320000
2024-02-08,70.85,71.20,70.60,71.00,1350000
2024-02-09,71.00,71.40,70.75,71.15,1240000
2024-02-12,71.15,71.50,70.90,71.30,1300000
2024-02-13,71.30,71.60,71.05,71.45,1180000
2024-02-14,71.45,71.80,71.20,71.60,1250000
2024-02-15,71.60,71.90,71.35,71.75,1320000
2024-02-16,71.75,72.10,71.50,71.90,1380000
2024-02-19,71.90,72.30,71.65,72.05,1220000
2024-02-20,72.05,72.40,71.80,72.20,1340000
2024-02-21,72.20,72.50,71.95,72.35,1280000
2024-02-22,72.35,72.70,72.10,72.50,1300000
2024-02-23,72.50,72.80,72.25,72.65,1350000
2024-02-26,72.65,73.00,72.40,72.80,1180000
2024-02-27,72.80,73.20,72.55,72.95,1250000
2024-02-28,72.95,73.30,72.70,73.10,1320000
2024-02-29,73.10,73.40,72.85,73.25,1280000
2024-03-01,73.25,73.60,73.00,73.40,1340000
2024-03-04,73.40,73.70,73.15,73.55,1200000
2024-03-05,73.55,73.90,73.30,73.70,1280000
2024-03-06,73.70,74.00,73.45,73.85,1320000
2024-03-07,73.85,74.20,73.60,74.00,1350000
2024-03-08,74.00,74.30,73.75,74.15,1240000
6. Running the Application
Terminal 1 - Backend:

cd backend
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start FastAPI server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
Terminal 2 - Frontend:

cd frontend
npm start
# or
yarn start
Terminal 3 - MongoDB (if local):

# Start MongoDB (if not running as service)
mongod
7. Access the Application
Frontend: http://localhost:3000
Backend API: http://localhost:8001
API Documentation: http://localhost:8001/docs
8. Testing the Application
Upload the sample CSV file from the root directory
Generate predictions with 14-day forecast
View the interactive chart with historical and forecast data
Download the results as CSV
9. Troubleshooting
Common Issues:

Python/Prophet Installation:

# If Prophet installation fails, try:
pip install pystan==2.19.1.1
pip install prophet
MongoDB Connection:

# Check if MongoDB is running:
mongo --eval "db.adminCommand('ismaster')"
Port Conflicts:

Change ports in .env files if 3000/8001 are occupied
Update CORS_ORIGINS accordingly
Memory Issues:

# If React build fails due to memory:
export NODE_OPTIONS="--max-old-space-size=4096"
npm start
10. Project Structure Final Check
Your final directory should look like:

bnp-stock-predictor/
├── backend/
│   ├── venv/
│   ├── server.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── node_modules/
│   ├── src/
│   │   ├── App.js
│   │   ├── App.css
│   │   └── components/ui/
│   ├── package.json
│   └── .env
└── sample_bnp_data.csv
That's it! You should now have the BNP Paribas Stock Price Predictor running locally on your machine. 🚀
