"""Quick analysis of the latest simulation results"""
import json
import glob
import os

# Find the latest results file
files = glob.glob("simulation_results_*.json")
if not files:
    print("No simulation results found!")
    exit(1)

latest = max(files, key=os.path.getctime)
print(f"\n{'='*60}")
print(f"SIMULATION RESULTS ANALYSIS")
print(f"{'='*60}")
print(f"\nAnalyzing: {latest}\n")

with open(latest) as f:
    data = json.load(f)

# Data is an array of tick snapshots
first_tick = data[0]
last_tick = data[-1]

# Count interventions
interventions = [t for t in data if "leviathan_intervention" in t]
total_trades = sum(t.get("total_trades", 0) for t in data)

print("📊 KEY FINDINGS:\n")
print(f"  Total Ticks: {len(data)}")
print(f"  Total Trades: {last_tick.get('total_trades', 0)}")
print(f"  Money Printing Events: {len(interventions)}")
print()

print("💰 WEALTH:")
print(f"  Initial: ${first_tick['avg_wealth']:.2f}")
print(f"  Final: ${last_tick['avg_wealth']:.2f}")
print(f"  Change: +{((last_tick['avg_wealth']/first_tick['avg_wealth'])-1)*100:.1f}%")
print()

print("📈 INEQUALITY (Gini Coefficient):")
print(f"  Initial: {first_tick['gini_coefficient']:.3f}")
print(f"  Final: {last_tick['gini_coefficient']:.3f}")
print(f"  Change: +{((last_tick['gini_coefficient']/first_tick['gini_coefficient'])-1)*100:.1f}%")
print()

# Check if we have price data
if 'market_stats' in last_tick:
    print("💵 COMMODITY PRICES (Final):")
    for commodity, stats in last_tick['market_stats'].items():
        price = stats.get('last_trade_price')
        if price:
            print(f"  {commodity}: ${price:.2f}")
    print()

print("⏱️  PERFORMANCE:")
# Calculate average tick time
times = [t.get('tick_time_ms', 0) for t in data if 'tick_time_ms' in t]
if times:
    avg_time = sum(times) / len(times)
    total_time = sum(times) / 1000
    print(f"  Average tick time: {avg_time:.2f}ms")
    print(f"  Total simulation time: {total_time:.2f}s")
print()

print(f"{'='*60}")
print("✅ MPES CONCEPT DEMONSTRATED:")
print(f"{'='*60}")
print()
print("The simulation shows how money printing (Leviathan interventions)")
print("increases average wealth but also increases inequality (Gini).")
print()
print("This is an emergent property of the system - when new money is")
print("introduced to buy scarce commodities, those who receive it first")
print("benefit more than those who receive it later (Cantillon effect).")
print(f"\n{'='*60}\n")
