import Link from 'next/link';

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero */}
      <section className="text-center py-20">
        <h1 className="text-6xl font-bold mb-6">🌍 Wealth of Agents</h1>
        <p className="text-2xl text-gray-600 mb-4">
          Agent-Based Economic Simulation
        </p>
        <p className="text-lg text-gray-700 max-w-3xl mx-auto mb-8">
          Explore emergent economic phenomena—inflation, inequality, and resource allocation—through 
          the interactions of autonomous agents in a realistic economic sandbox.
        </p>
        <div className="flex gap-4 justify-center">
          <Link 
            href="/new"
            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-semibold"
          >
            Start New Simulation
          </Link>
          <Link 
            href="/simulations"
            className="px-8 py-3 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors text-lg font-semibold"
          >
            View Simulations
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8 py-16">
        <div className="bg-white p-8 rounded-lg shadow-lg border border-gray-200">
          <div className="text-4xl mb-4">🤖</div>
          <h3 className="text-xl font-bold mb-3">Autonomous Agents</h3>
          <p className="text-gray-700">
            Rational utility-maximizing agents make trading decisions to maximize personal utility in a dynamic market.
          </p>
        </div>
        
        <div className="bg-white p-8 rounded-lg shadow-lg border border-gray-200">
          <div className="text-4xl mb-4">📈</div>
          <h3 className="text-xl font-bold mb-3">Market Dynamics</h3>
          <p className="text-gray-700">
            High-performance Limit Order Book with real-time price discovery for multiple commodities.
          </p>
        </div>
        
        <div className="bg-white p-8 rounded-lg shadow-lg border border-gray-200">
          <div className="text-4xl mb-4">💰</div>
          <h3 className="text-xl font-bold mb-3">Monetary Policy</h3>
          <p className="text-gray-700">
            Optional central bank demonstrates the Cantillon effect and demand-pull inflation dynamics.
          </p>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 bg-gray-50 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold mb-8 text-center">How It Works</h2>
          
          <div className="space-y-6">
            <div className="flex items-start gap-4">
              <div className="bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold flex-shrink-0">1</div>
              <div>
                <h4 className="font-bold text-lg mb-2">Configure Your Simulation</h4>
                <p className="text-gray-700">Set parameters like number of agents, simulation steps, initial money, and policy options.</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4">
              <div className="bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold flex-shrink-0">2</div>
              <div>
                <h4 className="font-bold text-lg mb-2">Run the Simulation</h4>
                <p className="text-gray-700">Our backend processes the job, running the full economic simulation with all agent interactions.</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4">
              <div className="bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold flex-shrink-0">3</div>
              <div>
                <h4 className="font-bold text-lg mb-2">Analyze Results</h4>
                <p className="text-gray-700">View detailed analytics, price charts, wealth distribution, and agent behaviors once complete.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Economics Model */}
      <section className="py-16">
        <h2 className="text-4xl font-bold mb-8 text-center">Economic Model</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-blue-50 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-4">🎯 Core Components</h3>
            <ul className="space-y-2 text-gray-700">
              <li>• High-performance Limit Order Book (LOB)</li>
              <li>• Distributed agent system with Ray</li>
              <li>• Cobb-Douglas utility preferences</li>
              <li>• Production and consumption cycles</li>
              <li>• Optional LLM-based cognitive reasoning</li>
            </ul>
          </div>
          
          <div className="bg-purple-50 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-4">📊 Measured Metrics</h3>
            <ul className="space-y-2 text-gray-700">
              <li>• Gini coefficient (inequality)</li>
              <li>• GDP and economic growth</li>
              <li>• Inflation rates</li>
              <li>• Price discovery dynamics</li>
              <li>• Wealth distribution</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
