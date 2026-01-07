
content = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MPES Simulation Visualizer</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Vis-Network CSS -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" rel="stylesheet" type="text/css" />

    <style>
        body { padding-top: 20px; background-color: #f8f9fa; }
        .card { margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: none; }
        .agent-card { 
            width: 140px; 
            height: 160px; 
            float: left; 
            margin: 5px; 
            padding: 8px;
            font-size: 0.75em; 
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            overflow: hidden;
        }
        .agent-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .agent-card.active { background-color: #d1e7dd; border: 2px solid #198754; }
        .agent-card.money_issuer { background-color: #f8d7da; border-color: #dc3545; }
        .inventory-list { text-align: left; margin-top: 5px; font-size: 0.85em; }
        .inventory-item { display: flex; justify-content: space-between; }
        
        #network-container { height: 600px; border: 1px solid #dee2e6; background: white; border-radius: 4px; }
        .control-panel { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .stat-value { font-size: 1.5rem; font-weight: bold; color: #2c3e50; }
        .stat-label { font-size: 0.9rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; }
        .chart-container { height: 300px; }
        
        /* Market Depth Bars */
        .depth-bar-container { display: flex; height: 200px; align-items: flex-end; gap: 2px; }
        .depth-bar { width: 10px; background: #ccc; }
        .depth-bar.bid { background: #2ecc71; }
        .depth-bar.ask { background: #e74c3c; }
    </style>
</head>
<body>

<div class="container-fluid">
    <!-- Header & Run Selection -->
    <div class="row mb-3">
        <div class="col-12">
            <div class="card">
                <div class="card-body d-flex justify-content-between align-items-center">
                    <h3 class="m-0"><i class="fas fa-chart-line text-primary me-2"></i>MPES Visualizer</h3>
                    <div class="d-flex gap-2">
                        <select id="runSelect" class="form-select" style="width: 300px;">
                            <option value="">Loading runs...</option>
                        </select>
                        <button id="loadBtn" class="btn btn-primary"><i class="fas fa-upload me-1"></i> Load Run</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Controls -->
    <div class="row mb-3">
        <div class="col-12">
            <div class="control-panel d-flex align-items-center gap-3">
                <button id="playBtn" class="btn btn-success rounded-circle" style="width: 50px; height: 50px;"><i class="fas fa-play"></i></button>
                <button id="pauseBtn" class="btn btn-warning rounded-circle d-none" style="width: 50px; height: 50px;"><i class="fas fa-pause"></i></button>
                
                <div class="flex-grow-1">
                    <label for="tickSlider" class="form-label d-flex justify-content-between">
                        <span>Current Tick: <span id="currentTickDisplay" class="fw-bold">0</span></span>
                        <span>Max Tick: <span id="maxTickDisplay">0</span></span>
                    </label>
                    <input type="range" class="form-range" id="tickSlider" min="0" max="0" value="0">
                </div>
                
                <div class="d-flex align-items-center gap-2">
                    <label class="mb-0">Speed:</label>
                    <select id="speedSelect" class="form-select form-select-sm" style="width: 100px;">
                        <option value="1000">Slow</option>
                        <option value="500" selected>Normal</option>
                        <option value="100">Fast</option>
                        <option value="10">Turbo</option>
                    </select>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div id="dashboard" class="d-none">
        
        <!-- Key Stats Row -->
        <div class="row mb-3">
            <div class="col-md-2">
                <div class="card p-3 text-center">
                    <div class="stat-label">Avg Wealth</div>
                    <div class="stat-value" id="valAvgWealth">-</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card p-3 text-center">
                    <div class="stat-label">Gini Coeff</div>
                    <div class="stat-value" id="valGini">-</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card p-3 text-center">
                    <div class="stat-label">Avg Utility</div>
                    <div class="stat-value" id="valAvgUtility">-</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card p-3 text-center">
                    <div class="stat-label">Tick Trades</div>
                    <div class="stat-value" id="valTickTrades">-</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card p-3 text-center">
                    <div class="stat-label">Total Trades</div>
                    <div class="stat-value" id="valTotalTrades">-</div>
                </div>
            </div>
             <div class="col-md-2">
                <div class="card p-3 text-center">
                    <div class="stat-label">Money Issuer</div>
                    <div class="stat-value" id="valMoneyIssuer">Inactive</div>
                </div>
            </div>
        </div>

        <!-- Tabs -->
        <ul class="nav nav-tabs mb-3" id="mainTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="summary-tab" data-bs-toggle="tab" data-bs-target="summary" type="button" role="tab"><i class="fas fa-chart-pie me-1"></i> Summary</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="market-tab" data-bs-toggle="tab" data-bs-target="market" type="button" role="tab"><i class="fas fa-balance-scale me-1"></i> Market</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="agents-tab" data-bs-toggle="tab" data-bs-target="agents" type="button" role="tab"><i class="fas fa-users me-1"></i> Agents</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="network-tab" data-bs-toggle="tab" data-bs-target="network" type="button" role="tab"><i class="fas fa-project-diagram me-1"></i> Network</button>
            </li>
        </ul>

        <div class="tab-content" id="mainTabsContent">
            
            <!-- Summary Tab -->
            <div class="tab-pane fade show active" id="summary" role="tabpanel">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header fw-bold">Commodity Prices</div>
                            <div class="card-body">
                                <div class="chart-container">
                                    <canvas id="priceChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header fw-bold">Economic Indicators</div>
                            <div class="card-body">
                                <div class="chart-container">
                                    <canvas id="ecoChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Market Tab -->
            <div class="tab-pane fade" id="market" role="tabpanel">
                <div class="row mb-3">
                    <div class="col-md-4">
                        <select id="marketCommoditySelect" class="form-select">
                            <!-- Options filled by JS -->
                        </select>
                    </div>
                    <div class="col-md-8 d-flex align-items-center gap-3">
                         <div>Current Price: <span id="marketPrice" class="fw-bold">-</span></div>
                         <div>Spread: <span id="marketSpread" class="fw-bold">-</span></div>
                         <div>Volume: <span id="marketVolume" class="fw-bold">-</span></div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-header fw-bold">Order Book (Market Depth)</div>
                            <div class="card-body">
                                <div class="chart-container">
                                    <canvas id="orderBookChart"></canvas>
                                </div>
                                <div class="text-center small mt-2">
                                    <span class="text-success"><i class="fas fa-square"></i> Bids (Buys)</span>
                                    <span class="mx-2">|</span>
                                    <span class="text-danger"><i class="fas fa-square"></i> Asks (Sells)</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header fw-bold">Market Depth Table</div>
                             <div class="card-body p-0">
                                 <table class="table table-sm table-striped mb-0 text-center" style="font-size: 0.85em;">
                                    <thead>
                                        <tr>
                                            <th>Type</th>
                                            <th>Price</th>
                                            <th>Qty</th>
                                        </tr>
                                    </thead>
                                    <tbody id="orderBookTable">
                                        <!-- Rows -->
                                    </tbody>
                                 </table>
                             </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Agents Tab -->
            <div class="tab-pane fade" id="agents" role="tabpanel">
                <div class="card">
                    <div class="card-body bg-light">
                        <div id="agentsGrid" class="clearfix">
                            <!-- Agent cards injected here -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- Network Tab -->
            <div class="tab-pane fade" id="network" role="tabpanel">
                 <div class="row">
                     <div class="col-md-9">
                        <div id="network-container"></div>
                     </div>
                     <div class="col-md-3">
                         <div class="card h-100">
                             <div class="card-header fw-bold">Key Transactions</div>
                             <div class="card-body" id="transactionList" style="overflow-y: auto; max-height: 600px;">
                                 <div class="text-muted text-center mt-5">Select a tick to view transactions</div>
                             </div>
                         </div>
                     </div>
                 </div>
            </div>
        </div>

    </div>
</div>

<!-- Scripts -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>

<script>
// State
let simulationData = [];
let transactions = [];
let metadata = {};
let currentTick = 0;
let isPlaying = false;
let playInterval = null;
let network = null;
let networkData = { nodes: null, edges: null };  // Vis DataSets
let charts = {};

let agentTradeCounts = {}; 

// Elements
const els = {
    runSelect: document.getElementById('runSelect'),
    loadBtn: document.getElementById('loadBtn'),
    playBtn: document.getElementById('playBtn'),
    pauseBtn: document.getElementById('pauseBtn'),
    tickSlider: document.getElementById('tickSlider'),
    currentTickDisplay: document.getElementById('currentTickDisplay'),
    maxTickDisplay: document.getElementById('maxTickDisplay'),
    speedSelect: document.getElementById('speedSelect'),
    dashboard: document.getElementById('dashboard'),
    // Stats
    valAvgWealth: document.getElementById('valAvgWealth'),
    valGini: document.getElementById('valGini'),
    valAvgUtility: document.getElementById('valAvgUtility'),
    valTickTrades: document.getElementById('valTickTrades'),
    valTotalTrades: document.getElementById('valTotalTrades'),
    valMoneyIssuer: document.getElementById('valMoneyIssuer'),
    // Containers
    agentsGrid: document.getElementById('agentsGrid'),
    transactionList: document.getElementById('transactionList'),
    networkContainer: document.getElementById('network-container'),
    // Market Items
    marketCommoditySelect: document.getElementById('marketCommoditySelect'),
    marketPrice: document.getElementById('marketPrice'),
    marketSpread: document.getElementById('marketSpread'),
    marketVolume: document.getElementById('marketVolume'),
    orderBookTable: document.getElementById('orderBookTable'),
};

// Initialize
async function init() {
    try {
        const response = await fetch('list_runs.json');
        const runs = await response.json();
        
        els.runSelect.innerHTML = '<option value="">Select a run...</option>';
        runs.reverse().forEach(run => {
            const option = document.createElement('option');
            option.value = run.path; 
            option.textContent = `${run.date} (Run ID: ${run.run_id}) - ${run.agents} Agents, ${run.ticks} Ticks`;
            els.runSelect.appendChild(option);
        });

        if(runs.length > 0) els.runSelect.selectedIndex = 1;

    } catch (e) {
        console.error("Error loading run list:", e);
        els.runSelect.innerHTML = '<option value="">Error loading list_runs.json</option>';
    }

    setupEventListeners();
}

function setupEventListeners() {
    els.loadBtn.addEventListener('click', loadSelectedRun);
    
    els.playBtn.addEventListener('click', () => {
        isPlaying = true;
        togglePlayControls();
        play();
    });
    
    els.pauseBtn.addEventListener('click', () => {
        isPlaying = false;
        togglePlayControls();
        stop();
    });

    els.tickSlider.addEventListener('input', (e) => {
        currentTick = parseInt(e.target.value);
        updateView();
    });

    els.speedSelect.addEventListener('change', () => {
        if (isPlaying) {
            stop();
            play();
        }
    });
    
    // Market Select Change
    els.marketCommoditySelect.addEventListener('change', () => {
        updateMarket(simulationData[currentTick]);
    });

    // Resize network
    document.getElementById('network-tab').addEventListener('shown.bs.tab', () => {
        if (network) network.fit();
    });
}

function togglePlayControls() {
    if (isPlaying) {
        els.playBtn.classList.add('d-none');
        els.pauseBtn.classList.remove('d-none');
    } else {
        els.playBtn.classList.remove('d-none');
        els.pauseBtn.classList.add('d-none');
    }
}

function play() {
    const interval = parseInt(els.speedSelect.value);
    playInterval = setInterval(() => {
        if (currentTick < simulationData.length - 1) {
            currentTick++;
            els.tickSlider.value = currentTick;
            updateView();
        } else {
            isPlaying = false;
            togglePlayControls();
            stop();
        }
    }, interval);
}

function stop() {
    clearInterval(playInterval);
}

async function loadSelectedRun() {
    const path = els.runSelect.value;
    if (!path) return;

    stop();
    isPlaying = false;
    togglePlayControls();
    els.loadBtn.textContent = 'Loading...';
    els.loadBtn.disabled = true;

    try {
        const [simDataRes, transRes, metaRes] = await Promise.all([
            fetch(`${path}/simulation_data.json`),
            fetch(`${path}/transactions.json`),
            fetch(`${path}/metadata.json`)
        ]);

        if (!simDataRes.ok || !transRes.ok || !metaRes.ok) throw new Error("Failed to load data files");

        simulationData = await simDataRes.json();
        transactions = await transRes.json();
        metadata = await metaRes.json();

        processData();
        initVisualization();

        els.dashboard.classList.remove('d-none');
        
    } catch (e) {
        alert("Error loading run data: " + e.message);
        console.error(e);
    } finally {
        els.loadBtn.textContent = 'Load Run';
        els.loadBtn.disabled = false;
    }
}

function processData() {
    currentTick = 0;
    agentTradeCounts = {}; 
    
    els.tickSlider.max = simulationData.length - 1;
    els.tickSlider.value = 0;
    els.maxTickDisplay.textContent = simulationData.length - 1;

    // Populate commodity select
    const run0 = simulationData[0];
    if (run0 && run0.market_stats) {
        els.marketCommoditySelect.innerHTML = '';
        Object.keys(run0.market_stats).forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c.charAt(0).toUpperCase() + c.slice(1);
            els.marketCommoditySelect.appendChild(opt);
        });
    }

    transactionsByTick = Array(simulationData.length).fill().map(() => []);
    transactions.forEach(t => {
        if (t.tick < transactionsByTick.length) {
            transactionsByTick[t.tick].push(t);
        }
    });
}

function initVisualization() {
    // Reset network explicitly
    networkData = { nodes: new vis.DataSet([]), edges: new vis.DataSet([]) };
    
    // Clear existing network instance if exists (optional but safer)
    if(network) {
        network.destroy();
        network = null;
    }

    updateView();
    initCharts();
    initNetwork();
}

function updateView() {
    els.currentTickDisplay.textContent = currentTick;
    const data = simulationData[currentTick];
    const tickTransactions = transactionsByTick[currentTick] || [];

    if (!data) return;

    // 1. Text Stats
    els.valAvgWealth.textContent = data.avg_wealth.toFixed(2);
    els.valGini.textContent = data.gini_coefficient.toFixed(3);
    els.valAvgUtility.textContent = data.avg_utility.toFixed(2);
    els.valTickTrades.textContent = tickTransactions.length;
    els.valTotalTrades.textContent = data.total_trades;
    
    if (data.money_issuer_active) {
         els.valMoneyIssuer.textContent = "ACTIVE";
         els.valMoneyIssuer.parentElement.classList.add('bg-danger', 'text-white');
         els.valMoneyIssuer.style.color = 'white';
    } else {
         els.valMoneyIssuer.textContent = "Inactive";
         els.valMoneyIssuer.parentElement.classList.remove('bg-danger', 'text-white');
         els.valMoneyIssuer.style.color = null;
    }

    updateCharts(currentTick);
    updateAgents(data, tickTransactions);
    updateNetwork(data, tickTransactions);
    updateMarket(data);
}

function updateMarket(data) {
    const commodity = els.marketCommoditySelect.value;
    if (!commodity || !data.market_stats || !data.market_stats[commodity]) return;

    const stats = data.market_stats[commodity];
    
    // Stats
    els.marketPrice.textContent = stats.avg_price_recent ? stats.avg_price_recent.toFixed(2) : '-';
    els.marketSpread.textContent = stats.spread ? stats.spread.toFixed(2) : '-';
    els.marketVolume.textContent = stats.total_trades; // Total accumulated trades

    // Order Book Visualization
    // Need data.order_books (newly added)
    if (data.order_books && data.order_books[commodity]) {
        const book = data.order_books[commodity];
        updateOrderBookChart(book);
    }
}

function updateOrderBookChart(book) {
    // book has { bids: [{price, qty, agent}], asks: [...] }
    const bids = book.bids || [];
    const asks = book.asks || [];
    
    // Table Update
    let html = '';
    // Show top 5 asks (reversed so lowest is bottom) and top 5 bids
    const asksToShow = [...asks].reverse().slice(-5);
    const bidsToShow = bids.slice(0, 5);

    asksToShow.forEach(o => {
        html += `<tr class="text-danger"><td><i class="fas fa-arrow-down"></i> Ask</td><td>${o.price.toFixed(2)}</td><td>${o.quantity.toFixed(1)}</td></tr>`;
    });
    html += `<tr class="table-active"><td colspan="3"><small>Spread</small></td></tr>`;
    bidsToShow.forEach(o => {
        html += `<tr class="text-success"><td><i class="fas fa-arrow-up"></i> Bid</td><td>${o.price.toFixed(2)}</td><td>${o.quantity.toFixed(1)}</td></tr>`;
    });
    els.orderBookTable.innerHTML = html;

    // Chart Update
    // Create a distribution for the chart
    // We want price on X, Quantity on Y.
    // Bids on left, Asks on right.
    const allOrders = [];
    bids.forEach(b => allOrders.push({ x: b.price, y: b.quantity, type: 'bid' }));
    asks.forEach(a => allOrders.push({ x: a.price, y: a.quantity, type: 'ask' }));
    
    // Sort by price
    allOrders.sort((a,b) => a.x - b.x);

    const labels = allOrders.map(o => o.x.toFixed(2));
    const bidData = allOrders.map(o => o.type === 'bid' ? o.y : null);
    const askData = allOrders.map(o => o.type === 'ask' ? o.y : null);

    if (charts.orderBook) {
        charts.orderBook.data.labels = labels;
        charts.orderBook.data.datasets[0].data = bidData;
        charts.orderBook.data.datasets[1].data = askData;
        charts.orderBook.update();
    }
}


function initCharts() {
    const commonOptions = {
        responsive: true, 
        maintainAspectRatio: false,
        animation: false,
        elements: { point: { radius: 0 } }
    };

    // Prices Chart
    const ctxPrice = document.getElementById('priceChart').getContext('2d');
    const commodities = Object.keys(simulationData[currentTick].market_stats || {});
    const datasets = commodities.map((c, i) => ({
        label: c,
        data: [],
        borderColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'][i % 4],
        borderWidth: 2,
        fill: false
    }));

    if (charts.prices) charts.prices.destroy();
    charts.prices = new Chart(ctxPrice, {
        type: 'line',
        data: { labels: [], datasets: datasets },
        options: { ...commonOptions, plugins: { title: { display: false } } }
    });

    // Economy Chart
    const ctxEco = document.getElementById('ecoChart').getContext('2d');
    if (charts.eco) charts.eco.destroy();
    charts.eco = new Chart(ctxEco, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Avg Wealth', data: [], borderColor: '#2ecc71', yAxisID: 'y' },
                { label: 'Gini Coeff', data: [], borderColor: '#e74c3c', yAxisID: 'y1' }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                y: { type: 'linear', display: true, position: 'left' },
                y1: { type: 'linear', display: true, position: 'right', min: 0, max: 1 }
            }
        }
    });

    // Order Book Chart
    const ctxOB = document.getElementById('orderBookChart').getContext('2d');
    if (charts.orderBook) charts.orderBook.destroy();
    charts.orderBook = new Chart(ctxOB, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                { label: 'Bids', data: [], backgroundColor: '#2ecc71' },
                { label: 'Asks', data: [], backgroundColor: '#e74c3c' }
            ]
        },
        options: {
             responsive: true, maintainAspectRatio: false, animation: false,
             scales: {
                 x: { display: true, title: { display: true, text: 'Price' } },
                 y: { display: true, title: { display: true, text: 'Volume' } }
             }
        }
    });
}

function updateCharts(tick) {
    if (!charts.prices) return;

    const slice = simulationData.slice(0, tick + 1);
    const labels = slice.map(d => d.tick);

    // Price Chart
    charts.prices.data.labels = labels;
    charts.prices.data.datasets.forEach(dataset => {
        dataset.data = slice.map(d => d.avg_prices[dataset.label] || 0);
    });
    charts.prices.update();

    // Eco Chart
    charts.eco.data.labels = labels;
    charts.eco.data.datasets[0].data = slice.map(d => d.avg_wealth);
    charts.eco.data.datasets[1].data = slice.map(d => d.gini_coefficient);
    charts.eco.update();
}

function updateAgents(data, tickTransactions) {
    // data.agents is array of {id, wallet, inventory, utility}
    // If old run without agent data, fallback?
    
    // Identify active
    const activeAgents = new Set();
    tickTransactions.forEach(t => {
        activeAgents.add(t.buyer_id);
        activeAgents.add(t.seller_id);
    });

    els.agentsGrid.innerHTML = '';
    const fragment = document.createDocumentFragment();

    const agents = data.agents || [];
    
    if (agents.length === 0 && metadata.config) {
        // Fallback for old runs
        els.agentsGrid.innerHTML = '<div class="alert alert-warning">Agent detail data not available in this run.</div>';
        return;
    }

    agents.forEach((a, i) => {
        // Format inventory
        let invHtml = '';
        Object.keys(a.inventory).forEach(k => {
            const qty = a.inventory[k];
            if (qty > 0.1) {
                invHtml += `<div class="inventory-item"><span>${k.charAt(0)}</span><span>${qty.toFixed(0)}</span></div>`;
            }
        });

        const active = activeAgents.has(a.id);
        const card = document.createElement('div');
        card.className = `card agent-card ${active ? 'active' : ''}`;
        
        card.innerHTML = `
            <div class="fw-bold">A-${i}</div>
            <div class="text-success fw-bold">$${a.wallet.toFixed(0)}</div>
            <div class="inventory-list text-muted">
                ${invHtml}
            </div>
        `;
        fragment.appendChild(card);
    });

    els.agentsGrid.appendChild(fragment);
}


function initNetwork() {
    const container = els.networkContainer;
    const options = {
        nodes: {
            shape: 'dot', size: 16, font: { size: 12, color: '#333' }, borderWidth: 2
        },
        edges: {
            width: 1, color: { color: '#848484' }, smooth: { type: 'continuous' }
        },
        physics: {
            stabilization: false,
            barnesHut: { gravitationalConstant: -2000, springConstant: 0.04, springLength: 95 }
        }
    };
    
    // Create new network with bound data sets
    network = new vis.Network(container, networkData, options);
}

function updateNetwork(data, tickTransactions) {
    if (!networkData.nodes) return;

    // 1. Update Nodes (Maintain positions by updating existing)
    const currentNodes = networkData.nodes.get({ returnType: 'Object' });
    const agents = data.agents || [];
    const newNodes = [];

    // Add agents if not exist
    agents.forEach((a, i) => {
        const id = a.id;
        if (!currentNodes[id]) {
            newNodes.push({ id: id, label: `A-${i}`, color: '#95a5a6', size: 15 });
        }
    });
    
    // Add Money Issuer if not exist
    if (!currentNodes['MONEY_ISSUER']) {
        newNodes.push({ id: 'MONEY_ISSUER', label: 'Issuer', color: '#e74c3c', shape: 'diamond', size: 25 });
    }
    
    if (newNodes.length > 0) {
        networkData.nodes.add(newNodes);
    }
    
    // Highlight active nodes
    const activeIds = new Set();
    tickTransactions.forEach(t => { activeIds.add(t.buyer_id); activeIds.add(t.seller_id); });
    
    const updates = [];
    networkData.nodes.forEach(node => {
        const isActive = activeIds.has(node.id);
        const newColor = isActive ? '#2ecc71' : (node.id === 'MONEY_ISSUER' ? '#e74c3c' : '#95a5a6');
        const newSize = isActive ? 20 : (node.id === 'MONEY_ISSUER' ? 25 : 15);
        if (node.color !== newColor || node.size !== newSize) {
            updates.push({ id: node.id, color: newColor, size: newSize });
        }
    });
    if(updates.length > 0) networkData.nodes.update(updates);


    // 2. Update Edges (Clear and redraw only active trades)
    // To avoid jumpiness, we only clear if different. But trades change every tick.
    // So clearing is correct for "showing current tick trades".
    networkData.edges.clear();
    
    const newEdges = tickTransactions.map(t => ({
        from: t.seller_id,
        to: t.buyer_id,
        title: `${t.commodity}: ${t.quantity.toFixed(1)} @ ${t.price.toFixed(1)}`,
        arrows: 'to',
        color: { color: getCommodityColor(t.commodity) }
    }));
    networkData.edges.add(newEdges);


    // Update List
    els.transactionList.innerHTML = '';
    if (tickTransactions.length === 0) {
        els.transactionList.innerHTML = '<div class="text-center text-muted mt-3">No transactions</div>';
    } else {
        tickTransactions.forEach(t => {
            const item = document.createElement('div');
            item.className = 'border-bottom p-2';
            item.style.fontSize = '0.85rem';
            item.innerHTML = `
                <div class="d-flex justify-content-between fw-bold">
                    <span class="text-primary">${t.commodity}</span>
                    <span>$${t.price.toFixed(2)}</span>
                </div>
                <div class="text-secondary">
                    ${t.seller_id.replace('agent_', 'A-')} &rarr; ${t.buyer_id.replace('agent_', 'A-')}
                    <span class="float-end">Qty: ${t.quantity.toFixed(1)}</span>
                </div>
            `;
            els.transactionList.appendChild(item);
        });
    }
}

function getCommodityColor(name) {
    const map = {
        'grain': '#f1c40f', 'iron': '#95a5a6', 'wood': '#d35400', 'stone': '#7f8c8d'
    };
    return map[name] || '#3498db';
}

init();

</script>
</body>
</html>"""

with open('visualizer.html', 'w', encoding='utf-8') as f:
    f.write(content)
