"""
Utility functions for data analysis and visualization.
"""

import json
import numpy as np
import pandas as pd
from typing import List, Dict
import matplotlib.pyplot as plt


def load_simulation_results(filename: str) -> List[Dict]:
    """Load simulation results from JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)


def create_dataframe(simulation_data: List[Dict]) -> pd.DataFrame:
    """Convert simulation data to pandas DataFrame."""
    
    rows = []
    for tick_data in simulation_data:
        row = {
            'tick': tick_data['tick'],
            'total_trades': tick_data['total_trades'],
            'total_orders': tick_data['total_orders'],
            'avg_wealth': tick_data['avg_wealth'],
            'total_utility': tick_data['total_utility'],
            'gini_coefficient': tick_data['gini_coefficient']
        }
        
        # Add commodity prices
        for commodity, price in tick_data.get('avg_prices', {}).items():
            row[f'price_{commodity}'] = price
        
        rows.append(row)
    
    return pd.DataFrame(rows)


def plot_price_trends(df: pd.DataFrame, output_file: str = 'price_trends.png'):
    """Plot commodity price trends over time."""
    
    price_cols = [col for col in df.columns if col.startswith('price_')]
    
    if not price_cols:
        print("No price data found")
        return
    
    plt.figure(figsize=(12, 6))
    
    for col in price_cols:
        commodity = col.replace('price_', '')
        plt.plot(df['tick'], df[col], label=commodity.capitalize(), linewidth=2)
    
    plt.xlabel('Tick', fontsize=12)
    plt.ylabel('Price ($)', fontsize=12)
    plt.title('Commodity Price Trends', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"✓ Saved price trends to {output_file}")


def plot_wealth_distribution(df: pd.DataFrame, output_file: str = 'wealth_dist.png'):
    """Plot wealth and inequality metrics."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Average wealth
    ax1.plot(df['tick'], df['avg_wealth'], linewidth=2, color='green')
    ax1.set_xlabel('Tick')
    ax1.set_ylabel('Average Wealth ($)')
    ax1.set_title('Average Wealth Over Time')
    ax1.grid(alpha=0.3)
    
    # Gini coefficient
    ax2.plot(df['tick'], df['gini_coefficient'], linewidth=2, color='red')
    ax2.set_xlabel('Tick')
    ax2.set_ylabel('Gini Coefficient')
    ax2.set_title('Inequality Over Time')
    ax2.grid(alpha=0.3)
    ax2.axhline(y=0.4, color='orange', linestyle='--', alpha=0.5, label='High Inequality Threshold')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"✓ Saved wealth distribution to {output_file}")


def calculate_inflation_rate(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate inflation rate for each commodity."""
    
    inflation_rates = {}
    
    price_cols = [col for col in df.columns if col.startswith('price_')]
    
    for col in price_cols:
        commodity = col.replace('price_', '')
        initial_price = df[col].iloc[0]
        final_price = df[col].iloc[-1]
        
        if initial_price > 0:
            inflation = ((final_price / initial_price) - 1) * 100
            inflation_rates[commodity] = inflation
    
    return inflation_rates


def generate_summary_report(simulation_data: List[Dict]) -> str:
    """Generate a text summary of simulation results."""
    
    df = create_dataframe(simulation_data)
    
    initial = df.iloc[0]
    final = df.iloc[-1]
    
    report = []
    report.append("="*60)
    report.append("SIMULATION SUMMARY REPORT")
    report.append("="*60)
    report.append(f"\nSimulation Duration: {len(simulation_data)} ticks")
    report.append(f"Total Trades Executed: {df['total_trades'].sum():,}")
    
    report.append("\n--- WEALTH METRICS ---")
    report.append(f"Initial Average Wealth: ${initial['avg_wealth']:.2f}")
    report.append(f"Final Average Wealth: ${final['avg_wealth']:.2f}")
    wealth_change = ((final['avg_wealth'] / initial['avg_wealth']) - 1) * 100
    report.append(f"Wealth Change: {wealth_change:+.2f}%")
    
    report.append("\n--- INEQUALITY METRICS ---")
    report.append(f"Initial Gini: {initial['gini_coefficient']:.4f}")
    report.append(f"Final Gini: {final['gini_coefficient']:.4f}")
    report.append(f"Average Gini: {df['gini_coefficient'].mean():.4f}")
    
    report.append("\n--- INFLATION ANALYSIS ---")
    inflation_rates = calculate_inflation_rate(df)
    for commodity, rate in inflation_rates.items():
        report.append(f"{commodity.capitalize()}: {rate:+.2f}%")
    
    report.append("\n--- MARKET ACTIVITY ---")
    report.append(f"Average Trades per Tick: {df['total_trades'].mean():.1f}")
    report.append(f"Average Orders per Tick: {df['total_orders'].mean():.1f}")
    report.append(f"Peak Trading Activity: {df['total_trades'].max()} trades (tick {df.loc[df['total_trades'].idxmax(), 'tick']})")
    
    report.append("\n" + "="*60)
    
    return "\n".join(report)


def export_to_csv(simulation_data: List[Dict], output_file: str = 'simulation_data.csv'):
    """Export simulation data to CSV."""
    df = create_dataframe(simulation_data)
    df.to_csv(output_file, index=False)
    print(f"✓ Exported data to {output_file}")


def analyze_results(results_file: str):
    """Complete analysis of simulation results."""
    
    print("📊 Analyzing simulation results...")
    
    # Load data
    data = load_simulation_results(results_file)
    df = create_dataframe(data)
    
    # Generate plots
    plot_price_trends(df)
    plot_wealth_distribution(df)
    
    # Generate summary
    report = generate_summary_report(data)
    print(report)
    
    # Save report
    with open('simulation_report.txt', 'w') as f:
        f.write(report)
    print("\n✓ Saved report to simulation_report.txt")
    
    # Export CSV
    export_to_csv(data)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        results_file = sys.argv[1]
        analyze_results(results_file)
    else:
        print("Usage: python analysis_utils.py <results_file.json>")
