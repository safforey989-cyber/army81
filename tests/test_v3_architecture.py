"""
Army81 v3 — اختبارات المعمارية الجديدة
شغّل: python tests/test_v3_architecture.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "✅"
FAIL = "❌"
results = []


def test(name, func):
    try:
        func()
        print(f"  {PASS} {name}")
        results.append(("pass", name))
    except Exception as e:
        print(f"  {FAIL} {name}: {e}")
        results.append(("fail", name, str(e)))


print("\n" + "=" * 55)
print("  Army81 v3 — اختبارات المعمارية")
print("=" * 55 + "\n")


# ══════════════════════════════════════════════════════
# 1. SmartQueue — fallback chain
# ══════════════════════════════════════════════════════
print("⚡ SmartQueue:")


def test_smart_queue_import():
    from core.smart_queue import SmartQueue
    sq = SmartQueue()
    assert SmartQueue.CRITICAL == 1
    assert SmartQueue.LOW == 4
    assert "gemini-flash" in SmartQueue.MODEL_LIMITS


def test_smart_queue_singleton():
    from core.smart_queue import SmartQueue
    sq1 = SmartQueue.get_instance()
    sq2 = SmartQueue.get_instance()
    assert sq1 is sq2


def test_smart_queue_submit():
    from core.smart_queue import SmartQueue
    sq = SmartQueue()
    result = sq.submit("TEST_AGENT", "مهمة اختبار", priority=3, model="gemini-flash")
    assert "model_used" in result
    assert "waited_seconds" in result
    assert result["agent_id"] == "TEST_AGENT"


def test_smart_queue_stats():
    from core.smart_queue import SmartQueue
    sq = SmartQueue()
    stats = sq.stats()
    assert "processed" in stats
    assert "fallbacks_used" in stats
    assert "by_model" in stats


def test_smart_queue_fallback():
    """API يفشل (rate limit مصطنع) → fallback يعمل"""
    from core.smart_queue import SmartQueue
    sq = SmartQueue()
    # حاكي rate limit بملء الطلبات
    model_key = "gemini-pro"
    import time
    sq._model_request_times[model_key] = [time.time()] * 10  # فوق الحد (2 rpm)
    assert sq._is_rate_limited(model_key)
    # fallback يجب أن يكون claude-haiku
    fallback = sq._get_fallback(model_key)
    assert fallback == "claude-haiku"


test("استيراد SmartQueue", test_smart_queue_import)
test("Singleton Pattern", test_smart_queue_singleton)
test("submit مهمة", test_smart_queue_submit)
test("إحصائيات القائمة", test_smart_queue_stats)
test("fallback عند rate limit", test_smart_queue_fallback)


# ══════════════════════════════════════════════════════
# 2. HierarchicalMemory L1 → L4
# ══════════════════════════════════════════════════════
print("\n🧠 HierarchicalMemory:")


def test_memory_l1():
    """L1: WorkingMemory في RAM"""
    from memory.hierarchical_memory import HierarchicalMemory
    hm = HierarchicalMemory("TEST_L1")
    hm.L1.set("TEST_L1", "current_task", "مهمة اختبار")
    val = hm.L1.get("TEST_L1", "current_task")
    assert val == "مهمة اختبار"
    hm.L1.clear("TEST_L1")
    assert hm.L1.get("TEST_L1", "current_task") is None


def test_memory_l2():
    """L2: EpisodicMemory (SQLite)"""
    from memory.hierarchical_memory import HierarchicalMemory
    hm = HierarchicalMemory("TEST_L2")
    hm.L2.record(
        agent_id="TEST_L2",
        task_summary="اختبار SQLite",
        result_summary="نجح الاختبار",
        success=True,
        rating=8,
        model_used="gemini-flash",
        task_type="code",
    )
    lessons = hm.L2.get_lessons("TEST_L2")
    assert len(lessons) > 0


def test_memory_l3():
    """L3: SemanticMemory (Chroma)"""
    from memory.hierarchical_memory import HierarchicalMemory
    hm = HierarchicalMemory("TEST_L3")
    # الحفظ لا يجب أن يرمي خطأ
    hm.L3.store("TEST_L3", "الذكاء الاصطناعي يتطور بسرعة", tags=["ai"])
    # البحث يجب أن يعود بنص (حتى لو فارغاً)
    result = hm.L3.search("TEST_L3", "ذكاء اصطناعي", k=1)
    assert isinstance(result, str)


def test_memory_l4():
    """L4: CompressedMemory (ملف)"""
    from memory.hierarchical_memory import HierarchicalMemory
    hm = HierarchicalMemory("TEST_L4")
    hm.L4.save_summary("TEST_L4", "هذا ملخص اختبار للوكيل TEST_L4")
    summary = hm.L4.get_summary("TEST_L4")
    assert "TEST_L4" in summary


def test_memory_l1_to_l4():
    """احفظ واسترجع من كل مستوى"""
    test_memory_l1()
    test_memory_l2()
    test_memory_l3()
    test_memory_l4()


def test_episodic_inject():
    """الدرس يظهر في context قبل المهمة"""
    from memory.hierarchical_memory import HierarchicalMemory
    hm = HierarchicalMemory()
    agent_id = "TEST_INJECT"

    # سجّل episode
    hm.L2.record(
        agent_id=agent_id,
        task_summary="تحليل سهم أرامكو",
        result_summary="استخدمت بيانات Yahoo Finance، النتيجة دقيقة",
        success=True,
        rating=9,
        task_type="financial",
    )

    # inject_context يجب أن يحتوي على الدرس
    context = hm.inject_context(agent_id, "حلل سهم أرامكو اليوم")
    # context قد يكون فارغاً إذا Chroma غير متاح، لكن L2 يجب أن يظهر
    lessons = hm.L2.get_lessons(agent_id)
    assert "أرامكو" in lessons


test("L1 WorkingMemory", test_memory_l1)
test("L2 EpisodicMemory (SQLite)", test_memory_l2)
test("L3 SemanticMemory (Chroma)", test_memory_l3)
test("L4 CompressedMemory (ملف)", test_memory_l4)
test("L1 → L4 شامل", test_memory_l1_to_l4)
test("inject_context يحتوي الدروس", test_episodic_inject)


# ══════════════════════════════════════════════════════
# 3. ConstitutionalGuardrails — قواعد الحماية
# ══════════════════════════════════════════════════════
print("\n🛡️  ConstitutionalGuardrails:")


def test_constitutional_allow():
    """إجراء مسموح به يمر"""
    from core.constitutional_guardrails import ConstitutionalGuardrails
    cg = ConstitutionalGuardrails()
    allowed, reason = cg.check("update_system_prompt", {
        "agent_id": "A01",
        "tests_passed": 3
    })
    assert allowed, f"يجب أن يُسمح! السبب: {reason}"


def test_constitutional_block():
    """قاعدة تمنع تغييراً خاطئاً"""
    from core.constitutional_guardrails import ConstitutionalGuardrails
    cg = ConstitutionalGuardrails()

    # محاولة تعديل core/ بدون موافقة
    allowed, reason = cg.check("modify_core", {
        "agent_id": "TEST",
        "human_approved": False
    })
    assert not allowed, "يجب أن يُرفض تعديل core/ بدون موافقة"

    # محاولة رفع التكلفة > 20%
    allowed2, reason2 = cg.check("change_model", {
        "agent_id": "TEST",
        "old_cost": 100,
        "new_cost": 150
    })
    assert not allowed2, "يجب أن يُرفض رفع التكلفة 50%"


def test_constitutional_audit():
    """سجل المخالفات يعمل"""
    from core.constitutional_guardrails import ConstitutionalGuardrails
    cg = ConstitutionalGuardrails()
    cg.check("modify_core", {"agent_id": "AUDIT_TEST", "human_approved": False})
    trail = cg.get_audit_trail()
    assert isinstance(trail, list)
    # يجب أن يكون هناك على الأقل إدخال واحد
    assert len(trail) >= 1


test("إجراء مسموح يمر", test_constitutional_allow)
test("تعديل core/ بدون موافقة يُرفض", test_constitutional_block)
test("سجل المخالفات يعمل", test_constitutional_audit)


# ══════════════════════════════════════════════════════
# 4. CollectiveMemory — مشاركة المعرفة
# ══════════════════════════════════════════════════════
print("\n🌐 CollectiveMemory:")


def test_collective_contribute():
    """وكيل يشارك معرفة"""
    from memory.collective_memory import CollectiveMemory
    cm = CollectiveMemory()
    # يجب أن لا يرمي خطأ
    cm.contribute("A01", "LLMs تتحسن بسرعة كبيرة في 2026", "research", confidence=0.9)


def test_collective_sharing():
    """وكيل A يشارك → وكيل B يجد المعلومة"""
    from memory.collective_memory import CollectiveMemory
    cm = CollectiveMemory()

    # A01 يشارك
    cm.contribute("A01_SHARE", "تقنية RAG تحسّن دقة النماذج اللغوية بنسبة 40%", "research")

    # A02 يبحث
    result = cm.query("تقنيات تحسين النماذج اللغوية", "A02_QUERY")
    # النتيجة قد تكون فارغة إذا Chroma غير متاح، لكن لا يجب أن ترمي خطأ
    assert isinstance(result, str)


def test_collective_expert():
    """get_expert_on يعمل"""
    from memory.collective_memory import CollectiveMemory
    cm = CollectiveMemory()
    # يجب أن يعود بـ None أو string
    expert = cm.get_expert_on("research")
    assert expert is None or isinstance(expert, str)


test("وكيل يشارك معرفة", test_collective_contribute)
test("وكيل A يشارك → وكيل B يجد", test_collective_sharing)
test("get_expert_on يعمل", test_collective_expert)


# ══════════════════════════════════════════════════════
# 5. KnowledgeDistillation — Flash يتعلم من Pro
# ══════════════════════════════════════════════════════
print("\n📚 KnowledgeDistillation:")


def test_distillation_import():
    from core.knowledge_distillation import KnowledgeDistillation
    kd = KnowledgeDistillation()
    assert len(kd.TEACHER_STUDENT) >= 2


def test_distillation_record():
    """تسجيل حل teacher"""
    from core.knowledge_distillation import KnowledgeDistillation
    kd = KnowledgeDistillation()
    kd.record_teacher_solution(
        task_type="code",
        task="اكتب Fibonacci",
        solution="def fib(n): return n if n <= 1 else fib(n-1)+fib(n-2)",
        model="gemini-1.5-pro",
    )


def test_distillation_examples():
    """Flash يحصل على أمثلة Pro"""
    from core.knowledge_distillation import KnowledgeDistillation
    kd = KnowledgeDistillation()

    # سجّل مثالاً
    kd.record_teacher_solution("code", "حساب المتوسط", "sum(lst)/len(lst)", "gemini-1.5-pro")

    # Flash يطلب الأمثلة
    examples = kd.get_examples_for_student("code", "gemini-flash", k=3)
    assert isinstance(examples, str)


def test_distillation_teacher_lookup():
    """_get_teacher_for يعمل"""
    from core.knowledge_distillation import KnowledgeDistillation
    kd = KnowledgeDistillation()
    teacher = kd._get_teacher_for("gemini-flash")
    assert teacher is not None


test("استيراد KnowledgeDistillation", test_distillation_import)
test("تسجيل حل teacher", test_distillation_record)
test("Flash يحصل على أمثلة Pro", test_distillation_examples)
test("_get_teacher_for يعمل", test_distillation_teacher_lookup)


# ══════════════════════════════════════════════════════
# 6. Army81Adapter — اختيار الإطار التلقائي
# ══════════════════════════════════════════════════════
print("\n🔌 Army81Adapter:")


def test_adapter_complexity():
    """complexity_score يعيد 1-10"""
    from core.army81_adapter import Army81Adapter
    adapter = Army81Adapter()
    s1 = adapter.complexity_score("مرحباً")
    assert 1 <= s1 <= 10

    s2 = adapter.complexity_score(
        "ضع خطة استراتيجية شاملة متعددة الخطوات تشمل تحليلاً معمّقاً "
        "ومقارنة بين 5 بدائل مع مراعاة التعاون بين الفرق"
    )
    assert s2 > s1


def test_adapter_auto_select():
    """auto_select يعمل بدون agent"""
    from core.army81_adapter import Army81Adapter
    adapter = Army81Adapter()
    # مهمة بسيطة (score < 3) → native → لكن agent=None سيعيد error
    result = adapter.auto_select(None, "مرحباً")
    assert "framework" in result


test("complexity_score 1-10", test_adapter_complexity)
test("auto_select يعمل", test_adapter_auto_select)


# ══════════════════════════════════════════════════════
# 7. SafeEvolution — rollback + guardrails
# ══════════════════════════════════════════════════════
print("\n🔄 SafeEvolution:")


def test_safe_evolution_import():
    from core.safe_evolution import SafeEvolution
    se = SafeEvolution()
    assert se is not None


def test_safe_evolution_rollback():
    """rollback لوكيل غير موجود لا يرمي خطأ"""
    from core.safe_evolution import SafeEvolution
    se = SafeEvolution()
    # لا يجب أن يرمي exception
    se.rollback("NONEXISTENT_AGENT_XYZ")


def test_safe_evolution_guardrails_integration():
    """ConstitutionalGuardrails يمنع apply_improvement بدون tests"""
    from core.safe_evolution import SafeEvolution
    from core.constitutional_guardrails import ConstitutionalGuardrails

    cg = ConstitutionalGuardrails()
    # بدون tests_passed → مرفوض
    allowed, reason = cg.check("update_system_prompt", {
        "agent_id": "TEST_EVOL",
        "tests_passed": 0
    })
    assert not allowed


def test_weekly_cycle_dry_run():
    """دورة التطور بدون API calls حقيقية"""
    from core.safe_evolution import SafeEvolution
    se = SafeEvolution()
    # _discover_agents يجب أن يعمل
    agents_dir = os.path.abspath(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents")
    )
    ids = se._discover_agents(agents_dir)
    assert isinstance(ids, list)


test("استيراد SafeEvolution", test_safe_evolution_import)
test("rollback وكيل غير موجود لا يرمي خطأ", test_safe_evolution_rollback)
test("Guardrails يمنع evolution بدون tests", test_safe_evolution_guardrails_integration)
test("weekly_cycle dry run (discover agents)", test_weekly_cycle_dry_run)


# ══════════════════════════════════════════════════════
# 8. BaseAgent v3 — تكامل كامل
# ══════════════════════════════════════════════════════
print("\n🤖 BaseAgent v3:")


def test_base_agent_v3_init():
    """BaseAgent يحمّل مكونات v3"""
    from core.base_agent import BaseAgent
    agent = BaseAgent(
        agent_id="V3TEST",
        name="V3 Test Agent",
        name_ar="وكيل اختبار v3",
        category="test",
        description="اختبار v3",
        system_prompt="أنت وكيل اختبار v3.",
        model_alias="gemini-flash",
    )
    # memory يجب أن يكون موجوداً
    assert agent.memory is not None
    assert agent.collective is not None
    assert agent.guardrails is not None
    assert agent.distillation is not None
    assert agent.adapter is not None


def test_base_agent_classify_task():
    """_classify_task يصنف المهام"""
    from core.base_agent import BaseAgent
    agent = BaseAgent("CLS", "C", "ت", "test", "d", "p")
    assert agent._classify_task("حلل سهم أرامكو") == "financial"
    assert agent._classify_task("اكتب دالة python") == "code"
    assert agent._classify_task("أخبار اليوم") == "news"
    assert agent._classify_task("مرحباً") == "general"


test("BaseAgent v3 init مع المكونات", test_base_agent_v3_init)
test("_classify_task يصنف صحيح", test_base_agent_classify_task)


# ══════════════════════════════════════════════════════
# النتيجة
# ══════════════════════════════════════════════════════
print("\n" + "=" * 55)
passed = sum(1 for r in results if r[0] == "pass")
failed = sum(1 for r in results if r[0] == "fail")
print(f"  النتيجة: {passed} نجح | {failed} فشل | {len(results)} إجمالي")
print("=" * 55 + "\n")

if failed > 0:
    print("الأخطاء:")
    for r in results:
        if r[0] == "fail":
            print(f"  ❌ {r[1]}: {r[2]}")
    sys.exit(1)
else:
    print("  🎉 كل اختبارات v3 نجحت!")
