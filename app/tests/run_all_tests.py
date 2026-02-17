"""
Script to run all tests for the URL Shortener API.

Usage:
    docker exec -it interview_api python tests/run_all_tests.py
"""
import unittest
import pytest
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Also add the current directory to handle imports from the tests module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    print("Running all URL Shortener API tests...")

    # First run the unit tests with unittest
    print("\n=== Running unit tests with unittest ===")
    unittest_suite = unittest.defaultTestLoader.discover('tests', pattern='test_*.py')
    unittest_runner = unittest.TextTestRunner(verbosity=2)
    unittest_result = unittest_runner.run(unittest_suite)

    # Then run the docker integration test
    print("\n=== Running Docker integration tests ===")
    from tests.docker_test import TestURLShortenerAPI
    docker_suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestURLShortenerAPI)
    docker_result = unittest_runner.run(docker_suite)

    # Report results
    print("\n=== Test Results Summary ===")
    print(f"Unit tests: {'PASSED' if unittest_result.wasSuccessful() else 'FAILED'}")
    print(f"Docker tests: {'PASSED' if docker_result.wasSuccessful() else 'FAILED'}")

    # Exit with appropriate code
    sys.exit(0 if unittest_result.wasSuccessful() and docker_result.wasSuccessful() else 1)