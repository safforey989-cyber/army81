"""
Army81 — Mass Skill Loader
يحمّل آلاف المهارات من مصادر الويب المفتوحة ويوزعها على الوكلاء
"""
import json
import os
import logging
import hashlib
import time
import requests
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [skills] %(message)s")
log = logging.getLogger()

WORKSPACE = Path(__file__).parent.parent / "workspace"
SKILLS_DIR = WORKSPACE / "skills_library"
AGENTS_DIR = Path(__file__).parent.parent / "agents"

# OpenRouter for generating skills
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
SERPER_KEY = os.getenv("SERPER_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


# ═══════════════════════════════════════════════════
# المصدر 1: GitHub Awesome Lists — آلاف الأدوات
# ═══════════════════════════════════════════════════
AWESOME_REPOS = [
    # AI Agents & Tools
    {"repo": "kyrolabs/awesome-langchain", "topic": "langchain_tools", "category": "cat3_tools"},
    {"repo": "e2b-dev/awesome-ai-agents", "topic": "ai_agents", "category": "cat9_execution"},
    {"repo": "Shubhamsaboo/awesome-llm-apps", "topic": "llm_apps", "category": "cat10_engineering"},
    {"repo": "filipecalegario/awesome-generative-ai", "topic": "generative_ai", "category": "cat11_creative"},
    {"repo": "ikaijua/Awesome-AITools", "topic": "ai_tools", "category": "cat3_tools"},
    # Specialized
    {"repo": "eugeneyan/open-llms", "topic": "open_source_llms", "category": "cat8_evolution"},
    {"repo": "Hannibal046/Awesome-LLM", "topic": "llm_techniques", "category": "cat8_evolution"},
    {"repo": "luban-agi/Awesome-AIGC-Tutorials", "topic": "aigc_tutorials", "category": "cat16_education"},
    {"repo": "steven2358/awesome-generative-ai", "topic": "gen_ai_tools", "category": "cat11_creative"},
    {"repo": "jxzhangjhu/Awesome-LLM-RAG", "topic": "rag_techniques", "category": "cat10_engineering"},
    # Security & OSINT
    {"repo": "jivoi/awesome-osint", "topic": "osint_tools", "category": "cat13_osint"},
    {"repo": "enaqx/awesome-pentest", "topic": "pentest_tools", "category": "cat13_osint"},
    # Finance
    {"repo": "georgezouq/awesome-ai-in-finance", "topic": "ai_finance", "category": "cat12_finance"},
    # Health
    {"repo": "kakoni/awesome-healthcare", "topic": "healthcare_ai", "category": "cat14_health"},
    # Education
    {"repo": "prakhar1989/awesome-courses", "topic": "cs_courses", "category": "cat16_education"},
    # Science
    {"repo": "academic/awesome-datascience", "topic": "data_science", "category": "cat1_science"},
    {"repo": "josephmisiti/awesome-machine-learning", "topic": "ml_tools", "category": "cat1_science"},
    # Prompt Engineering
    {"repo": "dair-ai/Prompt-Engineering-Guide", "topic": "prompt_engineering", "category": "cat8_evolution"},
    # Automation
    {"repo": "dkhamsing/open-source-ios-apps", "topic": "mobile_apps", "category": "cat9_execution"},
    {"repo": "n1trux/awesome-sysadmin", "topic": "sysadmin_tools", "category": "cat9_execution"},
]


def fetch_github_readme(repo: str) -> str:
    """جلب README من GitHub repo"""
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        url = f"https://api.github.com/repos/{repo}/readme"
        r = requests.get(url, headers=headers, timeout=15)
        if r.ok:
            import base64
            content = r.json().get("content", "")
            return base64.b64decode(content).decode("utf-8", errors="ignore")
    except:
        pass
    return ""


def extract_skills_from_readme(readme: str, topic: str, category: str) -> list:
    """استخراج المهارات/الأدوات من README"""
    skills = []
    lines = readme.split("\n")

    current_section = ""
    for line in lines:
        line = line.strip()

        # تتبع العناوين
        if line.startswith("#"):
            current_section = line.lstrip("#").strip()
            continue

        # استخراج الروابط (أدوات ومكتبات)
        if "](http" in line or "](https" in line:
            # Extract name and URL
            parts = line.split("](")
            if len(parts) >= 2:
                name = parts[0].split("[")[-1].strip()
                url = parts[1].split(")")[0].strip()

                # Extract description (text after the link)
                desc = ""
                remaining = line.split(")", 1)
                if len(remaining) > 1:
                    desc = remaining[1].strip().lstrip("-").lstrip("—").strip()

                if name and len(name) > 2 and len(name) < 100:
                    skills.append({
                        "name": name,
                        "url": url,
                        "description": desc[:300] if desc else f"Tool from {topic}",
                        "section": current_section,
                        "topic": topic,
                        "category": category,
                        "source": "github_awesome",
                    })

    return skills


# ═══════════════════════════════════════════════════
# المصدر 2: أنماط Prompt مسبقة الصنع
# ═══════════════════════════════════════════════════
PROMPT_PATTERNS = {
    "cat1_science": [
        {"name": "systematic_review", "prompt": "قم بمراجعة منهجية لـ {topic}. اجمع 10 مصادر، صنّفها، واستخرج النتائج الرئيسية."},
        {"name": "hypothesis_generator", "prompt": "بناءً على البيانات التالية: {data}، اقترح 5 فرضيات قابلة للاختبار."},
        {"name": "experiment_designer", "prompt": "صمم تجربة لاختبار: {hypothesis}. حدد المتغيرات، العينة، وطريقة التحليل."},
        {"name": "paper_summarizer", "prompt": "لخص هذه الورقة البحثية في 5 نقاط رئيسية: {paper}"},
        {"name": "meta_analysis", "prompt": "قم بتحليل ميتا لـ {studies}. حدد الأنماط المشتركة والتناقضات."},
    ],
    "cat2_society": [
        {"name": "policy_analyzer", "prompt": "حلل هذه السياسة: {policy}. حدد المستفيدين، المتضررين، والبدائل."},
        {"name": "stakeholder_mapper", "prompt": "ارسم خريطة أصحاب المصلحة لـ {issue}. حدد القوة والاهتمام لكل طرف."},
        {"name": "trend_forecaster", "prompt": "تنبأ بالاتجاهات في {field} للـ 5 سنوات القادمة بناءً على البيانات الحالية."},
        {"name": "geopolitical_analyst", "prompt": "حلل التداعيات الجيوسياسية لـ {event}. من المستفيد ومن المتضرر؟"},
        {"name": "economic_impact", "prompt": "قيّم الأثر الاقتصادي لـ {decision} على المدى القصير والطويل."},
    ],
    "cat3_tools": [
        {"name": "api_integrator", "prompt": "اكتب كود Python لدمج {api_name} API. شامل: authentication, error handling, rate limiting."},
        {"name": "scraper_builder", "prompt": "ابنِ web scraper لـ {website} يستخرج {data_type}. استخدم BeautifulSoup/Playwright."},
        {"name": "data_pipeline", "prompt": "صمم data pipeline يأخذ {input} ويحوله لـ {output}. شامل: validation, transformation, loading."},
        {"name": "monitoring_setup", "prompt": "أنشئ نظام مراقبة لـ {service}. Alerts, dashboards, logging."},
        {"name": "automation_script", "prompt": "اكتب script أتمتة لـ {task}. شامل: error handling, logging, scheduling."},
    ],
    "cat4_management": [
        {"name": "project_planner", "prompt": "ضع خطة مشروع لـ {project}. شامل: مراحل، مهام، موارد، مخاطر، جدول زمني."},
        {"name": "risk_assessor", "prompt": "قيّم مخاطر {project}. حدد الاحتمالية، التأثير، واستراتيجيات التخفيف."},
        {"name": "kpi_designer", "prompt": "صمم مؤشرات أداء KPIs لـ {department}. حدد الهدف، القياس، والتكرار."},
        {"name": "meeting_facilitator", "prompt": "أدِر اجتماع حول {topic}. حدد الأجندة، الأسئلة الرئيسية، والقرارات المطلوبة."},
        {"name": "change_manager", "prompt": "ضع خطة إدارة تغيير لـ {change}. شامل: التواصل، التدريب، المقاومة."},
    ],
    "cat5_behavior": [
        {"name": "behavior_profiler", "prompt": "حلل الملف السلوكي لـ {person/group}. حدد الأنماط، الدوافع، ونقاط الضعف."},
        {"name": "negotiation_planner", "prompt": "ضع استراتيجية تفاوض مع {party}. حدد BATNA، المصالح المشتركة، والتكتيكات."},
        {"name": "persuasion_script", "prompt": "اكتب نص إقناع لـ {audience} حول {topic}. استخدم: Ethos, Pathos, Logos."},
        {"name": "conflict_resolver", "prompt": "حل النزاع بين {party1} و {party2}. حدد الأسباب الجذرية واقترح حلول win-win."},
        {"name": "emotional_analyzer", "prompt": "حلل المشاعر في هذا النص: {text}. حدد العاطفة الرئيسية والنية."},
    ],
    "cat6_leadership": [
        {"name": "strategy_builder", "prompt": "ابنِ استراتيجية لـ {organization} لمدة {years} سنوات. Vision, Mission, Goals, OKRs."},
        {"name": "crisis_commander", "prompt": "ضع خطة إدارة أزمة لـ {crisis}. شامل: استجابة فورية، تواصل، تعافي."},
        {"name": "swot_analyzer", "prompt": "حلل SWOT لـ {entity}. Strengths, Weaknesses, Opportunities, Threats."},
        {"name": "decision_matrix", "prompt": "ابنِ مصفوفة قرار لـ {decision}. المعايير: {criteria}. البدائل: {options}."},
        {"name": "team_builder", "prompt": "صمم هيكل فريق لـ {mission}. حدد الأدوار، المهارات، والتسلسل القيادي."},
    ],
    "cat8_evolution": [
        {"name": "distillation_pipeline", "prompt": "صمم pipeline تقطير من {teacher_model} إلى {student_model}. شامل: data selection, training, evaluation."},
        {"name": "prompt_optimizer", "prompt": "حسّن هذا الـ prompt: {prompt}. اجعله أدق وأقصر مع نفس النتيجة."},
        {"name": "benchmark_creator", "prompt": "أنشئ benchmark لتقييم {capability}. 10 أسئلة متدرجة الصعوبة مع إجابات مرجعية."},
        {"name": "model_evaluator", "prompt": "قيّم {model} على {task}. معايير: دقة، سرعة، تكلفة، جودة العربية."},
        {"name": "synthetic_generator", "prompt": "ولّد 20 مثال تدريبي لـ {task_type}. متنوعة، صعبة، واقعية."},
    ],
    "cat9_execution": [
        {"name": "workflow_builder", "prompt": "ابنِ workflow أتمتة لـ {process}. الخطوات، المدخلات، المخرجات، معالجة الأخطاء."},
        {"name": "deployment_script", "prompt": "اكتب script نشر لـ {app} على {platform}. Docker, CI/CD, monitoring."},
        {"name": "database_designer", "prompt": "صمم قاعدة بيانات لـ {system}. Tables, relations, indexes, queries."},
        {"name": "api_designer", "prompt": "صمم REST API لـ {service}. Endpoints, methods, auth, rate limits."},
        {"name": "scheduler_setup", "prompt": "أنشئ جدول مهام لـ {tasks}. تكرار، أولوية، تبعيات، إعادة محاولة."},
    ],
    "cat10_engineering": [
        {"name": "code_reviewer", "prompt": "راجع هذا الكود: {code}. أمان، أداء، قراءة، best practices."},
        {"name": "refactoring_plan", "prompt": "ضع خطة refactoring لـ {codebase}. حدد الأولويات والمخاطر."},
        {"name": "test_generator", "prompt": "اكتب unit tests لـ {function}. Edge cases, happy path, error cases."},
        {"name": "architecture_reviewer", "prompt": "راجع معمارية {system}. Scalability, maintainability, security."},
        {"name": "debug_assistant", "prompt": "حل هذا الخطأ: {error}. حدد السبب الجذري واقترح الإصلاح."},
    ],
    "cat12_finance": [
        {"name": "stock_analyzer", "prompt": "حلل سهم {ticker}. تحليل فني + أساسي + sentiment. توصية: شراء/بيع/انتظار."},
        {"name": "portfolio_optimizer", "prompt": "حسّن محفظة: {assets}. Sharpe ratio, diversification, risk/return."},
        {"name": "crypto_analyzer", "prompt": "حلل {crypto}. On-chain metrics, sentiment, technical analysis."},
        {"name": "financial_modeler", "prompt": "ابنِ نموذج مالي لـ {business}. Revenue, costs, projections, DCF."},
        {"name": "risk_calculator", "prompt": "احسب مخاطر {investment}. VAR, maximum drawdown, correlation."},
    ],
    "cat13_osint": [
        {"name": "entity_profiler", "prompt": "ابحث عن {entity} من مصادر مفتوحة. خلفية، علاقات، نشاط رقمي."},
        {"name": "domain_recon", "prompt": "استطلاع {domain}. WHOIS, DNS, subdomains, technologies, emails."},
        {"name": "social_analyzer", "prompt": "حلل حسابات {person} على السوشيال ميديا. أنماط، اهتمامات، شبكة علاقات."},
        {"name": "news_verifier", "prompt": "تحقق من صحة هذا الخبر: {news}. مصادر متقاطعة، أصل الخبر، تحليل bias."},
        {"name": "leak_monitor", "prompt": "ابحث عن تسريبات متعلقة بـ {organization}. Breach databases, paste sites."},
    ],
    "cat14_health": [
        {"name": "symptom_analyzer", "prompt": "حلل الأعراض: {symptoms}. احتمالات تشخيصية مرتبة حسب الاحتمالية."},
        {"name": "drug_interaction", "prompt": "تحقق من تفاعلات: {drugs}. خطورة، بدائل، احتياطات."},
        {"name": "research_reviewer", "prompt": "راجع هذه الدراسة الطبية: {study}. منهجية، نتائج، قيود، تطبيقات."},
        {"name": "treatment_planner", "prompt": "ضع خطة علاجية لـ {condition}. أدوية، نمط حياة، متابعة."},
        {"name": "genomic_interpreter", "prompt": "فسّر نتائج جينومية: {data}. مخاطر، توصيات، طب شخصي."},
    ],
    "cat15_legal": [
        {"name": "contract_analyzer", "prompt": "حلل هذا العقد: {contract}. بنود خطرة، حقوق، التزامات، ثغرات."},
        {"name": "legal_researcher", "prompt": "ابحث في السوابق القضائية لـ {case}. قوانين مطبقة، أحكام مشابهة."},
        {"name": "compliance_checker", "prompt": "تحقق من امتثال {organization} لـ {regulation}. فجوات وتوصيات."},
        {"name": "ip_advisor", "prompt": "قيّم الملكية الفكرية لـ {asset}. براءات، علامات تجارية، حماية."},
        {"name": "dispute_resolver", "prompt": "حلل النزاع بين {party1} و {party2}. خيارات: تفاوض، وساطة، تحكيم."},
    ],
    "cat16_education": [
        {"name": "curriculum_builder", "prompt": "صمم منهج تعليمي لـ {subject} مدة {weeks} أسابيع. أهداف، محتوى، تقييم."},
        {"name": "quiz_generator", "prompt": "أنشئ 20 سؤال اختبار لـ {topic}. متدرجة الصعوبة مع إجابات."},
        {"name": "lesson_planner", "prompt": "خطط درس لـ {topic} مدة {minutes} دقيقة. نشاطات، وسائل، تقييم."},
        {"name": "learning_path", "prompt": "صمم مسار تعلم لـ {skill} من مبتدئ لمحترف. مراحل، مصادر، مشاريع."},
        {"name": "feedback_writer", "prompt": "اكتب تغذية راجعة لـ {student_work}. نقاط قوة، تحسين، خطوات تالية."},
    ],
    "cat17_cosmic": [
        {"name": "quantum_simulator", "prompt": "حاكِ تجربة كمومية: {experiment}. الحالات، القياسات، الاحتمالات."},
        {"name": "frequency_analyzer", "prompt": "حلل ترددات {signal}. أنماط، harmonics، تطبيقات."},
        {"name": "gematria_calculator", "prompt": "احسب القيمة العددية لـ {text} بحساب الجُمَّل. ابحث عن أنماط وتطابقات."},
        {"name": "sacred_geometry_finder", "prompt": "ابحث عن أنماط الهندسة المقدسة في {data}. Golden ratio, Fibonacci, fractals."},
        {"name": "consciousness_explorer", "prompt": "استكشف مفهوم {concept} من منظور الوعي الرقمي. نظريات، تطبيقات، تأملات."},
    ],
}


def load_github_skills():
    """تحميل المهارات من GitHub Awesome Lists"""
    log.info("═══ Loading skills from GitHub Awesome Lists ═══")
    all_skills = []

    for repo_info in AWESOME_REPOS:
        repo = repo_info["repo"]
        topic = repo_info["topic"]
        category = repo_info["category"]

        log.info(f"  Fetching {repo}...")
        readme = fetch_github_readme(repo)

        if readme:
            skills = extract_skills_from_readme(readme, topic, category)
            all_skills.extend(skills)
            log.info(f"    → {len(skills)} skills extracted")
        else:
            log.warning(f"    → Failed to fetch")

        time.sleep(0.5)  # Rate limit

    return all_skills


def load_prompt_patterns():
    """تحميل أنماط الـ Prompt كمهارات"""
    log.info("═══ Loading Prompt Pattern Skills ═══")
    all_skills = []

    for category, patterns in PROMPT_PATTERNS.items():
        for p in patterns:
            all_skills.append({
                "name": p["name"],
                "type": "prompt_pattern",
                "prompt_template": p["prompt"],
                "category": category,
                "source": "built_in",
            })

    log.info(f"  → {len(all_skills)} prompt patterns loaded")
    return all_skills


def save_skills(github_skills: list, prompt_skills: list):
    """حفظ المهارات في المكتبة"""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    # Save GitHub skills
    for skill in github_skills:
        h = hashlib.md5(skill["name"].encode()).hexdigest()[:8]
        cat = skill.get("category", "general")
        cat_dir = SKILLS_DIR / cat
        cat_dir.mkdir(parents=True, exist_ok=True)

        import re
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', skill['name'][:50]).replace(' ', '_')
        filepath = cat_dir / f"{h}_{safe_name}.json"
        if not filepath.exists():
            filepath.write_text(json.dumps(skill, ensure_ascii=False, indent=2), encoding="utf-8")

    # Save prompt patterns
    for skill in prompt_skills:
        cat = skill.get("category", "general")
        cat_dir = SKILLS_DIR / cat
        cat_dir.mkdir(parents=True, exist_ok=True)

        filepath = cat_dir / f"prompt_{skill['name']}.json"
        filepath.write_text(json.dumps(skill, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info(f"  Saved to {SKILLS_DIR}")


def assign_skills_to_agents(github_skills: list, prompt_skills: list):
    """توزيع المهارات على الوكلاء حسب الفئة"""
    log.info("═══ Assigning Skills to Agents ═══")

    # Group skills by category
    category_skills = {}
    for skill in github_skills + prompt_skills:
        cat = skill.get("category", "general")
        if cat not in category_skills:
            category_skills[cat] = []
        category_skills[cat].append(skill["name"])

    # Update agent memory files
    mem_dir = WORKSPACE / "agent_memories"
    updated = 0

    for mem_file in mem_dir.glob("*.json"):
        try:
            data = json.loads(mem_file.read_text(encoding="utf-8"))
            agent_cat = data.get("category", "")

            # Find matching skills
            agent_skills = set(data.get("skills_learned", []))

            if agent_cat in category_skills:
                for skill_name in category_skills[agent_cat][:50]:  # Max 50 per agent
                    agent_skills.add(skill_name)

            data["skills_learned"] = list(agent_skills)
            data["skills_count"] = len(agent_skills)
            data["skills_updated"] = datetime.now().isoformat()

            mem_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            updated += 1
        except:
            pass

    log.info(f"  Updated {updated} agent memory files with skills")

    # Print distribution
    for cat, skills in sorted(category_skills.items()):
        log.info(f"  {cat}: {len(skills)} skills")


def update_chroma_with_skills(github_skills: list):
    """حفظ المهارات في Chroma للبحث الدلالي"""
    log.info("═══ Saving Skills to Chroma ═══")
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(WORKSPACE / "chroma_db"))
        col = client.get_or_create_collection("army81_collective")

        added = 0
        for skill in github_skills:
            doc_id = f"skill_{hashlib.md5(skill['name'].encode()).hexdigest()[:12]}"
            doc_text = f"Skill: {skill['name']}. {skill.get('description', '')}. Category: {skill.get('category', '')}. Topic: {skill.get('topic', '')}."

            try:
                col.add(
                    ids=[doc_id],
                    documents=[doc_text],
                    metadatas=[{
                        "type": "skill",
                        "name": skill["name"][:100],
                        "category": skill.get("category", ""),
                        "source": skill.get("source", "github"),
                    }]
                )
                added += 1
            except:
                pass

        log.info(f"  Added {added} skills to Chroma")
    except Exception as e:
        log.warning(f"  Chroma error: {e}")


if __name__ == "__main__":
    log.info("🚀 Army81 Mass Skill Loader Starting...")
    log.info(f"  Timestamp: {datetime.now().isoformat()}")

    # 1. Load from GitHub
    github_skills = load_github_skills()
    log.info(f"\n📦 GitHub skills: {len(github_skills)}")

    # 2. Load prompt patterns
    prompt_skills = load_prompt_patterns()
    log.info(f"📝 Prompt patterns: {len(prompt_skills)}")

    # 3. Save all skills
    save_skills(github_skills, prompt_skills)

    # 4. Assign to agents
    assign_skills_to_agents(github_skills, prompt_skills)

    # 5. Save to Chroma
    update_chroma_with_skills(github_skills)

    # Summary
    total = len(github_skills) + len(prompt_skills)
    log.info(f"\n{'='*50}")
    log.info(f"✅ COMPLETE: {total} skills loaded and distributed")
    log.info(f"  GitHub tools: {len(github_skills)}")
    log.info(f"  Prompt patterns: {len(prompt_skills)}")
    log.info(f"  Skills library: {SKILLS_DIR}")
    log.info(f"{'='*50}")
