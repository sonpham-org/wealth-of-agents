# Wealth of Agents - Web Platform Guide

## 🎉 What's New

This is a modern web interface for the Wealth of Agents economic simulation system. It provides:

1. **Web UI** for creating and managing simulations (no command line needed!)
2. **Dual visualizers**: Modern React components + legacy HTML visualizer
3. **Cloud storage** support for permanent simulation archival
4. **Real-time monitoring** of running simulations
5. **REST API** for programmatic access

## 🚀 Getting Started

### Prerequisites
- Python 3.8+ with pip
- Node.js 20.9+ with npm
- Git

### Installation

```bash
# 1. Clone and navigate to project
cd /home/son/Desktop/GitHub/wealth-of-agents

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Node.js dependencies
cd web
npm install
cd ..
```

### Running Locally

**Option A: Quick Start (Two Terminals)**

Terminal 1 - Start API:
```bash
cd /home/son/Desktop/GitHub/wealth-of-agents
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Start Frontend:
```bash
cd /home/son/Desktop/GitHub/wealth-of-agents/web
npm run dev -- --port 3002
```

Then open: http://localhost:3002

**Option B: Background Servers**

```bash
# Start API in background
cd /home/son/Desktop/GitHub/wealth-of-agents
nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &

# Start frontend in background
cd web
nohup npm run dev -- --port 3002 > web.log 2>&1 &

# Check logs
tail -f ../api.log   # API logs
tail -f web.log      # Frontend logs
```

## 📖 Usage Guide

### Creating a Simulation

1. Navigate to http://localhost:3002
2. Click **"New Simulation"** button
3. Fill in the configuration form:
   - **Number of Agents**: 2-1000 (default: 10)
   - **Simulation Steps**: 10-10000 (default: 100)
   - **Initial Money**: Starting money per agent (default: 1000)
   - **Use Central Bank**: Enable money issuer agent
   - **Use Cognitive Agents**: Enable LLM-based reasoning (requires API keys)
   - **Commodities**: List of tradable goods
   - **Description**: Optional job description
4. Click **"Start Simulation"**
5. You'll be redirected to the simulation detail page

### Viewing Simulations

#### List View
- Navigate to "Simulations" from the navbar
- See all your simulation jobs with status badges:
  - 🟡 **Pending**: Queued, waiting to start
  - 🔵 **Running**: Currently executing
  - 🟢 **Completed**: Finished successfully
  - 🔴 **Failed**: Error occurred (click to see error details)
- Click any simulation to view details

#### Detail View
Once a simulation completes, you'll see two visualization options:

**1. Interactive Visualizer (New)**
- Modern React-based interface
- Features:
  - **Network Graph**: Visualize agent trading relationships
  - **Charts**: Wealth and energy distribution
  - **Agent Cards**: Click agents to see details
  - **Playback Controls**: Scrub through simulation timeline
  - **Live Stats**: Gini coefficient, total trades, active agents
- Fully interactive and keyboard-accessible

**2. Legacy Visualizer (Original)**
- Embedded iframe of original `visualizer.html`
- Full preservation of existing functionality
- Use this as a fallback or to compare visualizations
- Opens in dedicated browser window for full-screen experience

### Toggling Visualizers

Click the tabs at the top of the results section:
- **Interactive Visualizer** - Modern React version
- **Legacy Visualizer** - Original HTML version

Both load the same simulation data but render differently.

## 🔧 Configuration

### API Configuration

Create `/api/.env` file:

```bash
# Copy the example
cp api/.env.example api/.env

# Edit as needed
nano api/.env
```

**Important settings:**

```bash
# Storage (default: local)
STORAGE_TYPE=local

# For AWS S3 cloud storage:
# STORAGE_TYPE=s3
# S3_BUCKET_NAME=wealth-of-agents-simulations
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret
# AWS_REGION=us-east-1

# For LLM-powered cognitive agents:
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
```

### Frontend Configuration

Edit `/web/.env.local`:

```bash
# Local development
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production (after deployment)
# NEXT_PUBLIC_API_URL=https://agents-api.sonpham.net
```

## ☁️ Cloud Storage Setup

By default, simulations are stored locally in the `output/` directory. For production use, you can enable cloud storage:

### AWS S3 Setup

**See full guide in [CLOUD_STORAGE.md](CLOUD_STORAGE.md)**

Quick version:

1. **Create S3 bucket:**
   ```bash
   aws s3 mb s3://wealth-of-agents-simulations
   ```

2. **Configure credentials:**
   ```bash
   aws configure
   ```

3. **Update .env:**
   ```bash
   echo "STORAGE_TYPE=s3" >> api/.env
   echo "S3_BUCKET_NAME=wealth-of-agents-simulations" >> api/.env
   ```

4. **Restart API server**

Now all completed simulations will be automatically uploaded to S3 (while also remaining available locally).

## 📡 API Reference

### Endpoints

**Health Check**
```
GET /
Response: {"service": "Wealth of Agents API", "status": "running"}
```

**Create Job**
```
POST /jobs
Body: {
  "num_agents": 50,
  "num_steps": 200,
  "initial_money": 1000,
  "use_money_issuer": false,
  "use_cognitive_agents": false,
  "commodities": ["Grain", "Iron", "Wood"],
  "description": "Test simulation"
}
Response: {
  "id": "uuid",
  "status": "pending",
  "config": {...},
  "created_at": "2026-01-30T20:00:00"
}
```

**Get Job**
```
GET /jobs/{job_id}
Response: {
  "id": "uuid",
  "status": "completed",
  "config": {...},
  "created_at": "...",
  "started_at": "...",
  "completed_at": "...",
  "run_id": "20260130_200500",
  "output_path": "/path/to/output"
}
```

**List All Jobs**
```
GET /jobs
Response: [...]
```

**Get Job Results**
```
GET /jobs/{job_id}/results
Response: {
  "run_id": "...",
  "output_files": [...],
  "stdout": "...",
  "stderr": "..."
}
```

**List All Runs**
```
GET /runs
Response: [
  {
    "run_id": "20260130_200500",
    "timestamp": "...",
    "config": {...},
    "stats": {...}
  }
]
```

### API Documentation

Interactive docs available at: http://localhost:8000/docs

## 🎨 Customization

### Adding New Visualizations

Edit `/web/components/SimulationVisualizer.tsx`:

```tsx
// Add new chart
const myCustomChart = {
  labels: data.agents.map(a => a.id),
  datasets: [{
    label: 'My Metric',
    data: data.agents.map(a => a.myMetric),
    backgroundColor: 'rgba(255, 99, 132, 0.6)',
  }]
};

// Render in component
<div className="bg-white p-4 rounded-lg shadow">
  <h3 className="text-lg font-semibold mb-3">My Custom Chart</h3>
  <div className="h-64">
    <Bar data={myCustomChart} options={chartOptions} />
  </div>
</div>
```

### Styling

The frontend uses **Tailwind CSS**. Modify styles inline:

```tsx
<div className="bg-blue-500 text-white p-4 rounded-lg shadow-lg hover:bg-blue-600 transition-colors">
  My Custom Component
</div>
```

Or edit `/web/tailwind.config.js` for theme customization.

## 🐛 Troubleshooting

### "Cannot connect to API"
- Check API is running: `curl http://localhost:8000`
- Verify `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Check for CORS errors in browser console

### "ModuleNotFoundError: No module named 'ray'"
```bash
pip install -r requirements.txt
```

### Simulation stays "running" forever
- Check API logs: `tail -f api.log`
- Try running simulation manually:
  ```bash
  python run_simulation.py --agents 5 --ticks 50
  ```
- Check Ray is working: `python -c "import ray; ray.init(); print('OK')"`

### Visualizer shows "Loading..." forever
- Open browser DevTools → Network tab
- Check if `/output/{run_id}/simulation_data.json` returns 404
- Verify simulation completed successfully
- Try legacy visualizer as fallback

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn api.main:app --port 8001
```

## 📚 Further Reading

- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Full implementation details
- **[CLOUD_STORAGE.md](CLOUD_STORAGE.md)** - Cloud storage setup guide
- **[README.md](README.md)** - Original project README with economic model details

## 🤝 Support

Having issues? 
1. Check the troubleshooting section above
2. Review API logs: `tail -f api.log`
3. Check frontend console: Browser DevTools → Console
4. Verify all dependencies installed: `pip list` and `npm list`

---

**Happy simulating! 🎉**
