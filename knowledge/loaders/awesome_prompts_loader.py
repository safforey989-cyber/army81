"""
awesome_prompts_loader.py — تحميل أفضل prompts وربطها بالوكلاء المناسبين
"""
import csv
import json
import logging
import urllib.request
import io
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

PROMPTS_URL = "https://raw.githubusercontent.com/f/awesome-chatgpt-prompts/main/prompts.csv"

# كلمات مفتاحية لكل فئة
CATEGORY_KEYWORDS = {
    "cat1_science": ["scientist", "researcher", "doctor", "medical", "physicist", "chemist", "biologist", "climate", "space", "quantum", "neuroscience"],
    "cat2_society": ["economist", "historian", "journalist", "lawyer", "linguist", "sociologist", "artist", "teacher", "philosopher", "politician"],
    "cat3_tools": ["developer", "programmer", "hacker", "security", "engineer", "analyst", "researcher", "technical", "code", "software"],
    "cat4_management": ["manager", "executive", "consultant", "advisor", "planner", "administrator", "director", "project"],
    "cat5_behavior": ["psychologist", "therapist", "counselor", "coach", "negotiator", "profiler", "behavior", "social"],
    "cat6_leadership": ["leader", "strategist", "general", "commander", "visionary", "mentor", "crisis", "intelligence"],
    "cat7_new": ["ai", "artificial", "machine", "learning", "optimization", "system", "autonomous"],
}

# ربط agent_id بكلمات مفتاحية إضافية
AGENT_KEYWORDS = {
    "A07": ["doctor", "medical", "health", "clinical", "physician"],
    "A08": ["financial", "investment", "finance", "banker", "economist"],
    "A09": ["security", "hacker", "cybersecurity", "penetration", "forensic"],
    "A13": ["lawyer", "legal", "attorney", "judge", "law"],
    "A15": ["psychologist", "therapist", "counselor", "mental"],
    "A16": ["negotiator", "mediator", "diplomat"],
    "A28": ["military", "general", "strategist", "warfare"],
    "A34": ["crisis", "emergency", "disaster"],
    "A05": ["developer", "programmer", "code", "engineer"],
    "A06": ["data", "analyst", "statistician", "data scientist"],
    "A12": ["writer", "content", "copywriter", "marketer"],
    "A11": ["translator", "interpreter", "linguist"],
    "A32": ["geopolitics", "political", "diplomat", "foreign policy"],
    "A41": ["economist", "economy", "macro", "trade"],
    "A43": ["historian", "history", "historian"],
    "A44": ["journalist", "reporter", "media"],
}


def fetch_prompts() -> List[Dict]:
    """Download prompts CSV from awesome-chatgpt-prompts."""
    try:
        req = urllib.request.Request(
            PROMPTS_URL,
            headers={"User-Agent": "Army81/2.0 (educational)"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")

        reader = csv.DictReader(io.StringIO(content))
        prompts = []
        for row in reader:
            act = row.get("act", "").strip()
            prompt = row.get("prompt", "").strip()
            if act and prompt:
                prompts.append({"act": act, "prompt": prompt})

        logger.info(f"Downloaded {len(prompts)} prompts from awesome-chatgpt-prompts")
        return prompts
    except Exception as e:
        logger.error(f"Failed to fetch prompts: {e}")
        return []


def match_prompt_to_agents(prompt_entry: Dict) -> List[str]:
    """Map a prompt to matching agent IDs based on keywords."""
    act_lower = prompt_entry["act"].lower()
    matched = []

    # Check agent-specific keywords first
    for agent_id, keywords in AGENT_KEYWORDS.items():
        if any(kw in act_lower for kw in keywords):
            matched.append(agent_id)

    # If no specific match, check categories
    if not matched:
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in act_lower for kw in keywords):
                # Assign to first agent in that category (A01-A81)
                # We'll just store by category
                matched.append(f"cat:{cat}")

    return matched if matched else ["general"]


def enrich_agent_prompts(agent_json_dir: Path, prompts: List[Dict]) -> Dict[str, List[str]]:
    """
    Find best matching prompts for each agent and return mapping.
    Does NOT modify JSON files — returns dict {agent_id: [expert_knowledge_section]}
    """
    # Build agent -> prompts mapping
    agent_prompts: Dict[str, List[str]] = {}

    for prompt_entry in prompts:
        targets = match_prompt_to_agents(prompt_entry)
        for target in targets:
            if target not in agent_prompts:
                agent_prompts[target] = []
            if len(agent_prompts[target]) < 3:  # Max 3 prompts per agent
                agent_prompts[target].append(prompt_entry["prompt"][:500])

    return agent_prompts


def load_prompts_to_chroma() -> int:
    """Load all prompts into Chroma collection."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        db_path = Path(__file__).parent.parent.parent / "workspace" / "chroma_db"
        db_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(db_path))
        ef = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
        collection = client.get_or_create_collection(
            name="expert_prompts",
            embedding_function=ef,
            metadata={"source": "awesome-chatgpt-prompts"},
        )
    except ImportError:
        logger.error("chromadb not installed")
        return 0

    prompts = fetch_prompts()
    if not prompts:
        return 0

    docs = [f"[{p['act']}]\n{p['prompt']}" for p in prompts]
    ids = [f"prompt_{i}" for i in range(len(prompts))]
    metas = [{"act": p["act"], "source": "awesome-prompts"} for p in prompts]

    batch_size = 100
    total = 0
    for i in range(0, len(docs), batch_size):
        try:
            collection.upsert(
                documents=docs[i:i+batch_size],
                ids=ids[i:i+batch_size],
                metadatas=metas[i:i+batch_size],
            )
            total += len(docs[i:i+batch_size])
        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")

    # Save mapping to file
    agents_root = Path(__file__).parent.parent.parent / "agents"
    mapping = enrich_agent_prompts(agents_root, prompts)
    mapping_path = Path(__file__).parent.parent.parent / "workspace" / "knowledge" / "prompt_mapping.json"
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    logger.info(f"Stored {total} expert prompts in Chroma")
    return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = load_prompts_to_chroma()
    print(f"Done: {count} prompts stored")
