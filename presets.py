"""
Enhanced simulation preset configurations for more active trading
"""

# Preset configurations
PRESETS = {
    'active_trade': {
        'num_agents': 50,
        'num_ticks': 200,
        'enable_money_printing': False,
        'enable_llm': False,
        'enable_taxes': False,
        'commodities': ['grain', 'iron', 'wood', 'stone'],
        'description': 'Optimized for agent-to-agent trading'
    },
    'baseline': {
        'num_agents': 100,
        'num_ticks': 500,
        'enable_money_printing': False,
        'enable_llm': False,
        'enable_taxes': False,
        'description': 'Pure market without intervention'
    },
    'inflation': {
        'num_agents': 100,
        'num_ticks': 500,
        'enable_money_printing': True,
        'enable_llm': False,
        'enable_taxes': False,
        'inflation_rate': 0.1,
        'intervention_frequency': 20,
        'intervention_size': 1000.0,
        'description': 'Study inflation effects'
    },
    'inequality': {
        'num_agents': 200,
        'num_ticks': 1000,
        'enable_money_printing': True,
        'enable_llm': False,
        'enable_taxes': False,
        'inflation_rate': 0.05,
        'intervention_frequency': 50,
        'intervention_size': 500.0,
        'description': 'Study wealth distribution'
    },
    'deflation': {
        'num_agents': 100,
        'num_ticks': 500,
        'enable_money_printing': False,
        'enable_llm': False,
        'enable_taxes': True,
        'description': 'Study deflationary pressure'
    },
    'small': {
        'num_agents': 20,
        'num_ticks': 100,
        'enable_money_printing': True,
        'enable_llm': False,
        'enable_taxes': False,
        'inflation_rate': 0.05,
        'intervention_frequency': 20,
        'intervention_size': 500.0,
        'description': 'Quick test simulation'
    },
    'large': {
        'num_agents': 500,
        'num_ticks': 200,
        'enable_money_printing': True,
        'enable_llm': False,
        'enable_taxes': False,
        'inflation_rate': 0.05,
        'intervention_frequency': 20,
        'intervention_size': 2000.0,
        'description': 'Large-scale simulation'
    },
}
