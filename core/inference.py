"""
vLLM Inference Engine Wrapper for MPES
Centralized inference server with batching and prefix caching.
"""

import asyncio
from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class InferenceConfig:
    """Configuration for the inference engine."""
    model_name: str = "meta-llama/Llama-2-7b-chat-hf"
    use_vllm: bool = False  # Set to True to use actual vLLM
    batch_size: int = 32
    max_tokens: int = 256
    temperature: float = 0.7
    enable_prefix_caching: bool = True


class MockLLMInference:
    """
    Mock LLM inference for testing without actual model.
    Returns structured trading decisions based on simple heuristics.
    """
    
    def __init__(self, config: InferenceConfig):
        self.config = config
    
    async def generate_batch(
        self, 
        prompts: List[str], 
        agent_ids: List[str]
    ) -> List[Dict]:
        """
        Mock batch inference.
        Returns trading decisions for each agent.
        """
        # Simulate some processing time
        await asyncio.sleep(0.01 * len(prompts) / self.config.batch_size)
        
        decisions = []
        for prompt, agent_id in zip(prompts, agent_ids):
            # Parse basic info from prompt (mock)
            decision = self._mock_decision(prompt, agent_id)
            decisions.append(decision)
        
        return decisions
    
    def _mock_decision(self, prompt: str, agent_id: str) -> Dict:
        """Generate a mock trading decision."""
        # Random but consistent based on agent_id
        np.random.seed(hash(agent_id) % 2**32)
        
        # Decide action: 'buy', 'sell', 'produce', 'hold'
        action = np.random.choice(
            ['buy', 'sell', 'produce', 'hold'],
            p=[0.3, 0.3, 0.2, 0.2]
        )
        
        return {
            'agent_id': agent_id,
            'action': action,
            'confidence': np.random.uniform(0.5, 1.0),
            'reasoning': f"Mock decision for {agent_id}: {action}"
        }


class VLLMInference:
    """
    Real vLLM inference engine integration.
    Requires vLLM server running.
    """
    
    def __init__(self, config: InferenceConfig):
        self.config = config
        self.client = None
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the shared system prompt for prefix caching."""
        return """You are an economic agent in a market simulation. Your goal is to maximize your personal utility by trading commodities.

You have:
- Inventory of various commodities
- A wallet with currency
- Production capabilities
- Consumption needs

For each turn, analyze your situation and decide on trading actions:
1. What to buy (if you need more of a commodity)
2. What to sell (if you have excess)
3. Whether to produce (if you have energy)

Consider:
- Marginal utility (value decreases as you have more)
- Market prices and trends
- Your production efficiency
- Future consumption needs

Respond with structured trading decisions in JSON format."""
    
    async def initialize(self):
        """Initialize connection to vLLM server."""
        try:
            from vllm import AsyncLLMEngine, AsyncEngineArgs
            
            engine_args = AsyncEngineArgs(
                model=self.config.model_name,
                tensor_parallel_size=1,
                enable_prefix_caching=self.config.enable_prefix_caching
            )
            
            self.client = AsyncLLMEngine.from_engine_args(engine_args)
            print(f"✓ vLLM engine initialized with {self.config.model_name}")
            
        except ImportError:
            print("⚠ vLLM not available. Falling back to mock inference.")
            self.client = None
    
    async def generate_batch(
        self, 
        prompts: List[str], 
        agent_ids: List[str]
    ) -> List[Dict]:
        """
        Generate trading decisions for a batch of agents.
        Uses prefix caching for efficiency.
        """
        if not self.client:
            # Fallback to mock
            mock_engine = MockLLMInference(self.config)
            return await mock_engine.generate_batch(prompts, agent_ids)
        
        # Build full prompts with system context
        full_prompts = [
            f"{self.system_prompt}\n\n{agent_prompt}"
            for agent_prompt in prompts
        ]
        
        # Batch inference
        results = await self._vllm_batch_generate(full_prompts)
        
        # Parse results into structured decisions
        decisions = []
        for result, agent_id in zip(results, agent_ids):
            decision = self._parse_llm_output(result, agent_id)
            decisions.append(decision)
        
        return decisions
    
    async def _vllm_batch_generate(self, prompts: List[str]) -> List[str]:
        """Execute batch generation with vLLM."""
        from vllm import SamplingParams
        
        sampling_params = SamplingParams(
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=0.9
        )
        
        outputs = await self.client.generate(prompts, sampling_params)
        
        return [output.outputs[0].text for output in outputs]
    
    def _parse_llm_output(self, output: str, agent_id: str) -> Dict:
        """Parse LLM output into structured decision."""
        # Try to extract JSON if present
        import json
        import re
        
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if json_match:
            try:
                decision = json.loads(json_match.group())
                decision['agent_id'] = agent_id
                return decision
            except json.JSONDecodeError:
                pass
        
        # Fallback: parse text for keywords
        action = 'hold'
        if 'buy' in output.lower():
            action = 'buy'
        elif 'sell' in output.lower():
            action = 'sell'
        elif 'produce' in output.lower():
            action = 'produce'
        
        return {
            'agent_id': agent_id,
            'action': action,
            'reasoning': output[:200]  # Truncate
        }


class InferenceEngine:
    """
    Main inference engine that handles batching and routing.
    Supports both mock and real vLLM backends.
    """
    
    def __init__(self, config: InferenceConfig):
        self.config = config
        
        if config.use_vllm:
            self.backend = VLLMInference(config)
        else:
            self.backend = MockLLMInference(config)
        
        self.call_count = 0
        self.total_latency = 0.0
    
    async def initialize(self):
        """Initialize the inference backend."""
        if hasattr(self.backend, 'initialize'):
            await self.backend.initialize()
    
    async def batch_agent_decisions(
        self,
        agent_contexts: List[str],
        agent_ids: List[str]
    ) -> List[Dict]:
        """
        Process a batch of agent decision requests.
        Automatically handles batching for efficiency.
        """
        import time
        
        start_time = time.time()
        
        # Process in batches if needed
        all_decisions = []
        batch_size = self.config.batch_size
        
        for i in range(0, len(agent_contexts), batch_size):
            batch_contexts = agent_contexts[i:i + batch_size]
            batch_ids = agent_ids[i:i + batch_size]
            
            batch_decisions = await self.backend.generate_batch(
                batch_contexts,
                batch_ids
            )
            all_decisions.extend(batch_decisions)
        
        # Track metrics
        latency = time.time() - start_time
        self.call_count += 1
        self.total_latency += latency
        
        return all_decisions
    
    def get_statistics(self) -> Dict:
        """Get inference engine statistics."""
        avg_latency = (
            self.total_latency / self.call_count 
            if self.call_count > 0 
            else 0
        )
        
        return {
            'total_calls': self.call_count,
            'total_latency': self.total_latency,
            'average_latency': avg_latency,
            'backend': 'vLLM' if self.config.use_vllm else 'Mock',
            'batch_size': self.config.batch_size
        }


async def test_inference_engine():
    """Test the inference engine."""
    config = InferenceConfig(use_vllm=False, batch_size=10)
    engine = InferenceEngine(config)
    await engine.initialize()
    
    # Test batch
    contexts = [
        f"Agent {i} has 5 units of grain, 10 currency"
        for i in range(25)
    ]
    agent_ids = [f"agent_{i:04d}" for i in range(25)]
    
    decisions = await engine.batch_agent_decisions(contexts, agent_ids)
    
    print(f"Processed {len(decisions)} decisions")
    print(f"Stats: {engine.get_statistics()}")
    print(f"Sample decision: {decisions[0]}")


if __name__ == "__main__":
    asyncio.run(test_inference_engine())
