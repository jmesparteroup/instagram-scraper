#!/usr/bin/env python3
"""
Test script for Instagram Scraper API
"""

import requests
import json
import sys

API_BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the API server is running.")
        return False
    except Exception as e:
        print(f"❌ Error during health check: {str(e)}")
        return False
    return True

def test_scrape_endpoint(instagram_url):
    """Test the scrape endpoint with a given Instagram URL"""
    print(f"🔍 Testing scrape endpoint with URL: {instagram_url}")
    
    payload = {
        "instagram_url": instagram_url
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/scrape", 
            json=payload, 
            headers=headers,
            timeout=60  # 60 second timeout
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Scraping successful!")
                print("\n📊 Extracted Data:")
                print(json.dumps(data.get("data"), indent=2, ensure_ascii=False))
            else:
                print(f"❌ Scraping failed: {data.get('error')}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Raw response: {response.text}")
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Instagram scraping can take some time.")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the API server is running.")
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")

def test_invalid_url():
    """Test with an invalid URL to check error handling"""
    print("🔍 Testing error handling with invalid URL...")
    
    payload = {
        "instagram_url": "https://invalid-url.com"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/scrape", 
            json=payload, 
            headers=headers
        )
        
        if response.status_code == 400:
            data = response.json()
            print("✅ Error handling works correctly")
            print(f"Error message: {data.get('error')}")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during invalid URL test: {str(e)}")

def main():
    """Main test function"""
    print("🚀 Instagram Scraper API Test Suite")
    print("=" * 50)
    
    # Test health check first
    if not test_health_check():
        print("\n❌ Health check failed. Exiting.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Test invalid URL handling
    test_invalid_url()
    
    print("\n" + "=" * 50)
    
    # Test with a real Instagram URL if provided
    if len(sys.argv) > 1:
        instagram_url = sys.argv[1]
        test_scrape_endpoint(instagram_url)
    else:
        print("📝 To test with a real Instagram URL, run:")
        print("python test_api.py 'https://www.instagram.com/p/XXXXXXXXX/'")
        print("\n⚠️ Note: You need a valid OpenAI API key in your .env file")
        print("⚠️ Note: Some Instagram posts may not be accessible due to privacy settings")
    
    print("\n" + "=" * 50)
    print("🎉 Test suite completed!")

if __name__ == "__main__":
    main() 