#!/usr/bin/env python
"""
Quick start script for MPES.
Sets up environment and runs a demo simulation.
"""

import asyncio
import subprocess
import sys
import os


def check_dependencies():
    """Check if required packages are installed."""
    try:
        import ray
        import numpy
        import websockets
        print("✓ All required packages installed")
        return True
    except ImportError as e:
        print(f"✗ Missing package: {e.name}")
        print("\nInstalling dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True


async def run_demo():
    """Run a demo simulation."""
    from core.simulation import MPESSimulation, SimulationConfig
    
    print("\n" + "="*60)
    print("🎮 MPES DEMO SIMULATION")
    print("="*60)
    print("\nThis demo runs a small simulation with:")
    print("  • 50 agents")
    print("  • 4 commodities (grain, iron, wood, stone)")
    print("  • 100 ticks")
    print("  • Money printing enabled (demonstrating inflation)")
    print("\nThe simulation will take approximately 1-2 minutes.")
    print("="*60 + "\n")
    
    input("Press Enter to start the demo...")
    
    config = SimulationConfig(
        num_agents=50,
        commodities=["grain", "iron", "wood", "stone"],
        num_ticks=100,
        enable_llm=False,
        enable_money_printing=True,
        inflation_rate=0.05,
        intervention_frequency=10,
        intervention_size=200.0
    )
    
    simulation = MPESSimulation(config)
    await simulation.run()
    
    print("\n" + "="*60)
    print("🎉 DEMO COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Check the generated JSON file for detailed results")
    print("  2. Run 'python analysis_utils.py <results_file.json>' for analysis")
    print("  3. Try different configurations with 'python run_simulation.py --help'")
    print("  4. Enable visualization: 'python run_simulation.py --websocket'")
    print("     Then open frontend/index.html in your browser")
    print("="*60 + "\n")


def main():
    """Main entry point."""
    print("🚀 MPES Quick Start")
    print("="*60 + "\n")
    
    # Check dependencies
    if not check_dependencies():
        print("Failed to install dependencies. Please install manually:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Run demo
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n⏸ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
