from django.test import TestCase

class BLEOBaseTest(TestCase):
    """Base test class with enhanced logging for all BLEO tests"""
    
    def setUp(self):
        # This runs before each test
        self.test_name = self._testMethodName
        print(f"\n📋 Running test: {self.test_name}")
    
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
                        error_msg = failure[1].split('\n')[-2] if len(failure) > 1 else "Unknown error"
                        print(f"❌ FAILED: {test_doc.strip()} - {error_msg}")
                        return
                for error in result.errors:
                    if self == error[0]:
                        error_msg = error[1].split('\n')[-2] if len(error) > 1 else "Unknown error"
                        print(f"❌ ERROR: {test_doc.strip()} - {error_msg}")
                        return
        
        # If we got here, the test passed
        print(f"✅ PASSED: {test_doc.strip()}")


class ColoredOutput:
    """Simple colored output for Windows and Unix systems"""
    
    @staticmethod
    def red(text):
        return f"\033[91m{text}\033[0m"
    
    @staticmethod
    def green(text):
        return f"\033[92m{text}\033[0m"
    
    @staticmethod
    def yellow(text):
        return f"\033[93m{text}\033[0m"
    
    @staticmethod
    def blue(text):
        return f"\033[94m{text}\033[0m"
    
    @staticmethod
    def bold(text):
        return f"\033[1m{text}\033[0m"
    
    @staticmethod
    def cyan(text):
        return f"\033[96m{text}\033[0m"
    
    @staticmethod
    def magenta(text):
        return f"\033[95m{text}\033[0m"


class TestSummaryFormatter:
    """Shared test summary formatting logic"""
    
    @staticmethod
    def show_enhanced_summary(test_results, total_time=None, test_case_name=None):
        """Show the enhanced test summary - used by both runners"""
        print("\n" + "="*80)
        print(ColoredOutput.bold("📊 BLEO TEST EXECUTION SUMMARY"))
        print("="*80)
        
        if test_results:
            total_tests = test_results.testsRun
            failed_tests = len(test_results.failures)
            error_tests = len(test_results.errors)
            passed_tests = total_tests - failed_tests - error_tests
            total_failures = failed_tests + error_tests
            
            # Calculate success rate
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            # Overall statistics with enhanced colors
            print(f"\n📈 OVERALL RESULTS:")
            print(f"   Total Tests Run: {ColoredOutput.bold(ColoredOutput.cyan(str(total_tests)))}")
            if total_time:
                print(f"   Execution Time: {ColoredOutput.bold(ColoredOutput.magenta(f'{total_time:.2f} seconds'))}")
            
            if total_failures == 0:
                print(f"   Passed: {ColoredOutput.green(ColoredOutput.bold(f'{passed_tests}/{total_tests}'))}")
                print(f"   Failed: {ColoredOutput.green('0/' + str(total_tests))}")
                print(f"   Success Rate: {ColoredOutput.green(ColoredOutput.bold(f'{success_rate:.1f}%'))}")
                
                # Success celebration
                print(f"\n🎉 {ColoredOutput.green(ColoredOutput.bold('ALL TESTS PASSED!'))}")
                suite_name = test_case_name or 'Test suite'
                print(f"🌟 {ColoredOutput.cyan(suite_name)} completed with {ColoredOutput.green(ColoredOutput.bold('100% success rate'))}")
                
                if total_time:
                    print(f"🚀 {ColoredOutput.magenta(f'Executed {total_tests} test(s) successfully in {total_time:.1f}s')}")
                else:
                    print(f"🚀 {ColoredOutput.magenta(f'Executed {total_tests} test(s) successfully')}")
                
                # Success tips
                print(f"\n✨ EXCELLENCE ACHIEVED:")
                print(f"   • All test assertions passed successfully")
                print(f"   • No runtime errors encountered")
                print(f"   • Code coverage appears to be working correctly")
                print(f"   • Ready for deployment or further development")
                
            else:
                print(f"   Passed: {ColoredOutput.green(f'{passed_tests}/{total_tests}')}")
                print(f"   Failed: {ColoredOutput.red(f'{total_failures}/{total_tests}')}")
                print(f"   Success Rate: {ColoredOutput.yellow(f'{success_rate:.1f}%')}")
                
                print(f"\n⚠️  {ColoredOutput.yellow(f'Some tests failed - Success rate: {success_rate:.1f}%')}")
                suite_name = test_case_name or 'Test suite'
                print(f"📊 {ColoredOutput.cyan(suite_name)} results: {ColoredOutput.green(f'{passed_tests} passed')}, {ColoredOutput.red(f'{total_failures} failed')}")
                
                # Show detailed failure information
                TestSummaryFormatter._show_failure_details(test_results)
                
                # Quick fix suggestions
                print(f"\n💡 QUICK ACTIONS:")
                print(f"   • Review failed test cases listed above")
                print(f"   • Check assertion conditions and expected vs actual values")
                print(f"   • Verify test data setup and database state")
                print(f"   • Run individual tests for detailed debugging")
            
            # Final status line
            print("\n" + "="*80)
            if total_failures == 0:
                final_message = f"🚀 SUCCESS: {passed_tests} tests passed with 100% success rate!"
                print(ColoredOutput.green(ColoredOutput.bold(final_message)))
            else:
                final_message = f"⚠️  REVIEW NEEDED: {passed_tests} passed, {total_failures} failed ({success_rate:.1f}% success rate)"
                print(ColoredOutput.red(ColoredOutput.bold(final_message)))
            print("="*80)
            
        else:
            # Fallback if no results captured
            if total_time:
                print(f"⏱️  Total execution time: {total_time:.2f} seconds")
            print("ℹ️  No detailed test results available")
            print("="*80)
    
    @staticmethod
    def _show_failure_details(test_results):
        """Show detailed failure information"""
        if test_results.failures:
            print(f"\n❌ ASSERTION FAILURES ({len(test_results.failures)}):")
            for i, failure in enumerate(test_results.failures, 1):
                test_name = str(failure[0]).split('(')[0]
                test_class = failure[0].__class__.__name__
                print(f"   {i}. {ColoredOutput.red(f'{test_class}.{test_name}')}")
                
                # Extract error message
                error_lines = failure[1].split('\n')
                for line in error_lines:
                    if "AssertionError" in line:
                        clean_error = line.strip().replace("AssertionError: ", "")
                        print(f"      💥 {ColoredOutput.yellow(clean_error)}")
                        break
                else:
                    # If no AssertionError line found, show the last meaningful line
                    for line in reversed(error_lines):
                        if line.strip() and not line.strip().startswith('File'):
                            print(f"      💥 {ColoredOutput.yellow(line.strip())}")
                            break
        
        if test_results.errors:
            print(f"\n🚨 RUNTIME ERRORS ({len(test_results.errors)}):")
            for i, error in enumerate(test_results.errors, len(test_results.failures) + 1):
                test_name = str(error[0]).split('(')[0]
                test_class = error[0].__class__.__name__
                print(f"   {i}. {ColoredOutput.red(f'{test_class}.{test_name}')}")
                
                # Extract error message
                error_lines = error[1].split('\n')
                for line in error_lines:
                    if any(keyword in line for keyword in ["Error:", "Exception:", "ImportError:", "ModuleNotFoundError:"]):
                        clean_error = line.strip()
                        print(f"      🔥 {ColoredOutput.yellow(clean_error)}")
                        break
                else:
                    # If no specific error line found, show the last meaningful line
                    for line in reversed(error_lines):
                        if line.strip() and not line.strip().startswith('File'):
                            print(f"      🔥 {ColoredOutput.yellow(line.strip())}")
                            break


# Keep only the standalone runner for direct file execution
def run_test_with_output(test_case):
    """Run a test with custom output handling and detailed summary (for standalone execution)"""
    import unittest
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(test_case))
    
    # Use the shared formatter
    TestSummaryFormatter.show_enhanced_summary(result, test_case_name=test_case.__name__)
    
    return result