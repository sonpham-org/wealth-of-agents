# 🌍 Wealth of Agents

**Wealth of Agents** is a sophisticated Agent-Based Economic Simulation (ABES) designed to explore **emergent economic phenomena**—such as inflation, inequality, and resource allocation—through the interactions of autonomous agents.

Built on the **Ray** distributed computing framework, it features a high-performance Limit Order Book (LOB), rational utility-maximizing agents, and an optional **Money Issuer** (central bank) to demonstrate monetary dynamics.

## 🎯 Vision

To build a realistic economic sandbox where:
- **Autonomous Agents** make trading decisions to maximize personal utility.
- **Market Microstructure** is realistic, using a continuous double auction (Limit Order Book).
- **Macroeconomic Trends** like inflation and wealth inequality emerge naturally from micro-decisions.
- **Cognitive Agents** (optional) use LLMs to reason about market conditions.

## 🏗️ Architecture

### Core Components

1. **Market Engine** ([core/market.py](core/market.py))
   - High-performance Limit Order Book (LOB) matched in O(log N).
   - Real-time price discovery for multiple commodities (Grain, Iron, Wood, Stone).
   - Price-time priority matching.

2. **Agent System** ([core/agents.py](core/agents.py))
   - Distributed actors with persistent state (inventory, wallet).
   - Utility maximization based on Cobb-Douglas preferences.
   - Production and consumption cycles (energy dynamics).

3. **Money Issuer** ([core/money_issuer.py](core/money_issuer.py))
   - The "Leviathan" / Central Bank of the simulation.
   - Inject money into the economy through open market operations (buying commodities).
   - Demonstrates the Cantillon effect and demand-pull inflation.
   - Coordinates fiscal policy including taxation.

4. **Inference Engine** ([core/inference.py](core/inference.py))
   - Centralized vLLM integration for batch processing.
   - Enables agents to "think" using Large Language Models.
   - Prefix caching for high-throughput reasoning.

5. **Simulation Orchestrator** ([core/simulation.py](core/simulation.py))
   - Synchronous tick-based execution loop (Step → Think → Act → Match).
   - Global statistics collection (Gini coefficient, GDP, Inflation).
   - WebSocket streaming for real-time visualization.

6. **Visualization** ([frontend/](frontend/))
   - Interactive HTML5/Anime.js dashboard.
   - Real-time visualizations of the agent network, order books, and price history.

## 📊 Economic Model

### Agent Utility
Agents maximize a utility function $U$:
$$U = \sum_{i} \alpha_i \ln(q_i)$$
Where agents balance their inventory $q_i$ according to preferences $\alpha_i$.

### Trade Decisions
Agents buy when Marginal Utility ($MU$) > Market Price, and sell when $MU$ < Market Price.
$$MU_i = \frac{\alpha_i}{q_i}$$

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/wealth-of-agents.git
cd wealth-of-agents

# Create virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Basic Simulation

```bash
python -m core.simulation
```

### Run with Visualization

1. **Enable WebSocket in Config**:
   In `core/simulation.py`, ensure `enable_websocket=True` or configure via arguments.

2. **Open the Visualizer**:
   Open `visualizer.html` in your web browser.

### Run with vLLM (GPU Required)

```bash
pip install vllm
# Update config to enable_llm=True
```

## 🧪 Experiments

### 1. The Inflationary Spiral
Enable the **Money Issuer** to inject currency every 10 ticks. Observe how the price of commodities rises as the money supply increases, identifying which agents benefit first (Cantillon Effect).

### 2. Wealth Inequality
Disable money printing and observe if the economy converges to a stable wealth distribution or if Pareto efficiency leads to a "rich get richer" scenario.

### 3. Supply Shocks
Simulate a drought by reducing Grain production efficiency and watch the ripple effects through the Iron and Wood markets.

## 📁 Project Structure

```
wealth-of-agents/
├── core/
│   ├── market.py           # Matching engine
│   ├── agents.py           # Ray actors
│   ├── money_issuer.py     # Central bank logic
│   ├── simulation.py       # Main loop
│   └── inference.py        # LLM wrapper
├── frontend/
│   └── index.html          # Visualization
├── requirements.txt
└── README.md
```

## 🤝 Contributing

Contributions are welcome! We are looking for:
- **Strategies**: New agent trading algorithms (RL, evolutionary).
- **Markets**: Futures, options, and lending markets.
- **Viz**: 3D visualizations of the agent economy.

## 📄 License

MIT License
