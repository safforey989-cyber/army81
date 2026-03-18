"""
nasa_loader.py — بيانات NASA للمناخ والفضاء (مجاني، DEMO_KEY)
"""
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

NASA_API_KEY = "DEMO_KEY"  # مجاني، 30 req/hour
NASA_BASE = "https://api.nasa.gov"


def fetch_apod(count: int = 10) -> List[Dict]:
    """Fetch Astronomy Picture of the Day entries."""
    url = f"{NASA_BASE}/planetary/apod?api_key={NASA_API_KEY}&count={count}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read())
        return [{
            "title": d.get("title", ""),
            "explanation": d.get("explanation", ""),
            "date": d.get("date", ""),
            "url": d.get("url", ""),
            "media_type": d.get("media_type", ""),
            "source": "nasa_apod",
        } for d in (data if isinstance(data, list) else [data])]
    except Exception as e:
        logger.error(f"NASA APOD fetch failed: {e}")
        return []


def fetch_earth_events(limit: int = 50) -> List[Dict]:
    """Fetch natural Earth events (fires, storms, floods) from EONET."""
    url = f"{NASA_BASE}/EONET/v3/events?limit={limit}&status=open&api_key={NASA_API_KEY}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read())

        events = []
        for ev in data.get("events", []):
            categories = [c.get("title", "") for c in ev.get("categories", [])]
            events.append({
                "title": ev.get("title", ""),
                "description": f"Natural event: {ev.get('title', '')}. Categories: {', '.join(categories)}",
                "id": ev.get("id", ""),
                "categories": categories,
                "source": "nasa_eonet",
            })
        return events
    except Exception as e:
        logger.error(f"NASA EONET fetch failed: {e}")
        return []


def fetch_neo_asteroids(days: int = 7) -> List[Dict]:
    """Fetch Near Earth Objects data."""
    end = datetime.now()
    start = end - timedelta(days=days)
    url = (
        f"{NASA_BASE}/neo/rest/v1/feed"
        f"?start_date={start.strftime('%Y-%m-%d')}"
        f"&end_date={end.strftime('%Y-%m-%d')}"
        f"&api_key={NASA_API_KEY}"
    )
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read())

        neos = []
        for date_key, asteroids in data.get("near_earth_objects", {}).items():
            for ast in asteroids[:5]:  # Limit per day
                diameter = ast.get("estimated_diameter", {}).get("kilometers", {})
                neos.append({
                    "name": ast.get("name", ""),
                    "description": (
                        f"Near Earth Object: {ast.get('name', '')}. "
                        f"Date: {date_key}. "
                        f"Diameter: {diameter.get('estimated_diameter_min', 0):.3f}-{diameter.get('estimated_diameter_max', 0):.3f} km. "
                        f"Potentially hazardous: {ast.get('is_potentially_hazardous_asteroid', False)}."
                    ),
                    "date": date_key,
                    "hazardous": ast.get("is_potentially_hazardous_asteroid", False),
                    "source": "nasa_neo",
                })
        return neos
    except Exception as e:
        logger.error(f"NASA NEO fetch failed: {e}")
        return []


def load_nasa_to_chroma() -> Dict[str, int]:
    """Load NASA data to Chroma for A39 (climate) and A54 (space)."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        db_path = Path(__file__).parent.parent.parent / "workspace" / "chroma_db"
        db_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(db_path))
        ef = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
    except ImportError:
        logger.error("chromadb not installed")
        return {}

    counts = {}

    # Space collection (for A54 - space/defense)
    space_col = client.get_or_create_collection(
        name="nasa_space",
        embedding_function=ef,
        metadata={"source": "nasa", "agent_id": "A54"},
    )
    apod = fetch_apod(count=20)
    neos = fetch_neo_asteroids(days=7)
    space_items = apod + neos

    if space_items:
        docs = [f"{i.get('title','')}\n{i.get('explanation', i.get('description', ''))}" for i in space_items]
        ids = [f"nasa_space_{j}" for j in range(len(space_items))]
        metas = [{"source": i.get("source", "nasa"), "title": i.get("title", "")} for i in space_items]
        try:
            space_col.upsert(documents=docs, ids=ids, metadatas=metas)
            counts["nasa_space"] = len(space_items)
        except Exception as e:
            logger.error(f"NASA space upsert failed: {e}")

    # Climate collection (for A39 - climate)
    climate_col = client.get_or_create_collection(
        name="nasa_climate",
        embedding_function=ef,
        metadata={"source": "nasa", "agent_id": "A39"},
    )
    events = fetch_earth_events(limit=50)
    if events:
        docs = [e.get("description", e.get("title", "")) for e in events]
        ids = [f"nasa_climate_{j}" for j in range(len(events))]
        metas = [{"source": "nasa_eonet", "title": e.get("title", ""), "categories": str(e.get("categories", []))} for e in events]
        try:
            climate_col.upsert(documents=docs, ids=ids, metadatas=metas)
            counts["nasa_climate"] = len(events)
        except Exception as e:
            logger.error(f"NASA climate upsert failed: {e}")

    logger.info(f"NASA data loaded: {counts}")
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = load_nasa_to_chroma()
    print(f"Done: {results}")
