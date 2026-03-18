"""
worldbank_loader.py — بيانات البنك الدولي (GDP, inflation, trade)
"""
import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

WB_API = "https://api.worldbank.org/v2"

INDICATORS = {
    "GDP_USD": "NY.GDP.MKTP.CD",
    "GDP_per_capita": "NY.GDP.PCAP.CD",
    "inflation": "FP.CPI.TOTL.ZG",
    "trade_pct_gdp": "NE.TRD.GNFS.ZS",
    "unemployment": "SL.UEM.TOTL.ZS",
    "population": "SP.POP.TOTL",
    "gini_index": "SI.POV.GINI",
}

TOP_50_COUNTRIES = [
    "US", "CN", "JP", "DE", "IN", "GB", "FR", "IT", "CA", "KR",
    "RU", "BR", "AU", "ES", "MX", "ID", "NL", "SA", "TR", "CH",
    "TW", "PL", "SE", "BE", "AR", "NO", "AT", "AE", "NG", "IL",
    "ZA", "SG", "HK", "DK", "PH", "EG", "MY", "CL", "PK", "BD",
    "VN", "FI", "IR", "CO", "RO", "CZ", "PT", "NZ", "IQ", "QA",
]


def fetch_indicator(country_code: str, indicator: str, year: int = 2022) -> Optional[float]:
    """Fetch a single World Bank indicator value."""
    url = f"{WB_API}/country/{country_code}/indicator/{indicator}?date={year}&format=json&per_page=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Army81/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        if len(data) >= 2 and data[1]:
            val = data[1][0].get("value")
            return float(val) if val is not None else None
    except Exception:
        return None


def fetch_country_data(country_code: str) -> Dict:
    """Fetch all indicators for one country."""
    result = {"country": country_code, "indicators": {}}
    for name, ind_code in INDICATORS.items():
        val = fetch_indicator(country_code, ind_code)
        result["indicators"][name] = val
    return result


def load_worldbank_data(countries: List[str] = None, output_dir: str = None) -> str:
    """
    Fetch World Bank data for top 50 countries.
    Saves JSON to workspace/knowledge/economics/worldbank_data.json
    """
    if countries is None:
        countries = TOP_50_COUNTRIES

    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "workspace" / "knowledge" / "economics"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_data = {}

    # Fetch country info first (names etc.)
    try:
        url = f"{WB_API}/country/{';'.join(countries[:10])}?format=json&per_page=50"
        req = urllib.request.Request(url, headers={"User-Agent": "Army81/2.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            info_data = json.loads(resp.read())
        if len(info_data) >= 2:
            for c in info_data[1]:
                code = c.get("id", "")
                if code:
                    all_data[code] = {
                        "name": c.get("name", code),
                        "region": c.get("region", {}).get("value", ""),
                        "income_level": c.get("incomeLevel", {}).get("value", ""),
                        "indicators": {},
                    }
    except Exception as e:
        logger.error(f"Country info fetch failed: {e}")

    # Fetch indicators for each country (batch approach)
    for indicator_name, indicator_code in INDICATORS.items():
        logger.info(f"Fetching World Bank: {indicator_name}...")
        country_list = ";".join(countries)
        url = f"{WB_API}/country/{country_list}/indicator/{indicator_code}?date=2022&format=json&per_page=100"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Army81/2.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())

            if len(data) >= 2 and data[1]:
                for record in data[1]:
                    code = record.get("countryiso3code") or record.get("country", {}).get("id", "")
                    # Map iso3 to iso2
                    val = record.get("value")
                    # Try to match
                    for c_code in countries:
                        country_entry = all_data.get(c_code)
                        if country_entry and (c_code in str(record.get("country", {}))):
                            country_entry["indicators"][indicator_name] = float(val) if val is not None else None
                            break
        except Exception as e:
            logger.error(f"Batch fetch failed for {indicator_name}: {e}")

    # Save raw data
    output_path = output_dir / "worldbank_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    logger.info(f"World Bank data saved: {output_path}")

    # Also store summary in Chroma
    _store_in_chroma(all_data)

    return str(output_path)


def _store_in_chroma(data: Dict):
    """Store economic data summaries in Chroma."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        db_path = Path(__file__).parent.parent.parent / "workspace" / "chroma_db"
        client = chromadb.PersistentClient(path=str(db_path))
        ef = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
        collection = client.get_or_create_collection(
            name="economics_worldbank",
            embedding_function=ef,
            metadata={"source": "worldbank"},
        )

        docs, ids, metas = [], [], []
        for code, info in data.items():
            indicators = info.get("indicators", {})
            text = (
                f"Country: {info.get('name', code)} ({code})\n"
                f"Region: {info.get('region', 'N/A')}\n"
                f"Income Level: {info.get('income_level', 'N/A')}\n"
                f"GDP (USD): {indicators.get('GDP_USD', 'N/A')}\n"
                f"GDP per capita: {indicators.get('GDP_per_capita', 'N/A')}\n"
                f"Inflation: {indicators.get('inflation', 'N/A')}%\n"
                f"Trade (% of GDP): {indicators.get('trade_pct_gdp', 'N/A')}%\n"
                f"Unemployment: {indicators.get('unemployment', 'N/A')}%\n"
                f"Population: {indicators.get('population', 'N/A')}\n"
            )
            docs.append(text)
            ids.append(f"wb_{code}")
            metas.append({"country": code, "name": info.get("name", code), "source": "worldbank"})

        if docs:
            collection.upsert(documents=docs, ids=ids, metadatas=metas)
            logger.info(f"Stored {len(docs)} country records in Chroma")
    except Exception as e:
        logger.error(f"Chroma storage failed: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    path = load_worldbank_data()
    print(f"Saved: {path}")
