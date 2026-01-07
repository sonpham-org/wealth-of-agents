"""
Test script to verify MPES installation and basic functionality.
Run this after setup to ensure everything works.
"""

import sys
import importlib

def test_imports():
    """Test that all required packages can be imported."""
    print("🔍 Testing package imports...")
    
    required_packages = [
        ('ray', 'Ray'),
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('websockets', 'WebSockets'),
        ('aiohttp', 'aiohttp'),
        ('pytest', 'pytest'),
    ]
    
    failed = []
    for package, name in required_packages:
        try:
            importlib.import_module(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT FOUND")
            failed.append(name)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All packages installed!\n")
    return True


def test_core_modules():
    """Test that core modules can be imported."""
    print("🔍 Testing core modules...")
    
    try:
        from core.market import MarketEngine, LimitOrderBook
        print("  ✓ core.market")
    except ImportError as e:
        print(f"  ✗ core.market - {e}")
        return False
    
    try:
        from core.agents import EconomicAgent, AgentFactory
        print("  ✓ core.agents")
    except ImportError as e:
        print(f"  ✗ core.agents - {e}")
        return False
    
    try:
        from core.money_issuer import MoneyIssuer, FiscalPolicy
        print("  ✓ core.money_issuer")
    except ImportError as e:
        print(f"  ✗ core.money_issuer - {e}")
        return False
    
    try:
        from core.simulation import MPESSimulation, SimulationConfig
        print("  ✓ core.simulation")
    except ImportError as e:
        print(f"  ✗ core.simulation - {e}")
        return False
    
    print("\n✅ All core modules accessible!\n")
    return True


def test_market_basic():
    """Test basic market functionality."""
    print("🔍 Testing market engine...")
    
    try:
        from core.market import LimitOrderBook
        
        # Create order book
        lob = LimitOrderBook("grain")
        
        # Add orders
        lob.add_bid("agent_001", 10.0, 1.0)
        lob.add_ask("agent_002", 12.0, 1.0)
        
        # Check spread
        spread = lob.get_spread()
        assert spread == (10.0, 12.0), f"Expected (10.0, 12.0), got {spread}"
        
        print("  ✓ Order book creation")
        print("  ✓ Order insertion")
        print("  ✓ Spread calculation")
        
        # Test matching
        lob.add_bid("agent_003", 13.0, 0.5)
        trades = lob.match_orders()
        assert len(trades) == 1, f"Expected 1 trade, got {len(trades)}"
        assert trades[0].quantity == 0.5
        
        print("  ✓ Order matching")
        print("\n✅ Market engine works!\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Market test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ray():
    """Test Ray initialization."""
    print("🔍 Testing Ray...")
    
    try:
        import ray
        
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
        
        print("  ✓ Ray initialized")
        
        # Test simple Ray task
        @ray.remote
        def test_task(x):
            return x * 2
        
        result = ray.get(test_task.remote(21))
        assert result == 42
        
        print("  ✓ Ray tasks work")
        
        ray.shutdown()
        print("  ✓ Ray shutdown")
        
        print("\n✅ Ray works!\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Ray test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_minimal_simulation():
    """Test minimal simulation run."""
    print("🔍 Testing minimal simulation...")
    
    try:
        import asyncio
        from core.simulation import MPESSimulation, SimulationConfig
        
        async def run_test():
            config = SimulationConfig(
                num_agents=5,
                num_ticks=3,
                enable_llm=False,
                enable_money_printing=False
            )
            
            simulation = MPESSimulation(config)
            await simulation.initialize()
            
            # Run a few ticks
            for i in range(3):
                await simulation.run_tick()
            
            # Cleanup
            import ray
            ray.shutdown()
        
        asyncio.run(run_test())
        
        print("  ✓ Simulation initialization")
        print("  ✓ Agent creation")
        print("  ✓ Tick execution")
        print("\n✅ Simulation works!\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Simulation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("MPES INSTALLATION TEST")
    print("="*60)
    print()
    
    tests = [
        ("Package Imports", test_imports),
        ("Core Modules", test_core_modules),
        ("Market Engine", test_market_basic),
        ("Ray Framework", test_ray),
        ("Minimal Simulation", test_minimal_simulation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(success for _, success in results)
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYou're ready to run simulations!")
        print("\nNext steps:")
        print("  1. Run demo: python quickstart.py")
        print("  2. Run preset: python run_simulation.py --preset small")
        print("  3. Run tests: pytest tests/ -v")
        print()
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nPlease check the errors above and:")
        print("  1. Ensure all dependencies installed: pip install -r requirements.txt")
        print("  2. Check Python version (3.8+ required)")
        print("  3. Report issues with error messages")
        print()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
