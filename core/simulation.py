"""
MPES Simulation Orchestrator
Tick-based synchronous simulation: Step -> Think -> Act -> Match
"""

import ray
import asyncio
from ray.exceptions import ActorUnavailableError
from typing import List, Dict, Optional
import time
from dataclasses import dataclass, field
import json
from datetime import datetime
from pathlib import Path

from core.market import MarketEngine
from core.agents import AgentFactory
from core.money_issuer import FiscalPolicy, MonetaryPolicy
from core.inference import InferenceEngine, InferenceConfig


@dataclass
class SimulationConfig:
    """Configuration for the simulation."""
    num_agents: int = 100
    commodities: List[str] = field(default_factory=lambda: ["grain", "iron", "wood", "stone"])
    num_ticks: int = 1000
    enable_llm: bool = False  # Use LLM for agent decisions
    enable_money_printing: bool = True
    enable_taxes: bool = False
    
    # Monetary policy
    inflation_rate: float = 0.05
    intervention_frequency: int = 20
    intervention_size: float = 500.0
    
    # LLM config
    llm_batch_size: int = 32
    use_vllm: bool = False
    
    # Visualization
    enable_websocket: bool = False
    websocket_port: int = 8765
    
    # Output
    output_dir: str = "output"


class MPESSimulation:
    """
    Main simulation orchestrator for Massively Parallel Economic Simulation.
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.transaction_log = []  # Detailed transaction history
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_path = None  # Will be set when simulation starts
        
        # Core components
        self.market: Optional[MarketEngine] = None
        self.agents: List = []
        self.fiscal_policy: Optional[FiscalPolicy] = None
        self.inference_engine: Optional[InferenceEngine] = None
        
        # State tracking
        self.current_tick = 0
        self.simulation_data: List[Dict] = []
        self.is_running = False
        
        # Output Streams
        self.data_file = None
        
        # Summary Statistics (for final report without keeping full history)
        self.first_tick_stats = None
        self.last_tick_stats = None
        self.cumulative_trades = 0
        
        # Performance metrics
        self.tick_times: List[float] = []
    
    async def initialize(self):
        """Initialize all simulation components."""
        print("🚀 Initializing MPES Simulation...")

        # Setup Output Directory immediately
        self.output_path = Path(self.config.output_dir) / self.run_id
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Init Data File (JSONL)
        self.data_file = open(self.output_path / "simulation_data.jsonl", "w", encoding='utf-8')
        
        # Save initial metadata (for live visualization support)
        initial_metadata = {
            'run_id': self.run_id,
            'config': {
                'num_agents': self.config.num_agents,
                'commodities': self.config.commodities,
                'num_ticks': self.config.num_ticks, # Planned ticks
                'enable_llm': self.config.enable_llm,
                'enable_money_printing': self.config.enable_money_printing,
                'enable_taxes': self.config.enable_taxes,
                'inflation_rate': self.config.inflation_rate,
            },
            'start_time': self.run_id,
            'status': 'running',
            'total_ticks': 0,
            'total_trades': 0
        }
        with open(self.output_path / "metadata.json", 'w') as f:
            json.dump(initial_metadata, f, indent=2)
        
        # Initialize Ray
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
            print("✓ Ray initialized")
        
        # Create market engine
        self.market = MarketEngine(self.config.commodities)
        print(f"✓ Market engine created with {len(self.config.commodities)} commodities")
        
        # Create agent population
        print(f"Creating {self.config.num_agents} agents...")
        self.agents = AgentFactory.create_agent_population(
            num_agents=self.config.num_agents,
            commodities=self.config.commodities
        )
        print(f"✓ {len(self.agents)} agents created")
        
        # Initialize fiscal policy (Leviathan)
        if self.config.enable_money_printing or self.config.enable_taxes:
            monetary_policy = MonetaryPolicy(
                inflation_rate=self.config.inflation_rate,
                intervention_frequency=self.config.intervention_frequency,
                intervention_size=self.config.intervention_size,
                target_commodities=self.config.commodities
            )
            
            self.fiscal_policy = FiscalPolicy(
                enable_printing=self.config.enable_money_printing,
                enable_taxes=self.config.enable_taxes,
                monetary_policy=monetary_policy
            )
            
            self.fiscal_policy.initialize_actors(self.config.commodities)
            print("✓ Fiscal policy initialized (Money Issuer active)")
        
        # Initialize inference engine if using LLM
        if self.config.enable_llm:
            inference_config = InferenceConfig(
                use_vllm=self.config.use_vllm,
                batch_size=self.config.llm_batch_size
            )
            self.inference_engine = InferenceEngine(inference_config)
            await self.inference_engine.initialize()
            print("✓ Inference engine initialized")
        
        print("✅ Simulation initialization complete!\n")
    
    async def run_tick(self) -> Dict:
        """
        Execute one simulation tick.
        
        Tick Flow:
        1. Reset agent energy
        2. Agents produce commodities
        3. Agents consume commodities
        4. Agents decide trades (Think)
        5. Submit orders to market (Act)
        6. Leviathan intervention
        7. Match all orders
        8. Execute trades and update agent states
        9. Collect statistics
        """
        tick_start = time.time()
        
        # 1. Reset energy for all agents
        await asyncio.gather(*[
            agent.reset_energy.remote() for agent in self.agents
        ])
        
        # 2. Production phase
        production_results = await asyncio.gather(*[
            agent.produce.remote() for agent in self.agents
        ])
        total_production = sum(1 for p in production_results if p is not None)
        
        # 3. Consumption phase
        consumption_results = await asyncio.gather(*[
            agent.consume.remote() for agent in self.agents
        ])
        
        # 4. Get agent states for decision making
        agent_states = await asyncio.gather(*[
            agent.get_state.remote() for agent in self.agents
        ])
        
        # 5. Decision phase (Think)
        market_stats = self.market.get_all_market_stats()
        
        if self.config.enable_llm and self.inference_engine:
            # Use LLM for decisions
            agent_contexts = await asyncio.gather(*[
                agent.get_llm_prompt_context.remote() for agent in self.agents
            ])
            agent_ids = [s['agent_id'] for s in agent_states]
            
            llm_decisions = await self.inference_engine.batch_agent_decisions(
                agent_contexts, agent_ids
            )
            
            # Convert LLM decisions to orders (simplified)
            # In production, this would be more sophisticated
            agent_orders = await asyncio.gather(*[
                agent.decide_trade_action.remote(market_stats)
                for agent in self.agents
            ])
        else:
            # Use built-in logic
            agent_orders = await asyncio.gather(*[
                agent.decide_trade_action.remote(market_stats)
                for agent in self.agents
            ])
        
        # 6. Submit orders to market (Act)
        total_orders = 0
        for agent_state, orders in zip(agent_states, agent_orders):
            for order in orders:
                self.market.submit_order(
                    commodity=order['commodity'],
                    agent_id=agent_state['agent_id'],
                    is_bid=order['is_bid'],
                    price=order['price'],
                    quantity=order['quantity']
                )
                total_orders += 1
        
        # 6. Money Issuer intervention
        money_issuer_orders = []
        if self.fiscal_policy:
            money_issuer_orders, tax_amounts = await self.fiscal_policy.execute_fiscal_cycle(
                market_stats, agent_states, self.current_tick
            )
            
            # Submit Money Issuer orders
            for order in money_issuer_orders:
                self.market.submit_order(
                    commodity=order['commodity'],
                    agent_id=order['agent_id'],
                    is_bid=order['is_bid'],
                    price=order['price'],
                    quantity=order['quantity']
                )
            
            # Apply taxes to agents
            if tax_amounts:
                # This would require a method to deduct from wallets
                pass
        
        # 8. Match all orders
        trades = self.market.match_all_markets()
        
        # Record transactions with full details
        if trades:
            for trade in trades:
                transaction_record = {
                    'tick': self.current_tick,
                    'timestamp': time.time(),
                    'type': 'trade',
                    'buyer_id': trade.buyer_id,
                    'seller_id': trade.seller_id,
                    'commodity': trade.commodity,
                    'price': trade.price,
                    'quantity': trade.quantity,
                    'total_value': trade.price * trade.quantity
                }
                self.transaction_log.append(transaction_record)
        
        # 9. Execute trades on agents
        if trades:
            # Group trades by agent
            agent_trades = {}
            for trade in trades:
                buyer = trade.buyer_id
                seller = trade.seller_id
                
                if buyer not in agent_trades:
                    agent_trades[buyer] = []
                if seller not in agent_trades:
                    agent_trades[seller] = []
                
                trade_info = {
                    'buyer_id': buyer,
                    'seller_id': seller,
                    'commodity': trade.commodity,
                    'price': trade.price,
                    'quantity': trade.quantity
                }
                
                agent_trades[buyer].append(trade_info)
                agent_trades[seller].append(trade_info)
            
            # Execute on each agent
            for agent in self.agents:
                agent_state = await agent.get_state.remote()
                agent_id = agent_state['agent_id']
                
                if agent_id in agent_trades:
                    for trade_info in agent_trades[agent_id]:
                        await agent.execute_trade.remote(trade_info)
        
        # 10. Collect tick statistics
        tick_stats = await self.collect_tick_statistics(
            agent_states=agent_states,
            trades=trades,
            total_orders=total_orders,
            total_production=total_production,
            money_issuer_active=len(money_issuer_orders) > 0
        )
        
        tick_time = time.time() - tick_start
        self.tick_times.append(tick_time)
        tick_stats['tick_time'] = tick_time
        
        # STREAMING UPDATE
        if self.data_file:
            self.data_file.write(json.dumps(tick_stats) + "\n")
            self.data_file.flush()
            
        # Update summary stats
        if self.current_tick == 0:
            self.first_tick_stats = tick_stats
        self.last_tick_stats = tick_stats
        self.cumulative_trades += tick_stats['total_trades']
        
        # Note: We do NOT append to self.simulation_data to save memory
        self.current_tick += 1
        
        return tick_stats
    
    async def collect_tick_statistics(
        self,
        agent_states: List[Dict],
        trades: List,
        total_orders: int,
        total_production: int,
        money_issuer_active: bool
    ) -> Dict:
        """Collect comprehensive statistics for this tick."""
        
        # Market statistics
        market_stats = self.market.get_all_market_stats()
        
        # Agent statistics
        total_wealth = sum(s['wallet'] for s in agent_states)
        avg_wealth = total_wealth / len(agent_states)
        
        total_utility = sum(s['utility'] for s in agent_states)
        avg_utility = total_utility / len(agent_states)
        
        # Wealth distribution
        wealths = sorted([s['wallet'] for s in agent_states])
        gini_coefficient = self._calculate_gini(wealths)
        
        # Price tracking
        avg_prices = {}
        for commodity, stats in market_stats.items():
            avg_prices[commodity] = stats.get('avg_price_recent', 0)
            
        # Order Book Snapshot
        order_books = self.market.get_order_book_snapshot()

        # Simplified Agent States for Visualization
        agent_details = [
            {
                'id': s['agent_id'],
                'wallet': s['wallet'],
                'inventory': s['inventory'],
                'utility': s['utility']
            }
            for s in agent_states
        ]
        
        return {
            'tick': self.current_tick,
            'total_trades': len(trades),
            'total_orders': total_orders,
            'total_production': total_production,
            'total_wealth': total_wealth,
            'avg_wealth': avg_wealth,
            'total_utility': total_utility,
            'avg_utility': avg_utility,
            'gini_coefficient': gini_coefficient,
            'market_stats': market_stats,
            'order_books': order_books,
            'agents': agent_details,
            'avg_prices': avg_prices,
            'money_issuer_active': money_issuer_active
        }
    
    def _calculate_gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient for inequality measurement."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = 0
        
        for i, val in enumerate(sorted_values):
            cumsum += (i + 1) * val
        
        return (2 * cumsum) / (n * sum(sorted_values)) - (n + 1) / n
    
    async def run(self):
        """Run the complete simulation."""
        await self.initialize()
        
        self.is_running = True
        print(f"🎮 Starting simulation for {self.config.num_ticks} ticks...\n")
        
        try:
            for tick in range(self.config.num_ticks):
                tick_stats = await self.run_tick()
                
                # Print progress
                if tick % 10 == 0 or tick == 0:
                    self._print_tick_summary(tick_stats)
                
                # Optional: websocket broadcast for visualization
                if self.config.enable_websocket:
                    # TODO: Broadcast to websocket clients
                    pass
        
        except KeyboardInterrupt:
            print("\n⏸ Simulation interrupted by user")
        
        except ActorUnavailableError as e:
            print(f"\n⚠️ Simulation stopped early due to Ray actor error: {e}")
            print("This is typically a resource limitation on Windows (socket exhaustion).") 
            print("Finalizing collected data so you can view the partial run...")

        except Exception as e:
            print(f"\n❌ Unexpected error during simulation: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.is_running = False
            await self.finalize()
    
    def _print_tick_summary(self, stats: Dict):
        """Print summary of tick statistics."""
        print(f"⏱ Tick {stats['tick']:4d} | "
              f"Trades: {stats['total_trades']:3d} | "
              f"Wealth: ${stats['avg_wealth']:7.2f} | "
              f"Utility: {stats['avg_utility']:6.2f} | "
              f"Gini: {stats['gini_coefficient']:.3f} | "
              f"Time: {stats['tick_time']*1000:.1f}ms")
        
        # Print price updates
        if stats['tick'] % 50 == 0:
            print("  📈 Prices:", end=" ")
            for commodity, price in stats['avg_prices'].items():
                print(f"{commodity}=${price:.2f}", end=" ")
            print()

    async def finalize(self):
        """Cleanup and save results."""
        print("\n📊 Finalizing simulation...")
        
        # Close the streaming data file
        if self.data_file:
            self.data_file.close()
            print(f"✓ Simulation data stream closed ({self.output_path / 'simulation_data.jsonl'})")
        
        # Save transaction log (still monolithic for now, can be streamed if needed)
        transaction_file = self.output_path / "transactions.json"
        with open(transaction_file, 'w') as f:
            json.dump(self.transaction_log, f, indent=2)
        print(f"✓ Transaction log saved to {transaction_file}")
        
        # Save metadata
        metadata = {
            'run_id': self.run_id,
            'config': {
                'num_agents': self.config.num_agents,
                'commodities': self.config.commodities,
                'num_ticks': self.current_tick,
                'enable_llm': self.config.enable_llm,
                'enable_money_printing': self.config.enable_money_printing,
                'enable_taxes': self.config.enable_taxes,
                'inflation_rate': self.config.inflation_rate,
            },
            'start_time': self.run_id,
            'total_ticks': self.current_tick,
            'total_trades': self.cumulative_trades,
            'total_transactions': len(self.transaction_log),
        }
        metadata_file = self.output_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Metadata saved to {metadata_file}")
        
        # Print final statistics
        self._print_final_statistics()
        
        # Shutdown Ray
        ray.shutdown()
        print("✓ Ray shutdown complete")
    
    def _print_final_statistics(self):
        """Print final simulation statistics."""
        print("\n" + "="*60)
        print("FINAL SIMULATION STATISTICS")
        print("="*60)
        
        if not self.last_tick_stats:
            print("No data collected")
            return
        
        final_stats = self.last_tick_stats
        initial_stats = self.first_tick_stats or final_stats
        
        print(f"Total Ticks: {self.current_tick}")
        print(f"Total Trades: {self.cumulative_trades}")
        print(f"\nWealth:")
        print(f"  Initial Average: ${initial_stats['avg_wealth']:.2f}")
        print(f"  Final Average: ${final_stats['avg_wealth']:.2f}")
        
        if initial_stats['avg_wealth'] > 0:
            print(f"  Change: {((final_stats['avg_wealth']/initial_stats['avg_wealth'])-1)*100:+.1f}%")

        print(f"\nInequality (Gini):")
        print(f"  Initial: {initial_stats['gini_coefficient']:.3f}")
        print(f"  Final: {final_stats['gini_coefficient']:.3f}")
        
        print(f"\nPrice Inflation:")
        for commodity in self.config.commodities:
            initial_price = initial_stats['avg_prices'].get(commodity, 0)
            final_price = final_stats['avg_prices'].get(commodity, 0)
            
            if initial_price > 0:
                inflation = ((final_price / initial_price) - 1) * 100
                print(f"  {commodity}: {inflation:+.1f}%")
        
        print(f"\nPerformance:")
        if self.tick_times:
            avg_tick_time = sum(self.tick_times) / len(self.tick_times)
            print(f"  Average tick time: {avg_tick_time*1000:.2f}ms")
            print(f"  Total simulation time: {sum(self.tick_times):.2f}s")
        
        print("="*60 + "\n")


async def main():
    """Main entry point."""
    # Example configuration
    config = SimulationConfig(
        num_agents=50,
        commodities=["grain", "iron", "wood", "stone"],
        num_ticks=100,
        enable_llm=False,  # Set to True to use LLM
        enable_money_printing=True,
        inflation_rate=0.05,
        intervention_frequency=10
    )
    
    simulation = MPESSimulation(config)
    await simulation.run()


if __name__ == "__main__":
    asyncio.run(main())
