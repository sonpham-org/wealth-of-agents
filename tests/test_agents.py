"""
Test suite for Agent system.
"""

import pytest
import ray
from core.agents import (
    EconomicAgent, 
    AgentFactory, 
    UtilityProfile, 
    ProductionSkill,
    AgentState
)


class TestUtilityProfile:
    """Test utility calculations."""
    
    def test_marginal_utility(self):
        """Test marginal utility calculation."""
        profile = UtilityProfile(alpha={"grain": 10.0})
        
        # High MU when inventory is low
        mu_low = profile.marginal_utility("grain", 1.0)
        assert mu_low == 10.0
        
        # Lower MU when inventory is high
        mu_high = profile.marginal_utility("grain", 10.0)
        assert mu_high == 1.0
    
    def test_marginal_utility_zero_inventory(self):
        """Test MU with zero inventory (should use minimum)."""
        profile = UtilityProfile(alpha={"grain": 10.0})
        
        mu = profile.marginal_utility("grain", 0.0)
        assert mu == 10.0 / 0.01  # Uses minimum inventory of 0.01


class TestAgentState:
    """Test agent state management."""
    
    def test_total_utility(self):
        """Test total utility calculation."""
        state = AgentState(
            agent_id="test_agent",
            utility_profile=UtilityProfile(alpha={"grain": 10.0, "iron": 15.0}),
            inventory={"grain": 2.0, "iron": 3.0}
        )
        
        # U = 10*ln(2) + 15*ln(3)
        import numpy as np
        expected = 10 * np.log(2) + 15 * np.log(3)
        
        assert abs(state.total_utility() - expected) < 0.01


@pytest.fixture
def ray_context():
    """Initialize Ray for tests."""
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    yield
    # Don't shutdown - other tests might need it


class TestEconomicAgent:
    """Test Economic Agent behavior."""
    
    def test_agent_creation(self, ray_context):
        """Test creating an agent."""
        agent = EconomicAgent.remote(
            agent_id="agent_001",
            initial_wallet=100.0,
            utility_alpha={"grain": 10.0, "iron": 15.0},
            production_commodity="grain",
            production_efficiency=1.0,
            consumption_needs={"grain": 0.2}
        )
        
        state = ray.get(agent.get_state.remote())
        assert state['agent_id'] == "agent_001"
        assert state['wallet'] == 100.0
    
    def test_production(self, ray_context):
        """Test commodity production."""
        agent = EconomicAgent.remote(
            agent_id="agent_001",
            initial_wallet=100.0,
            utility_alpha={"grain": 10.0},
            production_commodity="grain",
            production_efficiency=1.5,
            consumption_needs={}
        )
        
        # Produce
        result = ray.get(agent.produce.remote())
        assert result is not None
        commodity, quantity = result
        assert commodity == "grain"
        assert quantity == 1.5
        
        # Check inventory increased
        state = ray.get(agent.get_state.remote())
        assert state['inventory']['grain'] > 1.0
    
    def test_consumption(self, ray_context):
        """Test commodity consumption."""
        agent = EconomicAgent.remote(
            agent_id="agent_001",
            initial_wallet=100.0,
            utility_alpha={"grain": 10.0},
            production_commodity="grain",
            production_efficiency=1.0,
            consumption_needs={"grain": 0.5}
        )
        
        # Get initial inventory
        initial_state = ray.get(agent.get_state.remote())
        initial_grain = initial_state['inventory']['grain']
        
        # Consume
        consumed = ray.get(agent.consume.remote())
        
        # Check consumption occurred
        assert 'grain' in consumed
        
        # Check inventory decreased
        final_state = ray.get(agent.get_state.remote())
        assert final_state['inventory']['grain'] < initial_grain
    
    def test_bid_price_calculation(self, ray_context):
        """Test bid price calculation."""
        agent = EconomicAgent.remote(
            agent_id="agent_001",
            initial_wallet=100.0,
            utility_alpha={"grain": 20.0},
            production_commodity="grain",
            production_efficiency=1.0,
            consumption_needs={}
        )
        
        bid_price = ray.get(agent.calculate_bid_price.remote("grain"))
        
        # Should be positive
        assert bid_price > 0
        # Should not exceed wallet constraints
        assert bid_price <= 10.0  # 10% of 100
    
    def test_ask_price_calculation(self, ray_context):
        """Test ask price calculation."""
        agent = EconomicAgent.remote(
            agent_id="agent_001",
            initial_wallet=100.0,
            utility_alpha={"grain": 20.0},
            production_commodity="grain",
            production_efficiency=1.0,
            consumption_needs={}
        )
        
        ask_price = ray.get(agent.calculate_ask_price.remote("grain"))
        
        # Should be positive if we have inventory
        assert ask_price is None or ask_price > 0
    
    def test_trade_execution_buy(self, ray_context):
        """Test executing a buy trade."""
        agent = EconomicAgent.remote(
            agent_id="agent_001",
            initial_wallet=100.0,
            utility_alpha={"grain": 10.0},
            production_commodity="iron",
            production_efficiency=1.0,
            consumption_needs={}
        )
        
        initial_state = ray.get(agent.get_state.remote())
        initial_wallet = initial_state['wallet']
        initial_grain = initial_state['inventory']['grain']
        
        # Execute buy trade
        trade_info = {
            'buyer_id': 'agent_001',
            'seller_id': 'agent_002',
            'commodity': 'grain',
            'price': 10.0,
            'quantity': 2.0
        }
        ray.get(agent.execute_trade.remote(trade_info))
        
        final_state = ray.get(agent.get_state.remote())
        
        # Check wallet decreased
        assert final_state['wallet'] == initial_wallet - 20.0
        # Check inventory increased
        assert final_state['inventory']['grain'] == initial_grain + 2.0
    
    def test_trade_execution_sell(self, ray_context):
        """Test executing a sell trade."""
        agent = EconomicAgent.remote(
            agent_id="agent_001",
            initial_wallet=100.0,
            utility_alpha={"grain": 10.0},
            production_commodity="grain",
            production_efficiency=1.0,
            consumption_needs={}
        )
        
        initial_state = ray.get(agent.get_state.remote())
        initial_wallet = initial_state['wallet']
        initial_grain = initial_state['inventory']['grain']
        
        # Execute sell trade
        trade_info = {
            'buyer_id': 'agent_002',
            'seller_id': 'agent_001',
            'commodity': 'grain',
            'price': 15.0,
            'quantity': 0.5
        }
        ray.get(agent.execute_trade.remote(trade_info))
        
        final_state = ray.get(agent.get_state.remote())
        
        # Check wallet increased
        assert final_state['wallet'] == initial_wallet + 7.5
        # Check inventory decreased
        assert final_state['inventory']['grain'] == initial_grain - 0.5


class TestAgentFactory:
    """Test agent factory."""
    
    def test_create_random_agent(self, ray_context):
        """Test creating a random agent."""
        commodities = ["grain", "iron", "wood"]
        agent = AgentFactory.create_random_agent(
            "agent_001",
            commodities,
            specialization="grain"
        )
        
        state = ray.get(agent.get_state.remote())
        assert state['agent_id'] == "agent_001"
        assert state['wallet'] > 0
    
    def test_create_agent_population(self, ray_context):
        """Test creating a population of agents."""
        commodities = ["grain", "iron"]
        agents = AgentFactory.create_agent_population(10, commodities)
        
        assert len(agents) == 10
        
        # Check all agents are functional
        states = ray.get([agent.get_state.remote() for agent in agents])
        assert len(states) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
