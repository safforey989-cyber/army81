"""
Army81 CLI - واجهة سطر الأوامر
الطريقة الأسرع للتفاعل مع النظام
"""
import argparse
import json
import os
import sys
import logging
from datetime import datetime

# إضافة المسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.base_agent import BaseAgent
from router.smart_router import SmartRouter
from memory.memory_system import MemorySystem
from protocols.a2a import MessageBus, CollaborationManager
from updates.daily_updater import DailyUpdater, SelfImprover

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("army81")


class Army81System:
    """النظام المتكامل - يجمع كل المكونات"""

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.router = SmartRouter()
        self.memory = MemorySystem(base_dir=self.base_dir)
        self.message_bus = MessageBus()
        self.collab_manager = CollaborationManager(self.message_bus, self.router)
        self.updater = DailyUpdater(base_dir=self.base_dir)
        self.improver = SelfImprover(
            agents_dir=os.path.join(self.base_dir, "agents"),
            memory_system=self.memory
        )
        self._loaded = False

    def load_agents(self) -> int:
        """تحميل كل الوكلاء من ملفات JSON"""
        agents_dir = os.path.join(self.base_dir, "agents")
        count = 0
        for cat_dir in sorted(os.listdir(agents_dir)):
            cat_path = os.path.join(agents_dir, cat_dir)
            if not os.path.isdir(cat_path) or cat_dir.startswith("_"):
                continue
            for fname in sorted(os.listdir(cat_path)):
                if fname.endswith(".json") and not fname.endswith(".bak"):
                    fpath = os.path.join(cat_path, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        agent = BaseAgent(
                            agent_id=data["agent_id"],
                            name=data["name"],
                            name_ar=data["name_ar"],
                            category=data["category"],
                            description=data["description"],
                            system_prompt=data["system_prompt"],
                            model=data.get("model", "qwen3:8b"),
                            provider=data.get("provider", "ollama"),
                        )
                        self.router.register_agent(agent)
                        self.message_bus.register(agent.agent_id)
                        count += 1
                    except Exception as e:
                        logger.error(f"Failed to load {fpath}: {e}")
        self._loaded = True
        logger.info(f"Loaded {count} agents")
        return count

    def status(self) -> dict:
        """حالة النظام الكاملة"""
        return {
            "system": "Army81",
            "version": "0.1.0",
            "timestamp": datetime.now().isoformat(),
            "agents": self.router.get_status(),
            "memory": self.memory.get_status(),
            "message_bus": self.message_bus.get_stats(),
            "loaded": self._loaded,
        }

    def task(self, task_text: str, agent_id: str = None, category: str = None) -> dict:
        """تنفيذ مهمة"""
        if not self._loaded:
            self.load_agents()
        return self.router.route(
            task=task_text,
            preferred_agent=agent_id,
            preferred_category=category,
        )

    def pipeline(self, task_text: str, agents: list) -> dict:
        """تنفيذ مهمة عبر سلسلة وكلاء"""
        if not self._loaded:
            self.load_agents()
        return self.router.pipeline(task_text, agents)

    def update(self) -> dict:
        """تشغيل التحديث اليومي"""
        return self.updater.run_daily_update()

    def evaluate(self, agent_id: str) -> dict:
        """تقييم أداء وكيل"""
        episodes = self.memory.episodic.get_episodes(agent_id)
        return self.improver.evaluate_agent(agent_id, episodes)


def main():
    parser = argparse.ArgumentParser(description="Army81 - نظام 81 وكيل ذكاء اصطناعي")
    subparsers = parser.add_subparsers(dest="command", help="الأوامر المتاحة")

    # أمر status
    subparsers.add_parser("status", help="عرض حالة النظام")

    # أمر list
    subparsers.add_parser("list", help="عرض قائمة الوكلاء")

    # أمر task
    task_parser = subparsers.add_parser("task", help="تنفيذ مهمة")
    task_parser.add_argument("text", help="نص المهمة")
    task_parser.add_argument("--agent", "-a", help="معرف الوكيل المحدد")
    task_parser.add_argument("--category", "-c", help="فئة الوكلاء")

    # أمر pipeline
    pipe_parser = subparsers.add_parser("pipeline", help="تنفيذ سلسلة مهام")
    pipe_parser.add_argument("text", help="نص المهمة")
    pipe_parser.add_argument("--agents", "-a", nargs="+", required=True, help="سلسلة الوكلاء")

    # أمر update
    subparsers.add_parser("update", help="تشغيل التحديث اليومي")

    # أمر evaluate
    eval_parser = subparsers.add_parser("evaluate", help="تقييم وكيل")
    eval_parser.add_argument("agent_id", help="معرف الوكيل")

    # أمر serve
    serve_parser = subparsers.add_parser("serve", help="تشغيل خادم API")
    serve_parser.add_argument("--port", "-p", type=int, default=8181, help="رقم المنفذ")

    # أمر chat (تفاعلي)
    subparsers.add_parser("chat", help="وضع الدردشة التفاعلي")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    system = Army81System()

    if args.command == "status":
        count = system.load_agents()
        status = system.status()
        print(json.dumps(status, ensure_ascii=False, indent=2))

    elif args.command == "list":
        count = system.load_agents()
        agents = system.router.get_status()["agents_status"]
        print(f"\n{'='*70}")
        print(f"  Army81 - {len(agents)} وكيل مسجل")
        print(f"{'='*70}")
        current_cat = ""
        for a in agents:
            if a["category"] != current_cat:
                current_cat = a["category"]
                print(f"\n  [{current_cat}]")
            print(f"    {a['id']:6s} | {a['name']:25s} | {a['model']}")
        print(f"\n{'='*70}\n")

    elif args.command == "task":
        system.load_agents()
        result = system.task(args.text, agent_id=args.agent, category=args.category)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "pipeline":
        system.load_agents()
        result = system.pipeline(args.text, args.agents)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "update":
        result = system.update()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "evaluate":
        system.load_agents()
        result = system.evaluate(args.agent_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "serve":
        print(f"Starting Army81 API server on port {args.port}...")
        import uvicorn
        uvicorn.run("gateway:app", host="0.0.0.0", port=args.port, log_level="info",
                    app_dir=os.path.dirname(os.path.abspath(__file__)))

    elif args.command == "chat":
        system.load_agents()
        print(f"\n{'='*50}")
        print("  Army81 Interactive Chat")
        print(f"  {len(system.router.agents)} agents loaded")
        print(f"{'='*50}")
        print("  Commands: /list, /agent <id>, /status, /quit")
        print(f"{'='*50}\n")

        current_agent = None
        while True:
            try:
                prompt = input(f"[{current_agent or 'auto'}] > ").strip()
                if not prompt:
                    continue
                if prompt == "/quit":
                    break
                if prompt == "/list":
                    for a in system.router.agents.values():
                        print(f"  {a.agent_id}: {a.name_ar} ({a.name})")
                    continue
                if prompt.startswith("/agent "):
                    aid = prompt.split()[1].upper()
                    if aid in system.router.agents:
                        current_agent = aid
                        a = system.router.agents[aid]
                        print(f"  Switched to: {a.name_ar} ({a.name})")
                    else:
                        print(f"  Agent {aid} not found")
                    continue
                if prompt == "/status":
                    print(json.dumps(system.status(), ensure_ascii=False, indent=2))
                    continue

                result = system.task(prompt, agent_id=current_agent)
                print(f"\n  [{result.get('agent_name', '?')}] ({result.get('elapsed_seconds', 0)}s):")
                print(f"  {result.get('result', 'No result')}\n")

            except (KeyboardInterrupt, EOFError):
                print("\n  Goodbye!")
                break


if __name__ == "__main__":
    main()
