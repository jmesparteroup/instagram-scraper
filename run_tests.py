#!/usr/bin/env python3
"""
Test runner for Instagram Scraper API
Provides easy commands to run different test suites
"""

import os
import sys
import subprocess
import argparse

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🏃‍♂️ {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"\n✅ {description} completed successfully")
        return True

def main():
    parser = argparse.ArgumentParser(description="Instagram Scraper API Test Runner")
    parser.add_argument(
        'test_type', 
        nargs='?', 
        default='all',
        choices=['all', 'unit', 'api', 'scraper', 'models', 'integration', 'coverage'],
        help='Type of tests to run'
    )
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-k', '--keyword', help='Run tests matching keyword')
    parser.add_argument('--no-cov', action='store_true', help='Skip coverage report')
    
    args = parser.parse_args()
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("🚀 Instagram Scraper API Test Runner")
    print("=" * 50)
    
    # Base pytest command
    pytest_cmd = ['python', '-m', 'pytest']
    
    if args.verbose:
        pytest_cmd.extend(['-v', '-s'])
    
    if args.keyword:
        pytest_cmd.extend(['-k', args.keyword])
    
    # Add coverage if not disabled
    if not args.no_cov and args.test_type != 'coverage':
        pytest_cmd.extend(['--cov=.', '--cov-report=term-missing'])
    
    success = True
    
    if args.test_type == 'all':
        # Run all tests
        success = run_command(pytest_cmd + ['tests/'], "Running all tests")
        
    elif args.test_type == 'unit':
        # Run unit tests (models and scraper)
        success = run_command(pytest_cmd + ['tests/test_models.py', 'tests/test_scraper.py'], "Running unit tests")
        
    elif args.test_type == 'api':
        # Run API tests
        success = run_command(pytest_cmd + ['tests/test_api.py'], "Running API tests")
        
    elif args.test_type == 'scraper':
        # Run scraper tests
        success = run_command(pytest_cmd + ['tests/test_scraper.py'], "Running scraper tests")
        
    elif args.test_type == 'models':
        # Run model tests
        success = run_command(pytest_cmd + ['tests/test_models.py'], "Running model tests")
        
    elif args.test_type == 'integration':
        # Run integration tests
        success = run_command(pytest_cmd + ['tests/test_integration.py'], "Running integration tests")
        
    elif args.test_type == 'coverage':
        # Run with detailed coverage report
        coverage_cmd = pytest_cmd + [
            'tests/',
            '--cov=.',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-fail-under=80'
        ]
        success = run_command(coverage_cmd, "Running tests with coverage report")
        
        if success:
            print("\n📊 Coverage report generated in 'htmlcov' directory")
            print("📂 Open 'htmlcov/index.html' in your browser to view detailed coverage")
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests completed successfully!")
        print("\n💡 Usage tips:")
        print("  - Run specific tests: python run_tests.py -k test_name")
        print("  - Run with verbose output: python run_tests.py -v")
        print("  - Generate coverage report: python run_tests.py coverage")
        print("  - Run only API tests: python run_tests.py api")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == '__main__':
    main() 