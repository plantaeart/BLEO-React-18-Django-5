from django.test.runner import DiscoverRunner
from tests.base_test import ColoredOutput, TestSummaryFormatter
import time

class BLEOTestRunner(DiscoverRunner):
    """Custom Django test runner with enhanced output"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.test_results = None
    
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        print(ColoredOutput.bold("🧪 BLEO Enhanced Test Runner"))
        print("="*60)
        self.start_time = time.time()
    
    def run_suite(self, suite, **kwargs):
        """Override to capture test results"""
        # Run the test suite and capture results
        result = super().run_suite(suite, **kwargs)
        self.test_results = result
        return result
    
    def teardown_test_environment(self, **kwargs):
        # Calculate total time
        total_time = time.time() - self.start_time
        
        # Use the shared summary formatter
        TestSummaryFormatter.show_enhanced_summary(
            self.test_results, 
            total_time=total_time,
            test_case_name="Django Test Suite"
        )
        
        super().teardown_test_environment(**kwargs)
    
    def run_tests(self, test_labels, **kwargs):
        """Override to provide custom output"""
        print(f"🚀 Running tests: {test_labels or 'All tests'}")
        
        # Run the tests using Django's mechanism
        result = super().run_tests(test_labels, **kwargs)
        
        return result