"""
Army81 - Daily Intelligence Updater
يجمع تحديثات يومية من arXiv + GitHub + NewsAPI
ويحفظها في Chroma تلقائياً
جدولة: كل يوم الساعة 2:00 صباحاً عبر APScheduler

تشغيل يدوي:   python scripts/daily_updater.py
تشغيل scheduler: python scripts/daily_updater.py --schedule
"""
import sys
import os
import logging
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("army81.daily_updater")


def fetch_recent_news(query: str, limit: int = 3) -> str:
    """جلب أحدث الأخبار المرتبطة بكلمات مفتاحية — للحقن في سياق الوكلاء"""
    try:
        import requests
        key = os.getenv("NEWSAPI_KEY", "")
        if not key:
            return ""
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": query, "pageSize": limit, "sortBy": "publishedAt", "language": "en"},
            headers={"X-Api-Key": key},
            timeout=5
        )
        if r.ok:
            articles = r.json().get("articles", [])
            lines = []
            for a in articles[:limit]:
                lines.append(f"- {a.get('title', '')} ({a.get('source', {}).get('name', '')})")
            return "\n".join(lines) if lines else ""
    except Exception:
        pass
    return ""
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [daily_updater] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

# Autonomy loop singleton (for scheduler ticks)
_AUTONOMY = None
_AUTONOMY_ROUTER = None

# ── الموضوعات المتابعة يومياً ──────────────────────────────
AI_TOPICS = [
    "large language models agents",
    "AI safety alignment 2025",
    "multimodal AI systems",
    "autonomous AI agents",
    "AI reasoning planning",
]

GITHUB_QUERIES = [
    "AI agent framework",
    "LLM tools python",
    "autonomous agents LLM",
]

NEWS_TOPICS = [
    "artificial intelligence",
    "machine learning breakthrough",
    "AI regulation policy",
]


# ── جامع arXiv ────────────────────────────────────────────

def collect_arxiv_papers() -> list:
    """جمع أحدث أبحاث الذكاء الاصطناعي من arXiv"""
    from tools.science_tools import search_arxiv
    papers = []

    for topic in AI_TOPICS:
        logger.info(f"arXiv: searching '{topic}'")
        try:
            result = search_arxiv(topic, max_results=3)
            if result and "خطأ" not in result:
                papers.append({
                    "source": "arxiv",
                    "topic": topic,
                    "content": result,
                    "timestamp": datetime.now().isoformat(),
                })
        except Exception as e:
            logger.warning(f"arXiv error for '{topic}': {e}")

    logger.info(f"Collected {len(papers)} arXiv results")
    return papers


# ── جامع GitHub Trending ──────────────────────────────────

def collect_github_trending() -> list:
    """جمع المستودعات الرائجة المتعلقة بالذكاء الاصطناعي"""
    from tools.github_tool import search_repos
    repos = []

    for query in GITHUB_QUERIES:
        logger.info(f"GitHub: searching '{query}'")
        try:
            result = search_repos(query, sort="stars", max_results=5)
            if result and "خطأ" not in result:
                repos.append({
                    "source": "github",
                    "query": query,
                    "content": result,
                    "timestamp": datetime.now().isoformat(),
                })
        except Exception as e:
            logger.warning(f"GitHub error for '{query}': {e}")

    logger.info(f"Collected {len(repos)} GitHub results")
    return repos


# ── جامع الأخبار ──────────────────────────────────────────

def collect_ai_news() -> list:
    """جمع أخبار الذكاء الاصطناعي من مصادر متعددة"""
    from tools.web_search import fetch_news
    news_items = []

    for topic in NEWS_TOPICS:
        logger.info(f"News: fetching '{topic}'")
        try:
            result = fetch_news(topic=topic, lang="en")
            if result and "خطأ" not in result:
                news_items.append({
                    "source": "news",
                    "topic": topic,
                    "content": result,
                    "timestamp": datetime.now().isoformat(),
                })
        except Exception as e:
            logger.warning(f"News error for '{topic}': {e}")

    logger.info(f"Collected {len(news_items)} news results")
    return news_items


# ── الحفظ في Chroma ───────────────────────────────────────

def save_to_chroma(items: list, collection_tag: str = "daily_update") -> int:
    """حفظ المعلومات المجمّعة في الذاكرة الدلالية"""
    from memory.chroma_memory import remember
    saved = 0

    for item in items:
        try:
            content = (
                f"[{item['source'].upper()} | {item.get('topic', item.get('query', ''))} | "
                f"{item['timestamp'][:10]}]\n\n{item['content']}"
            )
            tags = [item["source"], collection_tag, datetime.now().strftime("%Y-%m")]
            result = remember(content, agent_id="daily_updater", tags=tags)
            if "تم الحفظ" in result or "ID" in result:
                saved += 1
        except Exception as e:
            logger.warning(f"Chroma save error: {e}")

    return saved


# ── حفظ تقرير يومي ───────────────────────────────────────

def save_daily_report(all_items: list) -> str:
    """حفظ تقرير نصي يومي في workspace/reports/"""
    reports_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "workspace", "reports"
    )
    os.makedirs(reports_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(reports_dir, f"daily_report_{date_str}.md")

    lines = [
        f"# تقرير يومي Army81 — {date_str}\n",
        f"**إجمالي العناصر المجمّعة:** {len(all_items)}\n\n",
    ]

    by_source = {}
    for item in all_items:
        src = item["source"]
        by_source.setdefault(src, []).append(item)

    for source, items in by_source.items():
        lines.append(f"## {source.upper()} ({len(items)} عناصر)\n")
        for item in items:
            topic = item.get("topic", item.get("query", ""))
            lines.append(f"### {topic}\n")
            lines.append(item["content"][:800] + "\n\n---\n\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    logger.info(f"Daily report saved: {report_path}")
    return report_path


# ── الدالة الرئيسية ───────────────────────────────────────

def run_daily_update():
    """تنفيذ التحديث اليومي الكامل"""
    start = datetime.now()
    logger.info(f"=== Daily Update Started: {start.strftime('%Y-%m-%d %H:%M')} ===")

    all_items = []

    # 1. جمع الأبحاث
    logger.info("Step 1/3: Collecting arXiv papers...")
    arxiv_items = collect_arxiv_papers()
    all_items.extend(arxiv_items)

    # 2. جمع GitHub
    logger.info("Step 2/3: Collecting GitHub trending...")
    github_items = collect_github_trending()
    all_items.extend(github_items)

    # 3. جمع الأخبار
    logger.info("Step 3/3: Collecting AI news...")
    news_items = collect_ai_news()
    all_items.extend(news_items)

    # حفظ في Chroma
    if all_items:
        logger.info(f"Saving {len(all_items)} items to Chroma...")
        saved = save_to_chroma(all_items)
        logger.info(f"Saved {saved}/{len(all_items)} items to Chroma memory")

        # حفظ تقرير
        report_path = save_daily_report(all_items)
    else:
        logger.warning("No items collected — check API keys in .env")
        saved = 0
        report_path = None

    elapsed = (datetime.now() - start).total_seconds()
    summary = {
        "date": start.strftime("%Y-%m-%d"),
        "arxiv": len(arxiv_items),
        "github": len(github_items),
        "news": len(news_items),
        "total": len(all_items),
        "saved_to_chroma": saved,
        "report": report_path,
        "elapsed_seconds": round(elapsed, 1),
    }

    logger.info(f"=== Daily Update Complete in {elapsed:.1f}s: {summary} ===")

    # v5: إرسال التقرير عبر Telegram
    _send_telegram_daily_report(summary, all_items)

    return summary


def _send_telegram_daily_report(summary: dict, all_items: list):
    """إرسال ملخص التحديث اليومي عبر Telegram"""
    try:
        from core.human_interface import get_human_interface
        hi = get_human_interface()

        completed_lines = []
        if summary["arxiv"]:
            completed_lines.append(f"📚 {summary['arxiv']} أبحاث من arXiv")
        if summary["github"]:
            completed_lines.append(f"🐙 {summary['github']} مستودعات من GitHub")
        if summary["news"]:
            completed_lines.append(f"📰 {summary['news']} أخبار")

        report = {
            "completed": "\n".join(completed_lines) or "لم يُجمع شيء",
            "improvements": f"حُفظ {summary['saved_to_chroma']} عنصر في الذاكرة",
            "pending_count": len(hi.get_pending()),
            "key_finding": _extract_key_finding(all_items),
        }
        hi.send_daily_report(report)
    except Exception as e:
        logger.warning(f"Telegram daily report failed: {e}")


def _extract_key_finding(items: list) -> str:
    """استخراج أهم اكتشاف من العناصر المجمّعة"""
    if not items:
        return "لا اكتشافات اليوم"
    # أول عنصر كملخص
    first = items[0]
    content = first.get("content", "")
    if len(content) > 200:
        content = content[:200] + "..."
    return f"[{first.get('source', '?')}] {content}"


# ── v3: دوال الجدولة الجديدة ───────────────────────────────

def daily_distillation():
    """3:00 صباحاً — تقطير المعرفة (DeepSeek style)"""
    logger.info("=== Knowledge Distillation Started ===")
    try:
        from core.knowledge_distillation import KnowledgeDistillation
        kd = KnowledgeDistillation()
        result = kd.daily_distillation()
        logger.info(f"Distillation complete: {result}")
    except Exception as e:
        logger.error(f"Distillation error: {e}")


def compress_all_agents():
    """كل أحد 4:00 صباحاً — ضغط ذاكرة كل الوكلاء"""
    logger.info("=== Weekly Memory Compression Started ===")
    try:
        from memory.hierarchical_memory import HierarchicalMemory
        import json, os
        hm = HierarchicalMemory()

        agents_dir = os.path.abspath(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents")
        )
        compressed = 0
        for root, _, files in os.walk(agents_dir):
            for f in files:
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(root, f), "r", encoding="utf-8") as fp:
                            data = json.load(fp)
                        agent_id = data.get("agent_id")
                        if agent_id:
                            hm.compress_weekly(agent_id)
                            compressed += 1
                    except Exception as e:
                        logger.warning(f"Compress error for {f}: {e}")

        logger.info(f"=== Memory Compression Done: {compressed} agents ===")
    except Exception as e:
        logger.error(f"Memory compression error: {e}")


def weekly_evolution_cycle():
    """كل أحد 5:00 صباحاً — دورة التطور الذاتي"""
    logger.info("=== Weekly Evolution Cycle Started ===")
    try:
        from core.safe_evolution import SafeEvolution
        se = SafeEvolution()
        result = se.weekly_cycle()
        logger.info(f"Evolution cycle complete: {result.get('changed', [])} improved")
    except Exception as e:
        logger.error(f"Evolution cycle error: {e}")


# ── Scheduler ─────────────────────────────────────────────

def start_scheduler():
    """تشغيل APScheduler — الجدولة الكاملة v3"""
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler(timezone="Asia/Jerusalem")

    # 2:00 صباحاً — تحديث خارجي (arXiv + GitHub + أخبار)
    scheduler.add_job(
        run_daily_update,
        'cron', hour=2, minute=0,
        id="daily_update",
        name="Army81 Daily Intelligence Update",
        replace_existing=True,
    )

    # 3:00 صباحاً — تقطير المعرفة (DeepSeek style)
    scheduler.add_job(
        daily_distillation,
        'cron', hour=3, minute=0,
        id="daily_distillation",
        name="Knowledge Distillation",
        replace_existing=True,
    )

    # كل أحد 4:00 صباحاً — ضغط ذاكرة كل الوكلاء
    scheduler.add_job(
        compress_all_agents,
        'cron', day_of_week='sun', hour=4,
        id="weekly_compression",
        name="Weekly Memory Compression",
        replace_existing=True,
    )

    # كل أحد 5:00 صباحاً — دورة التطور الذاتي
    scheduler.add_job(
        weekly_evolution_cycle,
        'cron', day_of_week='sun', hour=5,
        id="weekly_evolution",
        name="Weekly Evolution Cycle",
        replace_existing=True,
    )

    # v5: 1:00 صباحاً يومياً — اكتشاف معرفة جديدة (SelfBuilder)
    scheduler.add_job(
        _run_self_builder_discovery,
        'cron', hour=1, minute=0,
        id="self_builder_discovery",
        name="Self Builder - Daily Discovery",
        replace_existing=True,
    )

    # v5: كل أحد 6:00 صباحاً — التقييم الذاتي الأسبوعي
    scheduler.add_job(
        _run_weekly_self_assessment,
        'cron', day_of_week='sun', hour=6,
        id="weekly_self_assessment",
        name="Weekly Self Assessment",
        replace_existing=True,
    )

    # ── v7: 24/7 Continuous Training ──────────────────────
    # كل 4 ساعات — دورة تدريب كاملة (486 مهمة/يوم)
    scheduler.add_job(
        _run_training_cycle,
        'interval', hours=4,
        id="training_cycle",
        name="24/7 Training Cycle",
        replace_existing=True,
    )

    # كل 2 ساعة — مراقبة أداء
    scheduler.add_job(
        _run_performance_monitor,
        'interval', hours=2,
        id="performance_monitor",
        name="Performance Monitor",
        replace_existing=True,
    )

    # كل 6 ساعات — تدريب جماعي (multi-agent drill)
    scheduler.add_job(
        _run_multi_agent_drill,
        'interval', hours=6,
        id="multi_agent_drill",
        name="Multi-Agent Drill",
        replace_existing=True,
    )

    # كل 12 ساعة — مزامنة الذاكرة المحلية → السحابة
    scheduler.add_job(
        _run_cloud_sync,
        'interval', hours=12,
        id="cloud_sync",
        name="Cloud Memory Sync",
        replace_existing=True,
    )

    # ── Autonomy Tick (حلقة تطور قصيرة متكررة) ────────────
    # تُستدعى كل 15 دقيقة لتفعيل "التطور الذاتي" بدون انتظار وظائف الساعة/اليوم.
    scheduler.add_job(
        _run_autonomy_tick,
        'interval', minutes=15,
        id="autonomy_tick",
        name="Autonomy Loop Tick",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler v7 started — 24/7 Training Active:")
    logger.info("  Every 2h    → Performance Monitor")
    logger.info("  Every 4h    → Training Cycle (81 agents)")
    logger.info("  Every 6h    → Multi-Agent Drill")
    logger.info("  Every 12h   → Cloud Memory Sync")
    logger.info("  1:00 AM     → Self Builder Discovery")
    logger.info("  2:00 AM     → Intelligence Update")
    logger.info("  3:00 AM     → Knowledge Distillation")
    logger.info("  4:00 AM Sun → Memory Compression")
    logger.info("  5:00 AM Sun → Evolution Cycle")
    logger.info("  6:00 AM Sun → Self Assessment")
    logger.info("  Every 15m  → Autonomy Tick")
    logger.info("Press Ctrl+C to stop.")

    try:
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
        scheduler.shutdown()

def _bootstrap_router_for_autonomy():
    """
    تشغيل الـ updater كسيرفس مستقل يحتاج Router + Agents محملين،
    وإلا ستعمل وظائف التدريب/المراقبة بدون أي وكلاء فعلياً.
    """
    try:
        from router.smart_router import SmartRouter
        from tools.registry import build_tools_registry
        from core.base_agent import load_agent_from_json
        import os

        r = SmartRouter()
        tools = build_tools_registry()

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        agents_dir = os.path.join(base_dir, "agents")

        loaded = 0
        for cat in sorted(os.listdir(agents_dir)):
            cat_path = os.path.join(agents_dir, cat)
            if not os.path.isdir(cat_path) or cat.startswith("_"):
                continue
            for fname in sorted(os.listdir(cat_path)):
                if not fname.endswith(".json"):
                    continue
                try:
                    a = load_agent_from_json(os.path.join(cat_path, fname), tools)
                    r.register(a)
                    loaded += 1
                except Exception as e:
                    logger.warning(f"Failed to load agent {fname}: {e}")

        # اربط الـ router للمدرب المستمر
        try:
            from core.continuous_trainer import get_continuous_trainer
            get_continuous_trainer(r)
        except Exception as e:
            logger.warning(f"Trainer bootstrap failed: {e}")

        logger.info(f"Autonomy bootstrap: {loaded} agents loaded")
        global _AUTONOMY_ROUTER
        _AUTONOMY_ROUTER = r
        return r
    except Exception as e:
        logger.error(f"Autonomy bootstrap error: {e}")
        return None


def _get_autonomy_loop():
    global _AUTONOMY
    if _AUTONOMY is None:
        from core.autonomy_loop import AutonomyLoop
        _AUTONOMY = AutonomyLoop(router=_AUTONOMY_ROUTER)
    if _AUTONOMY_ROUTER is not None:
        _AUTONOMY.attach_router(_AUTONOMY_ROUTER)
    return _AUTONOMY


def _run_autonomy_tick():
    """كل 15 دقيقة — Tick صغير للتطور الذاتي"""
    logger.info("=== Autonomy Tick ===")
    try:
        loop = _get_autonomy_loop()
        res = loop.tick()
        logger.info(f"Autonomy tick done: ran={len(res.get('ran', []))} errors={len(res.get('errors', []))}")
    except Exception as e:
        logger.error(f"Autonomy tick error: {e}")


def _run_training_cycle():
    """كل 4 ساعات — دورة تدريب كاملة"""
    logger.info("=== 24/7 Training Cycle Started ===")
    try:
        from core.continuous_trainer import get_continuous_trainer
        trainer = get_continuous_trainer()
        result = trainer.train_cycle(max_agents=81)
        logger.info(f"Training complete: {result['passed']}/{result['trained']} passed")
    except Exception as e:
        logger.error(f"Training cycle error: {e}")


def _run_performance_monitor():
    """كل 2 ساعة — مراقبة أداء"""
    logger.info("=== Performance Monitor ===")
    try:
        from core.continuous_trainer import get_continuous_trainer
        trainer = get_continuous_trainer()
        result = trainer.performance_monitor()
        if result.get("alerts"):
            logger.warning(f"Performance alerts: {len(result['alerts'])} agents")
    except Exception as e:
        logger.error(f"Performance monitor error: {e}")


def _run_multi_agent_drill():
    """كل 6 ساعات — تدريب جماعي"""
    logger.info("=== Multi-Agent Drill ===")
    try:
        from core.continuous_trainer import get_continuous_trainer
        trainer = get_continuous_trainer()
        result = trainer.multi_agent_drill()
        logger.info(f"Drill complete: {result}")
    except Exception as e:
        logger.error(f"Multi-agent drill error: {e}")


def _run_cloud_sync():
    """كل 12 ساعة — مزامنة الذاكرة"""
    logger.info("=== Cloud Memory Sync ===")
    try:
        from memory.cloud_memory import get_cloud_memory
        cm = get_cloud_memory()
        result = cm.sync_local_to_cloud()
        logger.info(f"Cloud sync: {result}")
    except Exception as e:
        logger.error(f"Cloud sync error: {e}")


def _run_self_builder_discovery():
    """1:00 صباحاً — اكتشاف معرفة جديدة"""
    logger.info("=== Self Builder Discovery Started ===")
    try:
        from core.self_builder import SelfBuilder
        builder = SelfBuilder()
        result = builder.discover_and_add_knowledge()
        logger.info(f"Discovery complete: {len(result.get('github', []))} repos found")

        # إرسال تنبيه Telegram إذا وُجد شيء مهم
        from core.human_interface import get_human_interface
        hi = get_human_interface()
        repos = result.get("github", [])
        if repos:
            hi.notify(
                "اكتشافات جديدة",
                f"وجدت {len(repos)} مستودعات مفيدة على GitHub. "
                f"اكتب /pending لمراجعتها.",
                urgency="normal",
            )
    except Exception as e:
        logger.error(f"Self builder discovery error: {e}")


def _run_weekly_self_assessment():
    """كل أحد 6:00 صباحاً — التقييم الذاتي"""
    logger.info("=== Weekly Self Assessment Started ===")
    try:
        from core.self_builder import SelfBuilder
        builder = SelfBuilder()
        report = builder.weekly_self_assessment()
        logger.info(f"Self assessment complete: {len(report.get('knowledge_gaps', []))} gaps")
    except Exception as e:
        logger.error(f"Self assessment error: {e}")


# ── Entry Point ───────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Army81 Daily Updater")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run as scheduled service (2 AM daily)",
    )
    parser.add_argument(
        "--now",
        action="store_true",
        default=True,
        help="Run once immediately (default)",
    )
    args = parser.parse_args()

    if args.schedule:
        _bootstrap_router_for_autonomy()
        start_scheduler()
    else:
        summary = run_daily_update()
        print(f"\n✅ Daily update complete:")
        for k, v in summary.items():
            print(f"   {k}: {v}")
