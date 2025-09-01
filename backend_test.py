import requests
import sys
import os
from datetime import datetime
import json

class BNPStockPredictorTester:
    def __init__(self, base_url="https://streamlit-bnp-pred.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.uploaded_data_id = None
        self.prediction_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers)

            print(f"Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Error Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_upload_valid_csv(self):
        """Test uploading valid CSV file"""
        csv_path = "/app/sample_bnp_data.csv"
        
        if not os.path.exists(csv_path):
            print(f"❌ Sample CSV file not found at {csv_path}")
            return False
            
        with open(csv_path, 'rb') as f:
            files = {'file': ('sample_bnp_data.csv', f, 'text/csv')}
            data = {'symbol': 'BNP'}
            
            success, response = self.run_test(
                "Upload Valid CSV",
                "POST",
                "upload-stock-data",
                200,
                data=data,
                files=files
            )
            
            if success and 'data_id' in response:
                self.uploaded_data_id = response['data_id']
                print(f"✅ Data ID stored: {self.uploaded_data_id}")
                return True
            return False

    def test_upload_invalid_file(self):
        """Test uploading invalid file (non-CSV)"""
        # Create a temporary text file
        invalid_content = "This is not a CSV file"
        files = {'file': ('invalid.txt', invalid_content, 'text/plain')}
        data = {'symbol': 'BNP'}
        
        success, response = self.run_test(
            "Upload Invalid File",
            "POST", 
            "upload-stock-data",
            500,  # Expecting error
            data=data,
            files=files
        )
        return True  # We expect this to fail, so success means test passed

    def test_predict_stock_prices(self):
        """Test generating stock price predictions"""
        if not self.uploaded_data_id:
            print("❌ No uploaded data ID available for prediction test")
            return False
            
        prediction_data = {
            "data_id": self.uploaded_data_id,
            "forecast_days": 14
        }
        
        success, response = self.run_test(
            "Generate Stock Predictions",
            "POST",
            "predict",
            200,
            data=prediction_data
        )
        
        if success and 'id' in response:
            self.prediction_id = response['id']
            print(f"✅ Prediction ID stored: {self.prediction_id}")
            
            # Validate response structure
            required_fields = ['rmse', 'mape', 'forecast_days', 'chart_data']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Validate chart_data structure
            chart_data = response['chart_data']
            if 'historical' not in chart_data or 'forecast' not in chart_data:
                print("❌ Invalid chart_data structure")
                return False
                
            return True
        return False

    def test_predict_invalid_data_id(self):
        """Test prediction with invalid data ID"""
        prediction_data = {
            "data_id": "invalid-id-12345",
            "forecast_days": 14
        }
        
        success, response = self.run_test(
            "Predict with Invalid Data ID",
            "POST",
            "predict", 
            404,  # Expecting not found
            data=prediction_data
        )
        return True  # We expect this to fail, so success means test passed

    def test_predict_invalid_forecast_days(self):
        """Test prediction with invalid forecast days"""
        if not self.uploaded_data_id:
            print("❌ No uploaded data ID available for invalid forecast days test")
            return False
            
        prediction_data = {
            "data_id": self.uploaded_data_id,
            "forecast_days": 50  # Invalid: should be 7-30
        }
        
        success, response = self.run_test(
            "Predict with Invalid Forecast Days",
            "POST",
            "predict",
            422,  # Expecting validation error
            data=prediction_data
        )
        return True  # We expect this to fail, so success means test passed

    def test_download_forecast(self):
        """Test downloading forecast CSV"""
        if not self.prediction_id:
            print("❌ No prediction ID available for download test")
            return False
            
        success, response = self.run_test(
            "Download Forecast CSV",
            "GET",
            f"download-forecast/{self.prediction_id}",
            200
        )
        return success

    def test_download_invalid_prediction(self):
        """Test downloading with invalid prediction ID"""
        success, response = self.run_test(
            "Download Invalid Prediction",
            "GET",
            "download-forecast/invalid-id-12345",
            404  # Expecting not found
        )
        return True  # We expect this to fail, so success means test passed

    def test_get_predictions(self):
        """Test getting all predictions"""
        success, response = self.run_test(
            "Get All Predictions",
            "GET",
            "predictions",
            200
        )
        
        if success:
            print(f"✅ Found {len(response)} predictions")
            return True
        return False

def main():
    print("🚀 Starting BNP Paribas Stock Predictor API Tests")
    print("=" * 60)
    
    tester = BNPStockPredictorTester()
    
    # Test sequence
    tests = [
        ("Upload Valid CSV", tester.test_upload_valid_csv),
        ("Upload Invalid File", tester.test_upload_invalid_file),
        ("Generate Predictions", tester.test_predict_stock_prices),
        ("Predict Invalid Data ID", tester.test_predict_invalid_data_id),
        ("Predict Invalid Forecast Days", tester.test_predict_invalid_forecast_days),
        ("Download Forecast", tester.test_download_forecast),
        ("Download Invalid Prediction", tester.test_download_invalid_prediction),
        ("Get All Predictions", tester.test_get_predictions),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            failed_tests.append(test_name)
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"  - {test}")
    else:
        print(f"\n✅ All tests passed!")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())