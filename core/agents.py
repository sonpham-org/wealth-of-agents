"""
Ray-based Agent System for MPES
Each agent is a stateful Ray Actor with inventory, wallet, and utility preferences.
"""

import ray
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import asyncio


@dataclass
class UtilityProfile:
    """
    Agent's utility preferences for each commodity.
    Alpha represents marginal utility coefficient.
    """
    alpha: Dict[str, float]  # Commodity -> preference weight
    
    def marginal_utility(self, commodity: str, current_inventory: float) -> float:
        """
        Calculate marginal utility: MU = α / current_inventory
        Higher α means stronger preference.
        As inventory increases, marginal utility decreases.
        """
        if commodity not in self.alpha:
            return 0.0
        
        # Avoid division by zero
        inventory = max(current_inventory, 0.01)
        return self.alpha[commodity] / inventory


@dataclass
class ProductionSkill:
    """Agent's production capabilities."""
    commodity: str  # What they produce
    efficiency: float  # Units produced per 1 energy unit
    energy_cost: float  # Energy required per production cycle


@dataclass
class AgentState:
    """Complete state of an agent."""
    agent_id: str
    inventory: Dict[str, float] = field(default_factory=dict)
    wallet: float = 100.0
    utility_profile: Optional[UtilityProfile] = None
    production_skill: Optional[ProductionSkill] = None
    energy: float = 100.0
    max_energy: float = 100.0
    consumption_needs: Dict[str, float] = field(default_factory=dict)  # Per tick consumption
    
    def total_utility(self) -> float:
        """Calculate total utility from current inventory."""
        if not self.utility_profile:
            return 0.0
        
        total = 0.0
        for commodity, quantity in self.inventory.items():
            if commodity in self.utility_profile.alpha:
                # Utility function: U = α * ln(quantity)
                total += self.utility_profile.alpha[commodity] * np.log(max(quantity, 0.01))
        return total

    def get_utility_breakdown(self) -> Dict[str, float]:
        """Return utility contributed by each commodity."""
        if not self.utility_profile:
            return {}
        
        breakdown = {}
        for commodity, quantity in self.inventory.items():
            if commodity in self.utility_profile.alpha:
                util = self.utility_profile.alpha[commodity] * np.log(max(quantity, 0.01))
                breakdown[commodity] = util
        return breakdown


@ray.remote
class EconomicAgent:
    """
    Ray Actor representing a single economic agent.
    Stateful actor that maintains inventory, wallet, and makes trading decisions.
    """
    
    def __init__(
        self,
        agent_id: str,
        initial_wallet: float,
        utility_alpha: Dict[str, float],
        production_commodity: str,
        production_efficiency: float,
        consumption_needs: Dict[str, float],
        initial_inventory: Optional[Dict[str, float]] = None
    ):
        self.state = AgentState(
            agent_id=agent_id,
            wallet=initial_wallet,
            utility_profile=UtilityProfile(alpha=utility_alpha),
            production_skill=ProductionSkill(
                commodity=production_commodity,
                efficiency=production_efficiency,
                energy_cost=50.0
            ),
            consumption_needs=consumption_needs,
            inventory=initial_inventory or {}
        )
        
        # Initialize inventory with small amounts
        self.state.inventory = {commodity: 1.0 for commodity in utility_alpha.keys()}
        
        # Trading history
        self.trade_history: List[Dict] = []
        self.decision_history: List[Dict] = []
        
        # Market Psychology State
        self.unsold_ticks: Dict[str, int] = {}  # Track how long I've been trying to sell X
        self.last_asked_prices: Dict[str, float] = {} # What I asked for last time
        self.market_sentiment: float = 1.0 # 1.0 = neutral, >1 bullish, <1 bearish
    
    def get_state(self) -> Dict:
        """Return current agent state for analysis."""
        return {
            'agent_id': self.state.agent_id,
            'wallet': self.state.wallet,
            'inventory': dict(self.state.inventory),
            'energy': self.state.energy,
            'max_energy': self.state.max_energy,
            'utility': self.state.total_utility(),
            'utility_breakdown': self.state.get_utility_breakdown()
        }
    
    def produce(self) -> Optional[Tuple[str, float]]:
        """
        Produce commodity if enough energy.
        Returns (commodity, quantity) or None.
        """
        if not self.state.production_skill:
            return None
        
        if self.state.energy >= self.state.production_skill.energy_cost:
            self.state.energy -= self.state.production_skill.energy_cost
            quantity = self.state.production_skill.efficiency
            commodity = self.state.production_skill.commodity
            
            # Add to inventory
            if commodity not in self.state.inventory:
                self.state.inventory[commodity] = 0.0
            self.state.inventory[commodity] += quantity
            
            return (commodity, quantity)
        
        return None
    
    def consume(self) -> Dict[str, float]:
        """
        Consume commodities based on needs.
        Returns dict of commodities consumed.
        """
        consumed = {}
        for commodity, need in self.state.consumption_needs.items():
            if commodity in self.state.inventory:
                actual_consumption = min(need, self.state.inventory[commodity])
                self.state.inventory[commodity] -= actual_consumption
                consumed[commodity] = actual_consumption
        
        return consumed
    
    def calculate_bid_price(self, commodity: str) -> float:
        """
        Calculate how much agent is willing to pay for a commodity.
        Based on marginal utility and current inventory.
        """
        if commodity not in self.state.inventory:
            self.state.inventory[commodity] = 0.0
        
        current_inv = self.state.inventory[commodity]
        mu = self.state.utility_profile.marginal_utility(commodity, current_inv)
        
        # Bid price proportional to marginal utility
        # Allow spending up to 40% of wallet on a single unit if desperate
        # If wallet is large (> 200), max_bid scales.
        max_bid = self.state.wallet * 0.4
        
        # Conversion factor utility -> money. 
        # If MU is 50 (desperate), bid could be 50. If MU is 1, bid is 1.
        bid_price = min(mu, max_bid)
        
        return max(bid_price, 0.01)  # Minimum bid
    
    def calculate_ask_price(self, commodity: str) -> Optional[float]:
        """
        Calculate minimum price to sell a commodity.
        Based on marginal utility of giving up inventory.
        Includes discount logic if item has been sitting unsold.
        """
        if commodity not in self.state.inventory or self.state.inventory[commodity] <= 0:
            return None
        
        current_inv = self.state.inventory[commodity]
        mu = self.state.utility_profile.marginal_utility(commodity, current_inv)
        
        # Ask price based on opportunity cost
        # We want to sell for more than the utility we lose
        base_ask_price = mu * 1.2
        
        # --- NEW LOGIC: Panic Selling / Inventory Clearance ---
        # If we have been trying to sell this for a long time, lower the price.
        unsold_duration = self.unsold_ticks.get(commodity, 0)
        discount_factor = 1.0
        
        if unsold_duration > 0:
            discount_factor = max(0.3, 1.0 - (unsold_duration * 0.1))
            
        final_ask_price = base_ask_price * discount_factor
        
        return max(final_ask_price, 0.01)
    
    def decide_trade_action(self, market_prices: Dict[str, Dict]) -> List[Dict]:
        """
        Decide what orders to place based on current market conditions.
        Returns list of orders: {'commodity': str, 'is_bid': bool, 'price': float, 'quantity': float}
        """
        orders = []
        committed_wallet = 0.0  # Track money we plan to spend this tick
        
        # Update unsold ticks based on previous round's success
        # Logic: If we listed it last time, but didn't sell it this turn (checked via trade history since last decision?), 
        # increment unsold counter.
        # Simplified: We just increment everything we "intend" to sell. 
        # If a sale happens, we reset it in execute_trade.
        
        for commodity in self.state.utility_profile.alpha.keys():
            current_inv = self.state.inventory.get(commodity, 0.0)
            mu = self.state.utility_profile.marginal_utility(commodity, current_inv)
            
            # Get market price if available
            market_info = market_prices.get(commodity, {})
            best_ask = market_info.get('best_ask')
            best_bid = market_info.get('best_bid')
            
            # --- BUYING STRATEGY ---
            # Buy if we have money and utility is decent
            # Check effective wallet (Wallet - Committed)
            available_funds = self.state.wallet - committed_wallet
            
            if mu > 0.5 and available_funds > 1.0:
                willingness_to_pay = self.calculate_bid_price(commodity)
                
                final_bid_price = willingness_to_pay
                take_market_ask = False

                # If there's a seller at a price we like, take it!
                if best_ask and best_ask <= willingness_to_pay:
                    final_bid_price = best_ask  # Match the ask to buy immediately
                    take_market_ask = True
                else:
                    # Otherwise, place a limit bid
                    if best_bid:
                         competitive_bid = best_bid * 1.05
                         final_bid_price = min(competitive_bid, willingness_to_pay)
                
                # Sizing
                affordability = available_funds / final_bid_price
                quantity = min(2.0, affordability * 0.5) 

                if quantity > 0.01 and (quantity * final_bid_price) <= available_funds:
                    orders.append({
                        'commodity': commodity,
                        'is_bid': True,
                        'price': final_bid_price,
                        'quantity': quantity
                    })
                    committed_wallet += (quantity * final_bid_price)
            
            # --- SELLING STRATEGY ---
            # Sell if we have inventory
            elif current_inv > 0.1:
                # Increment metadata for unsold tracking
                # We assume it's unsold until proven otherwise by execute_trade
                self.unsold_ticks[commodity] = self.unsold_ticks.get(commodity, 0) + 1
                
                min_ask_price = self.calculate_ask_price(commodity)
                
                if min_ask_price:
                    final_ask_price = min_ask_price
                    self.last_asked_prices[commodity] = final_ask_price
                    
                    # If there's a buyer at a price we like, take it!
                    if best_bid and best_bid >= min_ask_price:
                         final_ask_price = best_bid
                    elif best_ask:
                         # Undercut current ask to be competitive
                         competitive_ask = best_ask * 0.95
                         final_ask_price = max(competitive_ask, min_ask_price)
                    
                    # Quantity to sell
                    quantity = min(current_inv * 0.5, 5.0)  # Sell half of stock max
                    
                    if quantity > 0.01:
                        orders.append({
                            'commodity': commodity,
                            'is_bid': False,
                            'price': final_ask_price,
                            'quantity': quantity
                        })
        
        self.decision_history.append({
            'tick': len(self.decision_history),
            'orders': orders,
            'utility': self.state.total_utility()
        })
        
        return orders
    
    def execute_trade(self, trade_info: Dict):
        """
        Execute a trade (called by simulation after matching).
        Updates inventory and wallet.
        """
        if trade_info['buyer_id'] == self.state.agent_id:
            # We bought
            cost = trade_info['price'] * trade_info['quantity']
            
            # Double check affordability (though logic above tries to prevent it)
            if self.state.wallet >= cost:
                self.state.wallet -= cost
                
                commodity = trade_info['commodity']
                if commodity not in self.state.inventory:
                    self.state.inventory[commodity] = 0.0
                self.state.inventory[commodity] += trade_info['quantity']
            
        elif trade_info['seller_id'] == self.state.agent_id:
            # We sold
            revenue = trade_info['price'] * trade_info['quantity']
            self.state.wallet += revenue
            
            commodity = trade_info['commodity']
            self.state.inventory[commodity] -= trade_info['quantity']
            
            # RESET UNSOLD COUNTER - We successfully sold!
            self.unsold_ticks[commodity] = 0
    
    def reset_energy(self):
        """Reset energy to maximum (called each tick)."""
        self.state.energy = self.state.max_energy
    
    def get_llm_prompt_context(self) -> str:
        """
        Generate context string for LLM decision-making.
        This can be used for more sophisticated AI-driven trading.
        """
        context = f"""
Agent {self.state.agent_id} Status:
Wallet: ${self.state.wallet:.2f}
Energy: {self.state.energy:.1f}/{self.state.max_energy}

Inventory:
{chr(10).join(f"  {k}: {v:.2f} units" for k, v in self.state.inventory.items())}

Production Skill: {self.state.production_skill.commodity} 
  (efficiency: {self.state.production_skill.efficiency:.2f})

Utility Preferences:
{chr(10).join(f"  {k}: α={v:.2f}" for k, v in self.state.utility_profile.alpha.items())}

Current Total Utility: {self.state.total_utility():.2f}

Recent Trades: {len(self.trade_history[-5:])} in last 5 ticks
"""
        return context


class AgentFactory:
    """Factory for creating diverse agents with different profiles."""
    
    @staticmethod
    def create_random_agent(
        agent_id: str,
        commodities: List[str],
        specialization: Optional[str] = None
    ) -> ray.actor.ActorHandle:
        """
        Create an agent with random utility preferences and production skills.
        
        Now more diverse!
        """
        # Specialize in one commodity for production
        if not specialization:
            specialization = np.random.choice(commodities)
        
        # Create utility weights - Diverse Alpha!
        # Base logic: High preference for what they DON'T produce
        # Diversity logic: Random variations in preference intensity + Occasional weird preferences
        alpha = {}
        for commodity in commodities:
            if commodity == specialization:
                # Low utility for own production (they have plenty)
                # Variation: Some agents hoard their own stuff (alpha ~5-12), others don't care (~0.5-3)
                alpha[commodity] = np.random.uniform(0.5, 12.0)
            else:
                # High utility for things they need but don't produce
                # Variation: Some agents act desperate (alpha ~60), others are chill (~10)
                # Adds noise: Random "favorite" commodity they irrationally love
                is_irrationally_loved = np.random.random() < 0.1
                base_pref = np.random.uniform(10, 60)
                
                if is_irrationally_loved:
                     base_pref *= 1.5
                
                alpha[commodity] = base_pref
        
        # Production efficiency - produce MORE of specialty
        # Skill based on efficiency (output per unit energy)
        # Wider range: some are terrible (0.5), some are industrial (5.0)
        efficiency = np.random.uniform(0.5, 5.0)
        
        # Consumption needs - need LESS of what they produce, MORE of others
        consumption_needs = {}
        for commodity in commodities:
            if commodity == specialization:
                # Low consumption of own specialty
                consumption_needs[commodity] = np.random.uniform(0.01, 0.2)
            else:
                # High consumption of other commodities
                consumption_needs[commodity] = np.random.uniform(0.2, 1.2)
        
        # Initial wealth
        # Variation: Some start rich, some poor
        initial_wallet = np.random.uniform(80, 150)
        
        # Give small initial inventory of specialty
        initial_inventory = {specialization: 2.0}
        
        return EconomicAgent.remote(
            agent_id=agent_id,
            initial_wallet=initial_wallet,
            utility_alpha=alpha,
            production_commodity=specialization,
            production_efficiency=efficiency,
            consumption_needs=consumption_needs,
            initial_inventory=initial_inventory
        )
    
    @staticmethod
    def create_agent_population(
        num_agents: int,
        commodities: List[str]
    ) -> List[ray.actor.ActorHandle]:
        """Create a population of diverse agents."""
        agents = []
        
        # Ensure balanced specialization
        for i in range(num_agents):
            specialization = commodities[i % len(commodities)]
            agent = AgentFactory.create_random_agent(
                agent_id=f"agent_{i:04d}",
                commodities=commodities,
                specialization=specialization
            )
            agents.append(agent)
        
        return agents
