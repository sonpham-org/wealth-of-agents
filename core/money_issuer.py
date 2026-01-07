"""
MoneyIssuer: The Money Printer and Market Manipulator
System-level actor that controls money supply and can intervene in markets.
"""

import ray
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class MonetaryPolicy:
    """Configuration for monetary intervention."""
    inflation_rate: float = 0.02  # Per tick inflation target
    intervention_frequency: int = 10  # Every N ticks
    intervention_size: float = 100.0  # Currency injected per intervention
    target_commodities: List[str] = None  # Which commodities to buy
    
    def __post_init__(self):
        if self.target_commodities is None:
            self.target_commodities = []


@ray.remote
class MoneyIssuer:
    """
    The Money Printer - A system-level actor that:
    1. Increases total money supply
    2. Places market buy orders to inject liquidity
    3. Demonstrates inflation as emergent property
    """
    
    def __init__(self, policy: MonetaryPolicy, commodities: List[str]):
        self.policy = policy
        self.commodities = commodities
        self.tick_count = 0
        self.total_printed = 0.0
        self.intervention_history: List[Dict] = []
        
        # If no target commodities specified, target all
        if not self.policy.target_commodities:
            self.policy.target_commodities = commodities.copy()
    
    def should_intervene(self, tick: int) -> bool:
        """Decide if intervention should occur this tick."""
        return tick > 0 and tick % self.policy.intervention_frequency == 0
    
    def decide_intervention(
        self, 
        market_stats: Dict, 
        total_economy_wealth: float
    ) -> List[Dict]:
        """
        Decide on market interventions based on inflation target.
        Returns a list of buy orders to submit.
        """
        orders = []
        if not self.policy.target_commodities:
            return orders
            
        # Calculate target money injection
        # Target is to increase money supply by inflation_rate
        target_injection = total_economy_wealth * self.policy.inflation_rate
        
        # Or use fixed size if specified and > 0 (override)
        if self.policy.intervention_size > 0:
            target_injection = self.policy.intervention_size
            
        amount_per_commodity = target_injection / len(self.policy.target_commodities)
        
        for commodity in self.policy.target_commodities:
            if commodity not in market_stats:
                continue
                
            stats = market_stats[commodity]
            current_price = stats.get('avg_price_recent', 10.0)
            if current_price <= 0:
                current_price = 10.0
            
            # Buy enough quantity to inject the target amount of money
            # Quantity = Amount / Price
            # We bid slightly above market price to ensure execution (aggressive buy)
            bid_price = current_price * 1.05
            quantity = amount_per_commodity / bid_price
            
            orders.append({
                'commodity': commodity,
                'agent_id': 'MONEY_ISSUER',
                'is_bid': True,  # Always buying to inject money
                'price': bid_price,
                'quantity': quantity
            })
            
            self.total_printed += (bid_price * quantity)
            
        self.intervention_history.append({
            'tick': self.tick_count,
            'amount': target_injection,
            'orders': len(orders)
        })
        
        return orders

    def increment_tick(self):
        self.tick_count += 1
        
    def get_statistics(self) -> Dict:
        return {
            'total_printed': self.total_printed,
            'interventions_count': len(self.intervention_history)
        }


@ray.remote
class TaxCollector:
    """
    The Inverse of MoneyIssuer: Removes money from the system.
    """
    def __init__(self, tax_rate: float = 0.01):
        self.tax_rate = tax_rate
        self.total_collected = 0.0
        self.collection_history: List[Dict] = []
    
    def collect_taxes(self, agent_states: List[Dict], tick: int) -> Dict[str, float]:
        """
        Calculate taxes for each agent.
        Returns dict of {agent_id: tax_amount}
        """
        taxes = {}
        total_round_collection = 0.0
        
        for agent in agent_states:
            # Simple wealth tax
            wealth = agent['wallet']
            if wealth > 0:
                tax_amount = wealth * self.tax_rate
                taxes[agent['agent_id']] = tax_amount
                total_round_collection += tax_amount
        
        self.total_collected += total_round_collection
        
        self.collection_history.append({
            'tick': tick,
            'amount': total_round_collection,
            'agents_taxed': len(taxes)
        })
        
        return taxes
    
    def get_statistics(self) -> Dict:
        """Get tax collection statistics."""
        return {
            'total_collected': self.total_collected,
            'collections_count': len(self.collection_history),
            'average_collection': (
                self.total_collected / len(self.collection_history)
                if self.collection_history else 0
            )
        }


class FiscalPolicy:
    """
    Coordinates MoneyIssuer (money printing) and TaxCollector.
    Allows for complex monetary experiments.
    """
    
    def __init__(
        self,
        enable_printing: bool = True,
        enable_taxes: bool = False,
        monetary_policy: Optional[MonetaryPolicy] = None,
        tax_rate: float = 0.01
    ):
        self.enable_printing = enable_printing
        self.enable_taxes = enable_taxes
        
        self.money_issuer = None
        self.tax_collector = None
        
        if enable_printing:
            policy = monetary_policy or MonetaryPolicy()
            # Will be initialized with commodities list
            self.monetary_policy = policy
        
        if enable_taxes:
            self.tax_rate = tax_rate
    
    def initialize_actors(self, commodities: List[str]):
        """Initialize Ray actors after Ray is started."""
        if self.enable_printing:
            self.money_issuer = MoneyIssuer.remote(
                policy=self.monetary_policy,
                commodities=commodities
            )
        
        if self.enable_taxes:
            self.tax_collector = TaxCollector.remote(tax_rate=self.tax_rate)
    
    async def execute_fiscal_cycle(
        self,
        market_stats: Dict,
        agent_states: List[Dict],
        tick: int
    ) -> Tuple[List[Dict], Dict[str, float]]:
        """
        Execute complete fiscal cycle: taxes + interventions.
        Returns (intervention_orders, tax_amounts)
        """
        intervention_orders = []
        tax_amounts = {}
        
        # Collect taxes first
        if self.enable_taxes and self.tax_collector:
            tax_amounts = await self.tax_collector.collect_taxes.remote(
                agent_states, tick
            )
        
        # Then intervene in market
        if self.enable_printing and self.money_issuer:
            total_wealth = sum(s['wallet'] for s in agent_states)
            intervention_orders = await self.money_issuer.decide_intervention.remote(
                market_stats,
                total_wealth
            )
            await self.money_issuer.increment_tick.remote()
        
        return intervention_orders, tax_amounts
    
    async def get_combined_statistics(self) -> Dict:
        """Get statistics from all fiscal actors."""
        stats = {}
        
        if self.money_issuer:
            stats['money_issuer'] = await self.money_issuer.get_statistics.remote()
        
        if self.tax_collector:
            stats['tax_collector'] = await self.tax_collector.get_statistics.remote()
        
        return stats
