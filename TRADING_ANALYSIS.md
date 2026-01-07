# Why Is There Little Agent-to-Agent Trading?

## The Problem

You've noticed that most trades are between Money Issuer (the money printer) and agents, with very few agent-to-agent trades. This is happening for several reasons:

## Root Causes

### 1. **Agents Are Self-Sufficient**

Each agent produces exactly one commodity that they also need:
- They produce it for themselves
- They consume what they produce
- Little incentive to trade

**In core/agents.py:**
```python
# Agents produce their specialty
commodity = self.state.production_skill.commodity

# But they also need that same commodity
self.state.consumption_needs = {commodity: 0.5}
```

### 2. **Narrow Marginal Utility Range**

Current decision logic (calculate_bid_price):
```python
if mu > 5.0 and self.state.wallet > 10.0:
    # Place bid
```

This threshold is TOO HIGH. Most agents never reach MU > 5.0 because:
- They produce their own needs
- Inventory stays balanced
- No desperation to buy

### 3. **Money Issuer Dominates the Market**

When money printing is enabled:
- Money Issuer buys commodities directly
- Agents sell to Money Issuer (easy money!)
- No need to trade with each other
- Leviathan becomes the sole buyer

### 4. **No Specialization**

Agents should specialize in what they're GOOD at, not what they NEED:
- A "grain specialist" should need iron, wood, stone (not grain)
- Forces them to trade production for consumption
- Creates market demand

## Solutions

### Solution 1: Decouple Production from Consumption

Make agents produce what they're good at, consume what they're NOT producing:

```python
# In AgentFactory.create_agent_population()
for i in range(num_agents):
    # Specialize in ONE commodity
    production_commodity = commodities[i % len(commodities)]
    
    # Need ALL OTHER commodities
    consumption_needs = {
        c: 0.5 for c in commodities if c != production_commodity
    }
    
    # High utility for what they DON'T produce
    utility_alpha = {
        c: 20.0 if c != production_commodity else 1.0 
        for c in commodities
    }
```

### Solution 2: Lower Trading Thresholds

Make agents more willing to trade:

```python
# In decide_trade_action()
# OLD: if mu > 5.0 and self.state.wallet > 10.0:
# NEW: if mu > 2.0 and self.state.wallet > 5.0:  # More aggressive
    
# Also trade more quantity
quantity = min(5.0, self.state.wallet / bid_price)  # Buy up to 5 units
```

### Solution 3: Reduce Leviathan Intervention

Make Leviathan intervene less frequently:

```python
# In simulation config
intervention_frequency = 100  # Instead of 20
intervention_size = 100.0     # Instead of 500
```

Or disable completely:
```python
enable_money_printing = False
```

### Solution 4: Add Consumption Pressure

Make agents NEED to consume or suffer utility loss:

```python
# In consume()
for commodity, need in self.state.consumption_needs.items():
    shortage = need - self.state.inventory.get(commodity, 0)
    if shortage > 0:
        # Penalty for not meeting needs
        utility_penalty = shortage * 10
```

## Quick Fix Implementation

I'll create a new agent factory configuration that fixes this:

### File: `core/better_agents.py`

```python
def create_specialized_agents(num_agents, commodities):
    """
    Create agents that are specialized producers but need other commodities.
    This forces them to trade in the market.
    """
    agents = []
    
    for i in range(num_agents):
        # Each agent specializes in ONE commodity
        specialty = commodities[i % len(commodities)]
        
        # They need EVERYTHING ELSE
        consumption_needs = {}
        utility_weights = {}
        
        for commodity in commodities:
            if commodity == specialty:
                # Low need for what they produce
                consumption_needs[commodity] = 0.1
                utility_weights[commodity] = 1.0
            else:
                # High need for what they DON'T produce
                consumption_needs[commodity] = 0.8
                utility_weights[commodity] = 25.0  # Strong preference
        
        # Higher production efficiency
        production_efficiency = 2.0  # Produce 2 units per tick
        
        agent = EconomicAgent.remote(
            agent_id=f"agent_{str(i).zfill(4)}",
            initial_wallet=100.0,
            utility_alpha=utility_weights,
            production_commodity=specialty,
            production_efficiency=production_efficiency,
            energy_cost=10.0,
            consumption_needs=consumption_needs,
            initial_inventory={commodity: 1.0 for commodity in commodities}
        )
        
        agents.append(agent)
    
    return agents
```

## Testing the Fix

Run a simulation with these parameters:

```powershell
python run_simulation.py --agents 40 --no-money-printing --ticks 200
```

Expected results:
- **Before**: 90% Leviathan trades, 10% agent-agent
- **After**: 0% Leviathan, 100% agent-agent trades
- Agents desperate for commodities they don't produce
- Active bidding and asking
- Price discovery through supply/demand

## Metrics to Watch

After implementing fixes:

1. **Trade Distribution**
   - Count agent-to-agent vs Leviathan trades
   - Should be 80%+ agent-agent

2. **Order Book Activity**
   - More bids and asks
   - Tighter spreads
   - Frequent matching

3. **Price Volatility**
   - Prices should fluctuate more
   - Reflect scarcity and abundance

4. **Agent Utility**
   - Should vary more widely
   - Agents with shortages have low utility
   - Successful traders have high utility

## Next Steps

1. **Modify `core/agents.py`** - Implement specialized agent creation
2. **Update `AgentFactory`** - Use new specialization logic
3. **Run test simulation** - Verify more trades
4. **Tune parameters** - Adjust thresholds and needs
5. **Re-run visualizer** - See active network graph!

The agent network graph will come alive - instead of a star pattern (everyone trading with Leviathan), you'll see a mesh network with many interconnections.
