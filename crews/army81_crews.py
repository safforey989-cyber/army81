"""
army81_crews.py — CrewAI فرق العمل المتخصصة لنظام Army81

3 فرق متخصصة:
1. فريق التحليل الاستراتيجي: A01, A31, A32, A33
2. فريق البحث العلمي:       A07, A38, A39, A40
3. فريق إدارة الأزمات:      A29, A34, A35, A23
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Try importing CrewAI ──────────────────────────────────────────────────────
try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI not installed. Crews will run in fallback mode.")

# ── Try importing LLM client ──────────────────────────────────────────────────
try:
    from core.llm_client import LLMClient
    _llm = LLMClient()
except Exception:
    _llm = None

# ── Helper: load agent JSON ───────────────────────────────────────────────────
AGENTS_ROOT = Path(__file__).parent.parent / "agents"

def _load_agent_json(agent_id: str) -> dict:
    """Load agent JSON definition from any category folder."""
    for category_dir in AGENTS_ROOT.iterdir():
        if not category_dir.is_dir():
            continue
        for json_file in category_dir.glob("*.json"):
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("agent_id") == agent_id:
                    return data
            except Exception:
                continue
    raise FileNotFoundError(f"Agent {agent_id} not found in {AGENTS_ROOT}")


def _make_crewai_agent(agent_id: str, verbose: bool = False) -> "Agent":
    """Create a CrewAI Agent from an Army81 JSON definition."""
    data = _load_agent_json(agent_id)

    # Build LLM string for CrewAI
    model_name = data.get("model", "gemini-flash")
    model_map = {
        "gemini-flash": "gemini/gemini-1.5-flash",
        "gemini-pro":   "gemini/gemini-1.5-pro",
        "claude-fast":  "anthropic/claude-3-5-haiku-20241022",
        "claude-smart": "anthropic/claude-3-5-sonnet-20241022",
    }
    llm_str = model_map.get(model_name, "gemini/gemini-1.5-flash")

    return Agent(
        role=data.get("name", agent_id),
        goal=data.get("description", "مساعدة في إنجاز المهام"),
        backstory=data.get("system_prompt", ""),
        verbose=verbose,
        allow_delegation=False,
        llm=llm_str,
    )


# ── Fallback runner (when CrewAI is unavailable) ──────────────────────────────
def _fallback_run(team_name: str, agents_ids: list, task_desc: str) -> dict:
    """Run team task sequentially using LLMClient without CrewAI."""
    results = []
    for agent_id in agents_ids:
        try:
            data = _load_agent_json(agent_id)
            if _llm:
                prompt = f"{data.get('system_prompt', '')}\n\nالمهمة: {task_desc}"
                result = _llm.generate(prompt, model=data.get("model", "gemini-flash"))
            else:
                result = f"[{agent_id}] LLM غير متاح — وضع المحاكاة"
            results.append({"agent": agent_id, "result": result})
        except Exception as e:
            results.append({"agent": agent_id, "error": str(e)})

    combined = "\n\n".join(
        f"[{r['agent']}]: {r.get('result', r.get('error', ''))}" for r in results
    )
    return {
        "team": team_name,
        "mode": "fallback",
        "task": task_desc,
        "agents": agents_ids,
        "individual_results": results,
        "combined_output": combined,
    }


# ══════════════════════════════════════════════════════════════════════════════
# فريق 1: التحليل الاستراتيجي
# وكلاء: A01 (القائد الاستراتيجي), A31 (الاستخبارات), A32 (الجيوسياسة), A33 (المستقبليات)
# ══════════════════════════════════════════════════════════════════════════════

STRATEGIC_TEAM_IDS = ["A01", "A31", "A32", "A33"]

def run_strategic_analysis(task: str, verbose: bool = False) -> dict:
    """
    فريق التحليل الاستراتيجي.
    يحلل التحديات الاستراتيجية من أبعاد متعددة ويقدم توصيات شاملة.
    """
    team_name = "Strategic Analysis Team"

    if not CREWAI_AVAILABLE:
        return _fallback_run(team_name, STRATEGIC_TEAM_IDS, task)

    try:
        # إنشاء الوكلاء
        strategic_leader = _make_crewai_agent("A01", verbose)
        intel_agent      = _make_crewai_agent("A31", verbose)
        geo_agent        = _make_crewai_agent("A32", verbose)
        futures_agent    = _make_crewai_agent("A33", verbose)

        # تعريف المهام
        intel_task = Task(
            description=f"اجمع المعلومات الاستراتيجية وحلّل المشهد الراهن للمهمة التالية:\n{task}",
            agent=intel_agent,
            expected_output="تقرير استخباراتي شامل عن الوضع الراهن",
        )
        geo_task = Task(
            description=f"حلّل الأبعاد الجيوسياسية للمهمة:\n{task}\nبناءً على ما جمعه وكيل الاستخبارات.",
            agent=geo_agent,
            expected_output="تحليل جيوسياسي يشمل الفاعلين الرئيسيين والديناميكيات الإقليمية",
            context=[intel_task],
        )
        futures_task = Task(
            description=f"استشرف السيناريوهات المستقبلية للمهمة:\n{task}",
            agent=futures_agent,
            expected_output="3-5 سيناريوهات مستقبلية محتملة مع احتمالاتها",
            context=[intel_task, geo_task],
        )
        strategy_task = Task(
            description=(
                f"بناءً على التقارير السابقة، أعدّ توصيات استراتيجية شاملة للمهمة:\n{task}\n"
                "يجب أن تكون التوصيات قابلة للتنفيذ ومرتبة بالأولوية."
            ),
            agent=strategic_leader,
            expected_output="توصيات استراتيجية نهائية مرتبة حسب الأولوية",
            context=[intel_task, geo_task, futures_task],
        )

        crew = Crew(
            agents=[intel_agent, geo_agent, futures_agent, strategic_leader],
            tasks=[intel_task, geo_task, futures_task, strategy_task],
            process=Process.sequential,
            verbose=verbose,
        )

        result = crew.kickoff()
        return {
            "team": team_name,
            "mode": "crewai",
            "task": task,
            "agents": STRATEGIC_TEAM_IDS,
            "output": str(result),
        }

    except Exception as e:
        logger.error(f"CrewAI strategic crew failed: {e}")
        return _fallback_run(team_name, STRATEGIC_TEAM_IDS, task)


# ══════════════════════════════════════════════════════════════════════════════
# فريق 2: البحث العلمي
# وكلاء: A07 (الطب), A38 (الفيزياء/الكم), A39 (المناخ), A40 (رصد التكنولوجيا)
# ══════════════════════════════════════════════════════════════════════════════

RESEARCH_TEAM_IDS = ["A07", "A38", "A39", "A40"]

def run_scientific_research(task: str, verbose: bool = False) -> dict:
    """
    فريق البحث العلمي.
    يُجري أبحاثاً متعددة التخصصات ويدمج النتائج العلمية.
    """
    team_name = "Scientific Research Team"

    if not CREWAI_AVAILABLE:
        return _fallback_run(team_name, RESEARCH_TEAM_IDS, task)

    try:
        medical_agent  = _make_crewai_agent("A07", verbose)
        physics_agent  = _make_crewai_agent("A38", verbose)
        climate_agent  = _make_crewai_agent("A39", verbose)
        tech_agent     = _make_crewai_agent("A40", verbose)

        # المهمة الرئيسية: البحث الموازي ثم التجميع
        medical_task = Task(
            description=f"ابحث في الجانب الطبي/البيولوجي للموضوع:\n{task}",
            agent=medical_agent,
            expected_output="ملخص بحثي طبي/بيولوجي مدعوم بالأدلة",
        )
        physics_task = Task(
            description=f"ابحث في الجوانب الفيزيائية والكمية للموضوع:\n{task}",
            agent=physics_agent,
            expected_output="تحليل فيزيائي/تقني للموضوع",
        )
        climate_task = Task(
            description=f"ابحث في التأثيرات البيئية والمناخية للموضوع:\n{task}",
            agent=climate_agent,
            expected_output="تحليل بيئي ومناخي شامل",
        )
        synthesis_task = Task(
            description=(
                f"اجمع وادمج النتائج البحثية الثلاثة (طب، فيزياء، مناخ) لتقديم رؤية علمية "
                f"متكاملة حول:\n{task}\nحدّد أيضاً الفجوات البحثية وفرص الابتكار."
            ),
            agent=tech_agent,
            expected_output="تقرير علمي متكامل يدمج النتائج ويحدد الفرص",
            context=[medical_task, physics_task, climate_task],
        )

        crew = Crew(
            agents=[medical_agent, physics_agent, climate_agent, tech_agent],
            tasks=[medical_task, physics_task, climate_task, synthesis_task],
            process=Process.sequential,
            verbose=verbose,
        )

        result = crew.kickoff()
        return {
            "team": team_name,
            "mode": "crewai",
            "task": task,
            "agents": RESEARCH_TEAM_IDS,
            "output": str(result),
        }

    except Exception as e:
        logger.error(f"CrewAI research crew failed: {e}")
        return _fallback_run(team_name, RESEARCH_TEAM_IDS, task)


# ══════════════════════════════════════════════════════════════════════════════
# فريق 3: إدارة الأزمات
# وكلاء: A29 (حل النزاعات), A34 (إدارة الأزمات), A35 (الابتكار), A23 (إدارة التغيير)
# ══════════════════════════════════════════════════════════════════════════════

CRISIS_TEAM_IDS = ["A29", "A34", "A35", "A23"]

def run_crisis_management(task: str, verbose: bool = False) -> dict:
    """
    فريق إدارة الأزمات.
    يعالج الأزمات والتحديات الحرجة بسرعة وفعالية.
    """
    team_name = "Crisis Management Team"

    if not CREWAI_AVAILABLE:
        return _fallback_run(team_name, CRISIS_TEAM_IDS, task)

    try:
        conflict_agent  = _make_crewai_agent("A29", verbose)
        crisis_agent    = _make_crewai_agent("A34", verbose)
        innovation_agent = _make_crewai_agent("A35", verbose)
        change_agent    = _make_crewai_agent("A23", verbose)

        assessment_task = Task(
            description=f"قيّم الأزمة وحدّد مستوى الخطورة والأطراف المتأثرة:\n{task}",
            agent=crisis_agent,
            expected_output="تقييم الأزمة: الشدة، النطاق، الأطراف، الجدول الزمني",
        )
        conflict_task = Task(
            description=(
                f"حدّد النزاعات والتوترات الكامنة في هذه الأزمة وأقترح آليات حلّها:\n{task}"
            ),
            agent=conflict_agent,
            expected_output="خريطة النزاعات واستراتيجيات الحل",
            context=[assessment_task],
        )
        innovation_task = Task(
            description=(
                f"فكّر خارج الأطر التقليدية — ما الحلول الإبداعية غير المتوقعة لهذه الأزمة:\n{task}"
            ),
            agent=innovation_agent,
            expected_output="حلول إبداعية غير تقليدية للأزمة",
            context=[assessment_task, conflict_task],
        )
        response_plan_task = Task(
            description=(
                f"صمّم خطة استجابة شاملة لإدارة التغيير والخروج من الأزمة:\n{task}\n"
                "الخطة يجب أن تكون فورية (24-48 ساعة)، قصيرة المدى (أسبوع)، ومتوسطة المدى (شهر)."
            ),
            agent=change_agent,
            expected_output="خطة استجابة متكاملة 3 مراحل",
            context=[assessment_task, conflict_task, innovation_task],
        )

        crew = Crew(
            agents=[crisis_agent, conflict_agent, innovation_agent, change_agent],
            tasks=[assessment_task, conflict_task, innovation_task, response_plan_task],
            process=Process.sequential,
            verbose=verbose,
        )

        result = crew.kickoff()
        return {
            "team": team_name,
            "mode": "crewai",
            "task": task,
            "agents": CRISIS_TEAM_IDS,
            "output": str(result),
        }

    except Exception as e:
        logger.error(f"CrewAI crisis crew failed: {e}")
        return _fallback_run(team_name, CRISIS_TEAM_IDS, task)


# ══════════════════════════════════════════════════════════════════════════════
# واجهة موحدة
# ══════════════════════════════════════════════════════════════════════════════

TEAM_REGISTRY = {
    "strategic": {
        "name": "Strategic Analysis Team",
        "agents": STRATEGIC_TEAM_IDS,
        "runner": run_strategic_analysis,
        "description": "تحليل استراتيجي متكامل من أبعاد استخباراتية وجيوسياسية واستشرافية",
    },
    "research": {
        "name": "Scientific Research Team",
        "agents": RESEARCH_TEAM_IDS,
        "runner": run_scientific_research,
        "description": "بحث علمي متعدد التخصصات يدمج الطب والفيزياء والمناخ والتكنولوجيا",
    },
    "crisis": {
        "name": "Crisis Management Team",
        "agents": CRISIS_TEAM_IDS,
        "runner": run_crisis_management,
        "description": "إدارة الأزمات وتصميم خطط الاستجابة السريعة",
    },
}


def run_team(team_key: str, task: str, verbose: bool = False) -> dict:
    """
    تشغيل فريق محدد بمهمة معطاة.

    Args:
        team_key: "strategic" | "research" | "crisis"
        task: وصف المهمة
        verbose: طباعة تفاصيل التنفيذ

    Returns:
        dict with keys: team, mode, task, agents, output/combined_output
    """
    if team_key not in TEAM_REGISTRY:
        available = list(TEAM_REGISTRY.keys())
        return {"error": f"Team '{team_key}' not found. Available: {available}"}

    runner = TEAM_REGISTRY[team_key]["runner"]
    return runner(task, verbose=verbose)


def list_teams() -> list:
    """Return list of available teams with metadata."""
    return [
        {
            "key": key,
            "name": info["name"],
            "agents": info["agents"],
            "description": info["description"],
            "crewai_available": CREWAI_AVAILABLE,
        }
        for key, info in TEAM_REGISTRY.items()
    ]


# ── CLI entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("الاستخدام: python crews/army81_crews.py <team> <task>")
        print("الفرق المتاحة:", list(TEAM_REGISTRY.keys()))
        sys.exit(1)

    team  = sys.argv[1]
    task  = " ".join(sys.argv[2:])

    print(f"\n🚀 تشغيل فريق: {team}")
    print(f"📋 المهمة: {task}\n")

    result = run_team(team, task, verbose=True)

    print("\n" + "═" * 60)
    print("✅ النتيجة النهائية:")
    print("═" * 60)
    output = result.get("output") or result.get("combined_output") or result.get("error", "لا نتيجة")
    print(output)
