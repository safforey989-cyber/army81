# Advanced Multi-Agent Memory System
# Agent Memory + Core Kernel + Smart Recall

import json
import time
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# =========================
# Embedding
# =========================
def embed(text):
    return model.encode(text)

# =========================
# Agent Memory
# =========================
class AgentMemory:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.short_term = []
        self.long_term = []

    def store(self, text, importance=0.5):
        item = {
            "text": text,
            "embedding": embed(text),
            "importance": importance,
            "time": time.time()
        }

        if importance > 0.7:
            self.long_term.append(item)
        else:
            self.short_term.append(item)

    def search(self, query, top_k=5):
        q_emb = embed(query)
        results = []

        for item in self.short_term + self.long_term:
            sim = np.dot(q_emb, item["embedding"])
            score = sim * 0.7 + item["importance"] * 0.3
            results.append((score, item))

        results.sort(reverse=True, key=lambda x: x[0])
        return [r[1] for r in results[:top_k]]

# =========================
# Core Kernel (Global Brain)
# =========================
class KernelMemory:
    def __init__(self):
        self.global_memory = []

    def archive(self, agent_id, text):
        self.global_memory.append({
            "agent": agent_id,
            "text": text,
            "embedding": embed(text),
            "time": time.time()
        })

    def recall(self, query, top_k=5):
        q_emb = embed(query)
        results = []

        for item in self.global_memory:
            sim = np.dot(q_emb, item["embedding"])
            results.append((sim, item))

        results.sort(reverse=True, key=lambda x: x[0])
        return [r[1] for r in results[:top_k]]

# =========================
# Orchestrator
# =========================
class MemorySystem:
    def __init__(self):
        self.kernel = KernelMemory()
        self.agents = {}

    def get_agent(self, agent_id):
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentMemory(agent_id)
        return self.agents[agent_id]

    def store(self, agent_id, text, importance=0.5):
        agent = self.get_agent(agent_id)
        agent.store(text, importance)

        # archive important knowledge
        if importance > 0.6:
            self.kernel.archive(agent_id, text)

    def query(self, agent_id, query):
        agent = self.get_agent(agent_id)

        local_results = agent.search(query)

        if local_results:
            return local_results

        return self.kernel.recall(query)

# =========================
# Example Usage
# =========================
if __name__ == "__main__":
    system = MemorySystem()

    system.store("A1", "API failed due to timeout", importance=0.9)
    system.store("A1", "User prefers JSON responses", importance=0.8)

    result = system.query("A1", "API error")
    print(result)
