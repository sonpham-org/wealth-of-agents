"""
Cleanup old simulation JSON files from root directory
Move them to output folder if needed
"""
import json
from pathlib import Path
from datetime import datetime
import shutil

def cleanup_old_files():
    """Move old simulation JSON files to output folder."""
    root = Path('.')
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Find old result files
    old_files = list(root.glob('simulation_results_*.json'))
    
    if not old_files:
        print("✅ No old files to clean up")
        return
    
    print(f"Found {len(old_files)} old simulation files")
    
    legacy_dir = output_dir / 'legacy_migrations'
    legacy_dir.mkdir(exist_ok=True)
    
    for old_file in old_files:
        try:
            # Load the file
            with open(old_file) as f:
                data = json.load(f)
            
            # Extract timestamp from filename
            timestamp = old_file.stem.split('_')[-1]
            
            # Create run directory
            try:
                dt = datetime.fromtimestamp(int(timestamp))
                run_id = dt.strftime("%Y%m%d_%H%M%S")
            except:
                run_id = f"legacy_{timestamp}"
            
            run_dir = legacy_dir / run_id
            run_dir.mkdir(exist_ok=True)
            
            # Save as simulation_data.json
            new_file = run_dir / 'simulation_data.json'
            shutil.copy(old_file, new_file)
            
            # Create basic metadata
            metadata = {
                'run_id': run_id,
                'legacy_file': old_file.name,
                'total_ticks': len(data) if isinstance(data, list) else data.get('total_ticks', 0),
                'migrated': datetime.now().isoformat()
            }
            
            with open(run_dir / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create empty transactions file
            with open(run_dir / 'transactions.json', 'w') as f:
                json.dump([], f)
            
            print(f"  ✓ Migrated {old_file.name} -> {run_dir}")
            
            # Remove old file
            old_file.unlink()
            
        except Exception as e:
            print(f"  ⚠️  Error migrating {old_file.name}: {e}")
    
    print(f"\n✅ Cleanup complete!")
    print(f"   Legacy files moved to: {legacy_dir}")
    print(f"\n💡 Run 'python generate_run_list.py' to update visualizer")

if __name__ == "__main__":
    cleanup_old_files()
