'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function NewSimulation() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState({
    num_agents: 10,
    num_steps: 100,
    initial_money: 1000,
    use_money_issuer: false,
    use_cognitive_agents: false,
    description: '',
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/jobs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        const job = await response.json();
        router.push(`/simulations/${job.id}`);
      } else {
        alert('Failed to create simulation job');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to connect to API');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-5xl font-bold mb-8">Configure New Simulation</h1>

      <form onSubmit={handleSubmit} className="space-y-6 bg-white p-8 rounded-lg shadow-lg">
        <div>
          <label className="block text-sm font-bold mb-2">
            Number of Agents (2-1000)
          </label>
          <input
            type="number"
            min="2"
            max="1000"
            value={config.num_agents}
            onChange={(e) => setConfig({ ...config, num_agents: parseInt(e.target.value) })}
            className="w-full border border-gray-300 rounded px-4 py-2"
            required
          />
          <p className="text-sm text-gray-600 mt-1">More agents = more realistic but slower</p>
        </div>

        <div>
          <label className="block text-sm font-bold mb-2">
            Simulation Steps (10-10000)
          </label>
          <input
            type="number"
            min="10"
            max="10000"
            value={config.num_steps}
            onChange={(e) => setConfig({ ...config, num_steps: parseInt(e.target.value) })}
            className="w-full border border-gray-300 rounded px-4 py-2"
            required
          />
          <p className="text-sm text-gray-600 mt-1">Each step represents one trading round</p>
        </div>

        <div>
          <label className="block text-sm font-bold mb-2">
            Initial Money Per Agent
          </label>
          <input
            type="number"
            min="0"
            step="100"
            value={config.initial_money}
            onChange={(e) => setConfig({ ...config, initial_money: parseFloat(e.target.value) })}
            className="w-full border border-gray-300 rounded px-4 py-2"
            required
          />
          <p className="text-sm text-gray-600 mt-1">Starting wealth for each agent</p>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="money_issuer"
            checked={config.use_money_issuer}
            onChange={(e) => setConfig({ ...config, use_money_issuer: e.target.checked })}
            className="mr-3 w-5 h-5"
          />
          <label htmlFor="money_issuer" className="text-sm font-bold">
            Enable Central Bank (Money Issuer)
          </label>
        </div>
        <p className="text-sm text-gray-600 -mt-4 ml-8">
          Simulates monetary policy and inflation dynamics
        </p>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="cognitive"
            checked={config.use_cognitive_agents}
            onChange={(e) => setConfig({ ...config, use_cognitive_agents: e.target.checked })}
            className="mr-3 w-5 h-5"
          />
          <label htmlFor="cognitive" className="text-sm font-bold">
            Enable Cognitive Agents (LLM Reasoning)
          </label>
        </div>
        <p className="text-sm text-gray-600 -mt-4 ml-8">
          Agents use language models for decision-making (slower, requires vLLM)
        </p>

        <div>
          <label className="block text-sm font-bold mb-2">
            Description (Optional)
          </label>
          <textarea
            value={config.description}
            onChange={(e) => setConfig({ ...config, description: e.target.value })}
            className="w-full border border-gray-300 rounded px-4 py-2"
            rows={3}
            placeholder="What are you testing in this simulation?"
          />
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={loading}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold disabled:opacity-50"
          >
            {loading ? 'Starting Simulation...' : 'Start Simulation'}
          </button>
          <button
            type="button"
            onClick={() => router.push('/simulations')}
            className="px-8 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>

      <div className="mt-8 bg-blue-50 p-6 rounded-lg">
        <h3 className="font-bold mb-2">💡 Tips</h3>
        <ul className="text-sm text-gray-700 space-y-1">
          <li>• Start with 10 agents and 100 steps for quick tests</li>
          <li>• Use 50-100 agents for realistic market dynamics</li>
          <li>• Central bank adds monetary policy effects</li>
          <li>• Cognitive agents are experimental and slow</li>
        </ul>
      </div>
    </div>
  );
}
