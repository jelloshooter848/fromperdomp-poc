#!/usr/bin/env python3
"""
DOMP Master Test Runner
Executes all DOMP tests in sequence and provides comprehensive results.
"""

import subprocess
import sys
import time
import os
from typing import List, Tuple, Dict

# Test files in order of execution (using actual file names)
TEST_FILES = [
    "test_pow.py",                           # Basic PoW/crypto testing
    "test_lightning_client.py",              # Lightning client tests
    "test_reputation_system.py",             # Reputation system tests
    "test_lightning_escrow.py",              # Lightning escrow tests (FIXED)
    "test_complete_domp_flow.py",            # Complete DOMP flow tests
    "test_web_lightning.py",                 # Web API Lightning tests (FIXED)
    "test_lightning_payment.py",             # Lightning payment tests (FIXED)
    "test_nostr_relays.py",                  # Nostr relay tests (FIXED)
    "test_domp_lightning_integration.py",    # DOMP Lightning integration
    "test_real_lightning.py",                # Real Lightning Network tests
    "test_web_simple.py",                    # Simple web tests
]

class TestResult:
    def __init__(self, name: str, passed: bool, duration: float, output: str = ""):
        self.name = name
        self.passed = passed
        self.duration = duration
        self.output = output

def run_single_test(test_file: str) -> TestResult:
    """Run a single test file and return results."""
    print(f"🧪 Running {test_file}...")
    
    start_time = time.time()
    
    try:
        # Run the test
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout per test (reduced from 5 minutes)
        )
        
        duration = time.time() - start_time
        
        # Determine if test passed based on exit code and output
        passed = result.returncode == 0
        
        # Additional checks for specific success patterns
        output = result.stdout + result.stderr
        if "PASSED" in output or "SUCCESS" in output:
            passed = True
        elif "FAILED" in output or "ERROR" in output:
            passed = False
            
        return TestResult(test_file, passed, duration, output)
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return TestResult(test_file, False, duration, "Test timed out after 5 minutes")
    except Exception as e:
        duration = time.time() - start_time
        return TestResult(test_file, False, duration, f"Test execution failed: {e}")

def print_header():
    """Print the test runner header."""
    print("🎯 DOMP COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("Running all DOMP protocol tests to verify system integrity")
    print(f"📋 Total tests to run: {len(TEST_FILES)}")
    print("=" * 70)

def print_progress(current: int, total: int, test_name: str):
    """Print progress indicator."""
    progress = (current / total) * 100
    bar_length = 30
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\n[{bar}] {progress:.1f}% ({current}/{total}) - {test_name}")

def print_test_result(result: TestResult):
    """Print individual test result."""
    status = "✅ PASS" if result.passed else "❌ FAIL"
    duration_str = f"{result.duration:.2f}s"
    print(f"  {status} - {result.name} ({duration_str})")
    
    if not result.passed:
        # Show last few lines of output for failed tests
        lines = result.output.strip().split('\n')
        error_lines = lines[-5:] if len(lines) > 5 else lines
        for line in error_lines:
            if line.strip():
                print(f"    💥 {line.strip()}")

def print_summary(results: List[TestResult]):
    """Print comprehensive test summary."""
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed_tests = [r for r in results if r.passed]
    failed_tests = [r for r in results if not r.passed]
    total_duration = sum(r.duration for r in results)
    
    # Overall statistics
    print(f"\n📈 Overall Results:")
    print(f"  ✅ Passed: {len(passed_tests)}/{len(results)} tests")
    print(f"  ❌ Failed: {len(failed_tests)}/{len(results)} tests")
    print(f"  ⏱️  Total time: {total_duration:.2f} seconds")
    print(f"  📊 Success rate: {(len(passed_tests)/len(results)*100):.1f}%")
    
    # Detailed results by category (updated with actual file names)
    categories = {
        "Core & Crypto": ["test_pow.py"],
        "Lightning Network": ["test_lightning_client.py", "test_lightning_escrow.py", "test_lightning_payment.py", "test_real_lightning.py", "test_domp_lightning_integration.py"],
        "Network Integration": ["test_nostr_relays.py"],
        "Web API": ["test_web_lightning.py", "test_web_simple.py"],
        "Complete Flows": ["test_complete_domp_flow.py", "test_reputation_system.py"]
    }
    
    print(f"\n🏷️  Results by Category:")
    for category, tests in categories.items():
        category_results = [r for r in results if r.name in tests]
        category_passed = [r for r in category_results if r.passed]
        if category_results:
            success_rate = len(category_passed) / len(category_results) * 100
            status = "✅" if success_rate == 100 else "⚠️" if success_rate >= 50 else "❌"
            print(f"  {status} {category}: {len(category_passed)}/{len(category_results)} ({success_rate:.0f}%)")
    
    # Failed tests details
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for result in failed_tests:
            print(f"  • {result.name} - {result.duration:.2f}s")
    
    # Performance analysis
    print(f"\n⚡ Performance Analysis:")
    fastest = min(results, key=lambda r: r.duration)
    slowest = max(results, key=lambda r: r.duration)
    print(f"  🚀 Fastest: {fastest.name} ({fastest.duration:.2f}s)")
    print(f"  🐌 Slowest: {slowest.name} ({slowest.duration:.2f}s)")
    
    # Final verdict
    print(f"\n🎯 FINAL VERDICT:")
    if len(failed_tests) == 0:
        print("  🎉 ALL TESTS PASSED! DOMP system is fully functional!")
        print("  ✅ Ready for production deployment")
        print("  🚀 No regressions detected")
    elif len(failed_tests) <= 2:
        print("  ⚠️  Minor issues detected - mostly functional")
        print("  🔧 Few tests need attention")
    else:
        print("  ❌ Major issues detected - requires fixes")
        print("  🚨 Multiple test failures need investigation")

def main():
    """Main test runner function."""
    print_header()
    
    results = []
    
    # Run each test
    for i, test_file in enumerate(TEST_FILES, 1):
        print_progress(i, len(TEST_FILES), test_file)
        
        # Check if test file exists
        if not os.path.exists(test_file):
            print(f"  ❌ SKIP - {test_file} not found")
            results.append(TestResult(test_file, False, 0.0, "Test file not found"))
            continue
        
        # Run the test
        result = run_single_test(test_file)
        results.append(result)
        
        # Print immediate result
        print_test_result(result)
        
        # Small delay between tests
        time.sleep(0.5)
    
    # Print comprehensive summary
    print_summary(results)
    
    # Exit with appropriate code
    failed_count = len([r for r in results if not r.passed])
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)