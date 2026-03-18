"""
wikipedia_loader.py — جلب مقالات Wikipedia لكل وكيل
"""
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# خريطة كل وكيل → أبرز موضوعات Wikipedia
AGENT_WIKIPEDIA_TOPICS = {
    "A01": ["strategic management", "leadership theory", "decision making", "organizational behavior", "competitive strategy"],
    "A02": ["scientific method", "research methodology", "peer review", "academic publishing", "empirical research"],
    "A03": ["public policy", "political science", "governance", "policy analysis", "democracy"],
    "A04": ["artificial intelligence", "machine learning", "neural network", "deep learning", "natural language processing"],
    "A05": ["software development", "programming paradigm", "agile software development", "software architecture", "version control"],
    "A06": ["data analysis", "statistics", "data science", "machine learning", "data visualization"],
    "A07": ["pharmacology", "clinical trial", "evidence-based medicine", "medical diagnosis", "therapeutics"],
    "A08": ["financial analysis", "investment", "portfolio management", "risk management", "capital markets"],
    "A09": ["cybersecurity", "information security", "cryptography", "network security", "ethical hacking"],
    "A10": ["knowledge management", "information architecture", "ontology", "semantic web", "enterprise knowledge"],
    "A11": ["translation", "linguistics", "natural language processing", "multilingualism", "computational linguistics"],
    "A12": ["content marketing", "copywriting", "social media marketing", "digital marketing", "SEO"],
    "A13": ["law", "legal reasoning", "jurisprudence", "contract law", "international law"],
    "A14": ["project management", "agile methodology", "PRINCE2", "risk management", "stakeholder management"],
    "A15": ["psychology", "cognitive psychology", "behavioral psychology", "psychotherapy", "mental health"],
    "A16": ["negotiation", "conflict resolution", "mediation", "bargaining", "persuasion"],
    "A17": ["nonverbal communication", "body language", "facial expression", "gesture", "proxemics"],
    "A18": ["persuasion", "rhetoric", "social influence", "propaganda", "marketing psychology"],
    "A19": ["emotional intelligence", "empathy", "social intelligence", "self-regulation", "motivation"],
    "A20": ["social dynamics", "group dynamics", "social psychology", "conformity", "social influence"],
    "A21": ["crowd psychology", "collective behavior", "mob mentality", "mass hysteria", "social movement"],
    "A22": ["behavioral economics", "cognitive bias", "prospect theory", "heuristics", "nudge theory"],
    "A23": ["change management", "organizational change", "transformation", "leadership", "resistance to change"],
    "A24": ["leadership psychology", "transformational leadership", "servant leadership", "charisma", "motivation"],
    "A25": ["communication theory", "interpersonal communication", "organizational communication", "rhetoric", "semiotics"],
    "A26": ["decision theory", "cognitive bias", "rational choice theory", "bounded rationality", "heuristics"],
    "A27": ["cross-cultural communication", "cultural intelligence", "intercultural competence", "globalization", "cultural anthropology"],
    "A28": ["military strategy", "warfare", "military history", "geopolitics", "national security"],
    "A29": ["conflict resolution", "peace studies", "mediation", "negotiation", "arbitration"],
    "A30": ["innovation management", "disruptive innovation", "entrepreneurship", "technology transfer", "R&D management"],
    "A31": ["intelligence analysis", "OSINT", "surveillance", "counterintelligence", "geopolitical risk"],
    "A32": ["geopolitics", "international relations", "political geography", "power politics", "foreign policy"],
    "A33": ["futures studies", "strategic foresight", "scenario planning", "technology forecasting", "futurism"],
    "A34": ["crisis management", "emergency management", "business continuity", "disaster recovery", "risk assessment"],
    "A35": ["radical innovation", "disruptive technology", "blue ocean strategy", "business model innovation", "entrepreneurship"],
    "A36": ["risk management", "financial risk", "operational risk", "enterprise risk management", "quantitative risk"],
    "A37": ["organizational strategy", "corporate governance", "strategic planning", "competitive advantage", "value chain"],
    "A38": ["quantum mechanics", "quantum computing", "quantum information", "particle physics", "condensed matter physics"],
    "A39": ["climate change", "global warming", "greenhouse gas", "renewable energy", "environmental science"],
    "A40": ["technology forecasting", "emerging technology", "innovation", "patents", "technology scouting"],
    "A41": ["macroeconomics", "international trade", "economic globalization", "monetary policy", "fiscal policy"],
    "A42": ["cryptocurrency", "blockchain", "decentralized finance", "Bitcoin", "smart contract"],
    "A43": ["historiography", "world history", "historical method", "civilization", "cultural history"],
    "A44": ["journalism", "media studies", "propaganda", "news media", "social media"],
    "A45": ["international law", "treaty", "United Nations", "international courts", "human rights law"],
    "A46": ["art history", "aesthetics", "cultural theory", "music theory", "literature"],
    "A47": ["linguistics", "phonology", "syntax", "semantics", "pragmatics"],
    "A48": ["mathematics", "number theory", "algebra", "calculus", "topology"],
    "A49": ["sociology", "social theory", "social stratification", "culture", "social structure"],
    "A50": ["pedagogy", "learning theory", "educational psychology", "curriculum", "instructional design"],
    "A51": ["reverse engineering", "malware analysis", "assembly language", "binary analysis", "software security"],
    "A52": ["clinical medicine", "internal medicine", "diagnosis", "treatment", "evidence-based medicine"],
    "A53": ["advanced manufacturing", "Industry 4.0", "automation", "3D printing", "lean manufacturing"],
    "A54": ["robotics", "robot kinematics", "control systems", "computer vision", "autonomous systems"],
    "A55": ["space exploration", "aerospace engineering", "satellite", "propulsion", "military technology"],
    "A56": ["media intelligence", "OSINT", "signal intelligence", "information warfare", "media analysis"],
    "A57": ["systems integration", "API", "middleware", "enterprise architecture", "microservices"],
    "A58": ["early warning system", "risk assessment", "horizon scanning", "threat detection", "intelligence"],
    "A59": ["open innovation", "crowdsourcing", "technology transfer", "hackathon", "innovation ecosystem"],
    "A60": ["disinformation", "fake news", "propaganda", "fact-checking", "media literacy"],
    "A61": ["bioinformatics", "computational biology", "genomics", "protein structure", "systems biology"],
    "A62": ["corporate governance", "board of directors", "transparency", "accountability", "ESG"],
    "A63": ["large organization", "bureaucracy", "organizational structure", "management", "complexity"],
    "A64": ["megaproject", "project management", "infrastructure", "construction management", "cost overrun"],
    "A65": ["digital transformation", "digital strategy", "cloud computing", "digital innovation", "technology adoption"],
    "A66": ["performance management", "key performance indicator", "balanced scorecard", "OKR", "performance appraisal"],
    "A67": ["interpersonal relationship", "trust", "authentic leadership", "psychological safety", "vulnerability"],
    "A68": ["resource allocation", "operations research", "linear programming", "optimization", "decision analysis"],
    "A69": ["program evaluation", "impact assessment", "quality assurance", "benchmarking", "performance measurement"],
    "A70": ["disruptive innovation", "creative destruction", "first principles thinking", "exponential technology", "breakthrough innovation"],
    "A71": ["corporate governance", "internal audit", "compliance", "fraud detection", "whistleblowing"],
    "A72": ["machine learning", "reinforcement learning", "meta-learning", "self-improvement", "autonomous systems"],
    "A73": ["multi-agent system", "distributed computing", "coordination", "swarm intelligence", "agent-based model"],
    "A74": ["quality control", "quality assurance", "Six Sigma", "ISO 9001", "statistical process control"],
    "A75": ["system optimization", "operations research", "algorithm", "performance tuning", "efficiency"],
    "A76": ["machine learning", "transfer learning", "knowledge distillation", "federated learning", "continual learning"],
    "A77": ["workflow management", "business process management", "process automation", "orchestration", "RPA"],
    "A78": ["resource management", "capacity planning", "load balancing", "scheduling algorithm", "cloud computing"],
    "A79": ["feedback loop", "control theory", "user feedback", "iterative design", "continuous improvement"],
    "A80": ["pattern recognition", "machine learning", "data mining", "anomaly detection", "signal processing"],
    "A81": ["artificial general intelligence", "superintelligence", "intelligence amplification", "cognitive architecture", "meta-learning"],
}


def fetch_wikipedia_summary(title: str, sentences: int = 5) -> Optional[Dict]:
    """Fetch Wikipedia article summary."""
    try:
        import urllib.request
        import urllib.parse
        import json

        params = urllib.parse.urlencode({
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exsentences": sentences,
            "exintro": True,
            "explaintext": True,
            "format": "json",
        })
        url = f"https://en.wikipedia.org/w/api.php?{params}"

        req = urllib.request.Request(url, headers={"User-Agent": "Army81/2.0 (educational project)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())

        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id == "-1":
                return None
            extract = page.get("extract", "")
            if not extract or len(extract) < 100:
                return None
            return {
                "title": page.get("title", title),
                "content": extract,
                "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page.get('title', title).replace(' ', '_'))}",
                "source": "wikipedia",
            }
    except Exception as e:
        logger.debug(f"Wikipedia fetch failed for '{title}': {e}")
        return None


def load_wikipedia_for_agent(agent_id: str) -> int:
    """Load Wikipedia articles for a specific agent into Chroma."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        db_path = Path(__file__).parent.parent.parent / "workspace" / "chroma_db"
        db_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(db_path))
        ef = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
        collection = client.get_or_create_collection(
            name=f"wiki_{agent_id}",
            embedding_function=ef,
            metadata={"agent_id": agent_id, "source": "wikipedia"},
        )
    except ImportError:
        logger.error("chromadb not installed")
        return 0

    topics = AGENT_WIKIPEDIA_TOPICS.get(agent_id, [])
    if not topics:
        return 0

    stored = 0
    for i, topic in enumerate(topics):
        article = fetch_wikipedia_summary(topic)
        if article:
            try:
                collection.upsert(
                    documents=[article["content"]],
                    ids=[f"wiki_{agent_id}_{i}"],
                    metadatas=[{"title": article["title"], "url": article["url"], "topic": topic, "agent_id": agent_id, "source": "wikipedia"}],
                )
                stored += 1
            except Exception as e:
                logger.error(f"Chroma upsert failed: {e}")
        time.sleep(0.5)

    return stored


def load_wikipedia_all_agents(agent_ids: List[str] = None) -> Dict[str, int]:
    """Load Wikipedia articles for all agents."""
    if agent_ids is None:
        agent_ids = list(AGENT_WIKIPEDIA_TOPICS.keys())

    counts = {}
    for agent_id in agent_ids:
        logger.info(f"Wikipedia: loading for {agent_id}...")
        counts[agent_id] = load_wikipedia_for_agent(agent_id)
        time.sleep(1)

    total = sum(counts.values())
    logger.info(f"Wikipedia complete: {total} articles for {len(counts)} agents")
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = load_wikipedia_all_agents(["A01", "A07", "A38"])
    print(f"Done: {results}")
