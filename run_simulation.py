"""
Main entry point for running MPES simulation.
Provides CLI interface for different simulation modes.
"""

import argparse
import asyncio
from core.simulation import MPESSimulation, SimulationConfig
from core.leviathan import MonetaryPolicy


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Massively Parallel Economic Simulation (MPES)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Simulation parameters
    parser.add_argument(
        "--agents", 
        type=int, 
        default=100,
        help="Number of agents in simulation"
    )
    
    parser.add_argument(
        "--ticks", 
        type=int, 
        default=500,
        help="Number of simulation ticks"
    )
    
    parser.add_argument(
        "--commodities",
        nargs="+",
        default=["grain", "iron", "wood", "stone"],
        help="List of commodities to trade"
    )
    
    # LLM configuration
    parser.add_argument(
        "--enable-llm",
        action="store_true",
        help="Use LLM for agent decisions"
    )
    
    parser.add_argument(
        "--use-vllm",
        action="store_true",
        help="Use vLLM backend (requires GPU)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="LLM batch size"
    )
    
    # Fiscal policy
    parser.add_argument(
        "--money-printing",
        action="store_true",
        default=True,
        help="Enable Leviathan money printing"
    )
    
    parser.add_argument(
        "--no-money-printing",
        action="store_false",
        dest="money_printing",
        help="Disable money printing (baseline economy)"
    )
    
    parser.add_argument(
        "--inflation-rate",
        type=float,
        default=0.05,
        help="Target inflation rate per intervention"
    )
    
    parser.add_argument(
        "--intervention-freq",
        type=int,
        default=20,
        help="Ticks between Leviathan interventions"
    )
    
    parser.add_argument(
        "--intervention-size",
        type=float,
        default=500.0,
        help="Currency injected per intervention"
    )
    
    parser.add_argument(
        "--enable-taxes",
        action="store_true",
        help="Enable taxation"
    )
    
    # Visualization
    parser.add_argument(
        "--websocket",
        action="store_true",
        help="Enable WebSocket server for visualization"
    )
    
    parser.add_argument(
        "--ws-port",
        type=int,
        default=8765,
        help="WebSocket server port"
    )
    
    # Presets
    parser.add_argument(
        "--preset",
        choices=["baseline", "inflation", "deflation", "inequality", "small", "large"],
        help="Use a preset configuration"
    )
    
    return parser.parse_args()


def get_preset_config(preset: str) -> SimulationConfig:
    """Get preset simulation configuration."""
    
    presets = {
        "baseline": SimulationConfig(
            num_agents=100,
            num_ticks=1000,
            enable_money_printing=False,
            enable_taxes=False
        ),
        
        "inflation": SimulationConfig(
            num_agents=100,
            num_ticks=500,
            enable_money_printing=True,
            inflation_rate=0.10,
            intervention_frequency=10,
            intervention_size=1000.0
        ),
        
        "deflation": SimulationConfig(
            num_agents=100,
            num_ticks=500,
            enable_money_printing=False,
            enable_taxes=True
        ),
        
        "inequality": SimulationConfig(
            num_agents=200,
            num_ticks=1000,
            enable_money_printing=True,
            enable_taxes=True,
            inflation_rate=0.03
        ),
        
        "small": SimulationConfig(
            num_agents=20,
            num_ticks=100,
            enable_money_printing=True
        ),
        
        "large": SimulationConfig(
            num_agents=500,
            num_ticks=2000,
            enable_money_printing=True,
            enable_websocket=True
        )
    }
    
    return presets.get(preset, SimulationConfig())


async def main():
    """Main entry point."""
    args = parse_args()
    
    # Use preset or custom configuration
    if args.preset:
        config = get_preset_config(args.preset)
        print(f"🎯 Using preset: {args.preset}")
    else:
        config = SimulationConfig(
            num_agents=args.agents,
            commodities=args.commodities,
            num_ticks=args.ticks,
            enable_llm=args.enable_llm,
            enable_money_printing=args.money_printing,
            enable_taxes=args.enable_taxes,
            inflation_rate=args.inflation_rate,
            intervention_frequency=args.intervention_freq,
            intervention_size=args.intervention_size,
            llm_batch_size=args.batch_size,
            use_vllm=args.use_vllm,
            enable_websocket=args.websocket,
            websocket_port=args.ws_port
        )
    
    # Print configuration
    print("\n" + "="*60)
    print("MPES SIMULATION CONFIGURATION")
    print("="*60)
    print(f"Agents: {config.num_agents}")
    print(f"Commodities: {', '.join(config.commodities)}")
    print(f"Ticks: {config.num_ticks}")
    print(f"LLM Enabled: {config.enable_llm}")
    print(f"Money Printing: {config.enable_money_printing}")
    print(f"Taxes: {config.enable_taxes}")
    
    if config.enable_money_printing:
        print(f"  Inflation Rate: {config.inflation_rate*100:.1f}%")
        print(f"  Intervention Frequency: {config.intervention_frequency} ticks")
        print(f"  Intervention Size: ${config.intervention_size:.2f}")
    
    print(f"WebSocket: {config.enable_websocket}")
    if config.enable_websocket:
        print(f"  Port: {config.websocket_port}")
        print(f"  Open frontend/index.html in browser to visualize")
    
    print("="*60 + "\n")
    
    # Run simulation
    simulation = MPESSimulation(config)
    await simulation.run()


if __name__ == "__main__":
    asyncio.run(main())
