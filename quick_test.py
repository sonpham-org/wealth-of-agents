"""
ECON_SIM Quick Test Runner
Run this anytime to verify everything works!
"""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and report success/failure"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False, text=True)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 ECON_SIM QUICK TEST SUITE")
    print("="*60)
    
    tests = [
        ("conda run -n econ_sim python test_installation.py", 
         "Installation Verification"),
        ("conda run -n econ_sim python run_simulation.py --preset small --ticks 20",
         "Quick Simulation (20 ticks)"),
        ("conda run -n econ_sim python analyze_results.py",
         "Results Analysis"),
    ]
    
    results = []
    for cmd, desc in tests:
        results.append(run_command(cmd, desc))
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is operational.")
        print("\nNext: Try 'python run_simulation.py --preset inflation'")
    else:
        print("\n⚠️  Some tests failed. Check output above.")
    print()

if __name__ == "__main__":
    main()
