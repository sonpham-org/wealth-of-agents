'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

interface Job {
  id: string;
  status: string;
  config: any;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

export default function SimulationDetail() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  
  const [job, setJob] = useState<Job | null>(null);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchJob();
    const interval = setInterval(fetchJob, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, [jobId]);

  const fetchJob = async () => {
    try {
      const response = await fetch(`${API_URL}/jobs/${jobId}`);
      if (response.ok) {
        const data = await response.json();
        setJob(data);
        
        if (data.status === 'completed') {
          fetchResults();
        }
      }
    } catch (error) {
      console.error('Error fetching job:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchResults = async () => {
    try {
      const response = await fetch(`${API_URL}/jobs/${jobId}/results`);
      if (response.ok) {
        const data = await response.json();
        setResults(data);
      }
    } catch (error) {
      console.error('Error fetching results:', error);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
        <div className="text-2xl">Loading simulation...</div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
        <div className="text-2xl mb-4">Simulation not found</div>
        <button
          onClick={() => router.push('/simulations')}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg"
        >
          Back to Simulations
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <button
        onClick={() => router.push('/simulations')}
        className="mb-4 text-blue-600 hover:underline"
      >
        ← Back to all simulations
      </button>

      <h1 className="text-4xl font-bold mb-6">
        {job.config.description || `Simulation ${jobId.slice(0, 8)}`}
      </h1>

      {/* Status */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-2xl font-bold mb-4">Status</h2>
        <div className="flex items-center gap-4">
          <span className={`px-4 py-2 rounded-full text-lg font-semibold ${
            job.status === 'completed' ? 'bg-green-100 text-green-800' :
            job.status === 'running' ? 'bg-blue-100 text-blue-800 animate-pulse' :
            job.status === 'failed' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {job.status.toUpperCase()}
          </span>
          {job.status === 'running' && (
            <span className="text-gray-600">Simulation in progress...</span>
          )}
        </div>
        
        {job.error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
            <p className="text-red-800 font-semibold">Error:</p>
            <p className="text-red-700">{job.error}</p>
          </div>
        )}
      </div>

      {/* Configuration */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-2xl font-bold mb-4">Configuration</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <div className="text-gray-600 text-sm">Agents</div>
            <div className="text-2xl font-bold">{job.config.num_agents}</div>
          </div>
          <div>
            <div className="text-gray-600 text-sm">Steps</div>
            <div className="text-2xl font-bold">{job.config.num_steps}</div>
          </div>
          <div>
            <div className="text-gray-600 text-sm">Initial Money</div>
            <div className="text-2xl font-bold">${job.config.initial_money}</div>
          </div>
          <div>
            <div className="text-gray-600 text-sm">Central Bank</div>
            <div className="text-2xl font-bold">{job.config.use_money_issuer ? 'Yes' : 'No'}</div>
          </div>
          <div>
            <div className="text-gray-600 text-sm">Cognitive Agents</div>
            <div className="text-2xl font-bold">{job.config.use_cognitive_agents ? 'Yes' : 'No'}</div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-2xl font-bold mb-4">Timeline</h2>
        <div className="space-y-2 text-sm">
          <div>
            <span className="text-gray-600">Created:</span>
            <span className="ml-2 font-semibold">{new Date(job.created_at).toLocaleString()}</span>
          </div>
          {job.started_at && (
            <div>
              <span className="text-gray-600">Started:</span>
              <span className="ml-2 font-semibold">{new Date(job.started_at).toLocaleString()}</span>
            </div>
          )}
          {job.completed_at && (
            <div>
              <span className="text-gray-600">Completed:</span>
              <span className="ml-2 font-semibold">{new Date(job.completed_at).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-2xl font-bold mb-4">Results</h2>
          <div className="bg-gray-50 p-4 rounded overflow-auto max-h-96">
            <pre className="text-sm">{results.stdout}</pre>
          </div>
        </div>
      )}

      {job.status === 'pending' && (
        <div className="text-center py-12 text-gray-600">
          <div className="text-6xl mb-4">⏳</div>
          <p className="text-xl">Simulation pending...</p>
        </div>
      )}
    </div>
  );
}
