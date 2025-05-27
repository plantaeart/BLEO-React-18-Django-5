from django.test import TestCase
import sys
import unittest

class BLEOBaseTest(TestCase):
    """Base test class with enhanced logging for all BLEO tests"""
    
    def setUp(self):
        # This runs before each test
        self.test_name = self._testMethodName
        print(f"\n📋 Running test: {self.test_name}")
        # Track if there were failures
        self._was_successful = True
    
    def tearDown(self):
        # This runs after each test
        test_method = getattr(self, self._testMethodName)
        test_doc = test_method.__doc__ or "No description"
        
        # Check if the test was successful
        if hasattr(self, '_outcome'):  # For Python 3.4+
            result = self._outcome.result
            if result.failures or result.errors:
                for failure in result.failures:
                    if self == failure[0]:
                        self._was_successful = False
                        error_msg = failure[1].split('\n')[-2] if len(failure) > 1 else "Unknown error"
                        print(f"❌ FAILED: {test_doc.strip()} - {error_msg}")
                        return
                for error in result.errors:
                    if self == error[0]:
                        self._was_successful = False
                        error_msg = error[1].split('\n')[-2] if len(error) > 1 else "Unknown error"
                        print(f"❌ ERROR: {test_doc.strip()} - {error_msg}")
                        return
        
        # If we got here, the test passed
        print(f"✅ PASSED: {test_doc.strip()}")


def run_test_with_output(test_case):
    """Run a test with custom output handling"""
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(test_case))
    
    total_failures = len(result.failures) + len(result.errors)
    if total_failures > 0:
        print(f"\n❌ FAILED TESTS: {total_failures} of {result.testsRun}")
        for i, failure in enumerate(result.failures, 1):
            test_name = str(failure[0]).split('(')[0]
            print(f"  {i}. {test_name}")
            error_lines = failure[1].split('\n')
            # Find the assertion line
            for line in error_lines:
                if "AssertionError" in line:
                    print(f"     {line.strip()}")
                    break
        
        for i, error in enumerate(result.errors, len(result.failures) + 1):
            test_name = str(error[0]).split('(')[0]
            print(f"  {i}. {test_name}")
            error_lines = error[1].split('\n')
            # Find the error line
            for line in error_lines:
                if "Error:" in line:
                    print(f"     {line.strip()}")
                    break
    else:
        print(f"\n✅ All {result.testsRun} tests PASSED!")