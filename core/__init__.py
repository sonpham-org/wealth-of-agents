"""
Core package initialization for MPES.
"""

from core.market import MarketEngine, LimitOrderBook
from core.agents import EconomicAgent, AgentFactory
# from core.leviathan import Leviathan, FiscalPolicy, MonetaryPolicy  # Optional module
from core.inference import InferenceEngine, InferenceConfig
from core.simulation import MPESSimulation, SimulationConfig

__all__ = [
    'MarketEngine',
    'LimitOrderBook',
    'EconomicAgent',
    'AgentFactory',
    # 'Leviathan',
    # 'FiscalPolicy',
    # 'MonetaryPolicy',
    'InferenceEngine',
    'InferenceConfig',
    'MPESSimulation',
    'SimulationConfig',
]

__version__ = '0.1.0'
