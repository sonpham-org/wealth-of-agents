'use client';

import { useEffect, useRef, useState } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
  ChartOptions
} from 'chart.js';
import { Network } from 'vis-network/standalone';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface Agent {
  id: string;
  type: string;
  energy: number;
  money: number;
  inventory: Record<string, number>;
  active: boolean;
}

interface SimulationData {
  agents: Agent[];
  tick: number;
  max_tick: number;
  trades: any[];
  gini_coefficient?: number;
  total_trades?: number;
}

interface VisualizerProps {
  data: SimulationData;
  onTickChange?: (tick: number) => void;
}

export default function SimulationVisualizer({ data, onTickChange }: VisualizerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTick, setCurrentTick] = useState(0);
  const [speed, setSpeed] = useState(500);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const networkRef = useRef<HTMLDivElement>(null);
  const networkInstance = useRef<Network | null>(null);

  // Network visualization
  useEffect(() => {
    if (!networkRef.current || !data.agents) return;

    const nodes = data.agents.map(agent => ({
      id: agent.id,
      label: agent.id,
      color: agent.type === 'money_issuer' ? '#dc3545' : 
             agent.active ? '#198754' : '#6c757d',
      size: Math.max(20, agent.money / 10),
    }));

    const edges = data.trades?.map((trade, idx) => ({
      id: idx,
      from: trade.buyer_id,
      to: trade.seller_id,
      arrows: 'to',
      color: { color: '#3498db', opacity: 0.5 }
    })) || [];

    const visData = { nodes, edges };
    const options = {
      physics: {
        enabled: true,
        stabilization: { iterations: 100 }
      },
      interaction: {
        hover: true,
        selectConnectedEdges: false
      }
    };

    if (!networkInstance.current) {
      networkInstance.current = new Network(networkRef.current, visData, options);
      networkInstance.current.on('click', (params) => {
        if (params.nodes.length > 0) {
          setSelectedAgent(params.nodes[0]);
        }
      });
    } else {
      networkInstance.current.setData(visData);
    }

    return () => {
      if (networkInstance.current) {
        networkInstance.current.destroy();
        networkInstance.current = null;
      }
    };
  }, [data]);

  // Auto-play functionality
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentTick(prev => {
        const next = prev + 1;
        if (next >= data.max_tick) {
          setIsPlaying(false);
          return prev;
        }
        onTickChange?.(next);
        return next;
      });
    }, speed);

    return () => clearInterval(interval);
  }, [isPlaying, speed, data.max_tick, onTickChange]);

  // Prepare chart data
  const wealthDistribution = {
    labels: data.agents.map(a => a.id),
    datasets: [{
      label: 'Money',
      data: data.agents.map(a => a.money),
      backgroundColor: 'rgba(241, 196, 15, 0.6)',
      borderColor: 'rgba(241, 196, 15, 1)',
      borderWidth: 1
    }]
  };

  const energyDistribution = {
    labels: data.agents.map(a => a.id),
    datasets: [{
      label: 'Energy',
      data: data.agents.map(a => a.energy),
      backgroundColor: 'rgba(52, 152, 219, 0.6)',
      borderColor: 'rgba(52, 152, 219, 1)',
      borderWidth: 1
    }]
  };

  const chartOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false }
    },
    scales: {
      y: { beginAtZero: true }
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`w-12 h-12 rounded-full flex items-center justify-center ${
              isPlaying ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-green-500 hover:bg-green-600'
            } text-white transition-colors`}
          >
            {isPlaying ? '⏸' : '▶'}
          </button>

          <div className="flex-1">
            <div className="flex justify-between text-sm mb-1">
              <span>Current Tick: <strong>{currentTick}</strong></span>
              <span>Max Tick: <strong>{data.max_tick}</strong></span>
            </div>
            <input
              type="range"
              min="0"
              max={data.max_tick}
              value={currentTick}
              onChange={(e) => {
                const tick = parseInt(e.target.value);
                setCurrentTick(tick);
                onTickChange?.(tick);
              }}
              className="w-full"
            />
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm">Speed:</label>
            <select
              value={speed}
              onChange={(e) => setSpeed(parseInt(e.target.value))}
              className="px-3 py-1 border rounded"
            >
              <option value="1000">Slow</option>
              <option value="500">Normal</option>
              <option value="100">Fast</option>
              <option value="10">Turbo</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow text-center">
          <div className="text-3xl font-bold text-gray-800">{data.agents?.length || 0}</div>
          <div className="text-sm text-gray-600 uppercase">Active Agents</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow text-center">
          <div className="text-3xl font-bold text-gray-800">{data.total_trades || 0}</div>
          <div className="text-sm text-gray-600 uppercase">Total Trades</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow text-center">
          <div className="text-3xl font-bold text-gray-800">
            {data.gini_coefficient?.toFixed(3) || '0.000'}
          </div>
          <div className="text-sm text-gray-600 uppercase">Gini Coefficient</div>
        </div>
      </div>

      {/* Network Visualization */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-3">Agent Network</h3>
        <div ref={networkRef} className="w-full h-[600px] border rounded"></div>
      </div>

      {/* Agent Cards */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-3">Agents</h3>
        <div className="flex flex-wrap gap-2">
          {data.agents?.map(agent => (
            <div
              key={agent.id}
              onClick={() => setSelectedAgent(agent.id)}
              className={`w-36 p-3 border-2 rounded-lg cursor-pointer transition-all ${
                selectedAgent === agent.id ? 'border-green-500 bg-green-50' :
                agent.type === 'money_issuer' ? 'border-red-300 bg-red-50' :
                'border-gray-200 hover:border-gray-400'
              }`}
            >
              <div className="text-xs font-semibold text-center mb-2">{agent.id}</div>
              
              {/* Energy Bar */}
              <div className="h-1.5 bg-gray-200 rounded-full mb-1 overflow-hidden">
                <div 
                  className="h-full bg-blue-500" 
                  style={{ width: `${Math.min(100, agent.energy)}%` }}
                ></div>
              </div>
              
              {/* Money Bar */}
              <div className="h-1.5 bg-gray-200 rounded-full mb-2 overflow-hidden">
                <div 
                  className="h-full bg-yellow-500" 
                  style={{ width: `${Math.min(100, agent.money / 10)}%` }}
                ></div>
              </div>

              <div className="text-xs space-y-0.5">
                <div className="flex justify-between">
                  <span className="text-gray-600">E:</span>
                  <span className="font-mono">{agent.energy.toFixed(0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">M:</span>
                  <span className="font-mono">{agent.money.toFixed(0)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-3">Wealth Distribution</h3>
          <div className="h-64">
            <Bar data={wealthDistribution} options={chartOptions} />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-3">Energy Distribution</h3>
          <div className="h-64">
            <Bar data={energyDistribution} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Selected Agent Detail */}
      {selectedAgent && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-3">Agent Details: {selectedAgent}</h3>
          {data.agents?.find(a => a.id === selectedAgent) && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <strong>Type:</strong> {data.agents.find(a => a.id === selectedAgent)?.type}
              </div>
              <div>
                <strong>Active:</strong> {data.agents.find(a => a.id === selectedAgent)?.active ? 'Yes' : 'No'}
              </div>
              <div>
                <strong>Energy:</strong> {data.agents.find(a => a.id === selectedAgent)?.energy.toFixed(2)}
              </div>
              <div>
                <strong>Money:</strong> {data.agents.find(a => a.id === selectedAgent)?.money.toFixed(2)}
              </div>
              <div className="col-span-2">
                <strong>Inventory:</strong>
                <pre className="mt-2 p-2 bg-gray-50 rounded text-xs">
                  {JSON.stringify(data.agents.find(a => a.id === selectedAgent)?.inventory, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
