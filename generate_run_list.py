"""
Generate list of available simulation runs for the visualizer
"""
import json
from pathlib import Path
from datetime import datetime

def generate_run_list(output_dir="output"):
    """Scan output directory and generate list of runs."""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"Output directory '{output_dir}' not found")
        return
    
    runs = []
    
    # Scan all subdirectories
    for run_dir in output_path.iterdir():
        if not run_dir.is_dir():
            continue
        
        metadata_file = run_dir / "metadata.json"
        if not metadata_file.exists():
            continue
        
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            # Parse run ID to get date/time
            run_id = metadata['run_id']
            try:
                date_obj = datetime.strptime(run_id, "%Y%m%d_%H%M%S")
                date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except:
                date_str = run_id
            
            run_info = {
                'path': str(run_dir).replace('\\', '/'),
                'run_id': run_id,
                'date': date_str,
                'agents': metadata['config']['num_agents'],
                'ticks': metadata['total_ticks'],
                'trades': metadata['total_trades'],
                'money_printing': metadata['config']['enable_money_printing']
            }
            
            runs.append(run_info)
            
        except Exception as e:
            print(f"Error processing {run_dir}: {e}")
            continue
    
    # Sort by date (newest first)
    runs.sort(key=lambda x: x['run_id'], reverse=True)
    
    # Save to JSON
    output_file = Path('list_runs.json')
    with open(output_file, 'w') as f:
        json.dump(runs, f, indent=2)
    
    print(f"✅ Generated run list with {len(runs)} simulations")
    print(f"   Saved to: {output_file}")
    print(f"\nAvailable runs:")
    for run in runs[:5]:  # Show first 5
        print(f"  • {run['date']}: {run['agents']} agents, {run['ticks']} ticks, {run['trades']} trades")
    
    if len(runs) > 5:
        print(f"  ... and {len(runs) - 5} more")
    
    print(f"\n💡 Open visualizer.html in your browser to view!")

if __name__ == "__main__":
    generate_run_list()
