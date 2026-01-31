'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Job {
  id: string;
  status: string;
  config: {
    num_agents: number;
    num_steps: number;
    initial_money: number;
    use_money_issuer: boolean;
    use_cognitive_agents: boolean;
    description?: string;
  };
  created_at: string;
  completed_at?: string;
}

export default function Simulations() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await fetch(`${API_URL}/jobs`);
      if (response.ok) {
        const data = await response.json();
        setJobs(data.sort((a: Job, b: Job) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        ));
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✓';
      case 'running': return '⟳';
      case 'failed': return '✗';
      default: return '○';
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
        <div className="text-2xl">Loading simulations...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-5xl font-bold">Simulations</h1>
        <Link 
          href="/new"
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
        >
          + New Simulation
        </Link>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-20 bg-gray-50 rounded-lg">
          <p className="text-xl text-gray-600 mb-4">No simulations yet</p>
          <Link 
            href="/new"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Start Your First Simulation
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <Link 
              key={job.id}
              href={`/simulations/${job.id}`}
              className="block bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow border border-gray-200"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(job.status)}`}>
                      {getStatusIcon(job.status)} {job.status.toUpperCase()}
                    </span>
                    <span className="text-gray-500 text-sm">
                      {new Date(job.created_at).toLocaleString()}
                    </span>
                  </div>
                  
                  <h3 className="text-lg font-bold mb-2">
                    {job.config.description || `Simulation ${job.id.slice(0, 8)}`}
                  </h3>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Agents:</span>
                      <span className="font-semibold ml-2">{job.config.num_agents}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Steps:</span>
                      <span className="font-semibold ml-2">{job.config.num_steps}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Initial $:</span>
                      <span className="font-semibold ml-2">{job.config.initial_money}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Central Bank:</span>
                      <span className="font-semibold ml-2">{job.config.use_money_issuer ? 'Yes' : 'No'}</span>
                    </div>
                  </div>
                </div>
                
                <div className="text-blue-600 text-2xl">→</div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
