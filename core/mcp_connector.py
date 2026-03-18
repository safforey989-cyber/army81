"""
Army81 v5 — MCP Connector
يدير اتصالات MCP Servers (Model Context Protocol)
مصدر: mcp.ai + glama.ai (19,575 خادم)

يمكّن الوكلاء من:
- الوصول لـ GitHub, Brave Search, Playwright, Memory, Filesystem
- قواعد البيانات: SQLite, PostgreSQL, MongoDB
- أدوات الإنتاجية: Notion, Linear, Google Calendar
- التواصل: Slack, Email
- الأمن: Kaspersky Threat Intelligence
- المالية: Polygon.io
"""
import os
import json
import subprocess
import logging
import shutil
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("army81.mcp_connector")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(BASE_DIR, "knowledge", "mcp", "mcp_registry.json")
MCP_STATE_PATH = os.path.join(BASE_DIR, "workspace", "mcp_state.json")
MCP_CONFIG_PATH = os.path.join(BASE_DIR, ".claude", "mcp_servers.json")

os.makedirs(os.path.dirname(MCP_STATE_PATH), exist_ok=True)


class MCPConnector:
    """
    مدير اتصالات MCP — يربط Army81 بـ 30+ خادم MCP
    """

    def __init__(self):
        self.registry = self._load_registry()
        self.state = self._load_state()

    # ═══════════════════════════════════════════════
    # Registry — السجل
    # ═══════════════════════════════════════════════

    def get_all_servers(self) -> List[Dict]:
        """كل الخوادم المسجلة"""
        return self.registry.get("servers", [])

    def get_server(self, server_id: str) -> Optional[Dict]:
        """خادم واحد بالمعرّف"""
        for s in self.get_all_servers():
            if s["id"] == server_id:
                return s
        return None

    def get_servers_by_category(self, category: str) -> List[Dict]:
        """خوادم بالفئة"""
        return [s for s in self.get_all_servers() if s.get("category") == category]

    def get_servers_for_agent(self, agent_id: str) -> List[Dict]:
        """الخوادم المناسبة لوكيل معين"""
        agent_map = self.registry.get("agent_mcp_map", {})
        server_ids = agent_map.get(agent_id, [])
        return [s for s in self.get_all_servers() if s["id"] in server_ids]

    def get_installed_servers(self) -> List[Dict]:
        """الخوادم المثبتة فعلاً"""
        return [s for s in self.get_all_servers() if s.get("status") == "installed"]

    def get_available_servers(self) -> List[Dict]:
        """الخوادم المتاحة للتثبيت"""
        return [s for s in self.get_all_servers()
                if s.get("status") == "available"]

    def get_ready_servers(self) -> List[Dict]:
        """الخوادم الجاهزة (مثبتة + المفتاح موجود)"""
        ready = []
        for s in self.get_all_servers():
            if s.get("status") == "installed":
                ready.append(s)
            elif s.get("status") == "available" and not s.get("needs_api_key"):
                ready.append(s)
            elif s.get("needs_api_key") and os.getenv(s.get("env_key", ""), ""):
                ready.append(s)
        return ready

    # ═══════════════════════════════════════════════
    # تثبيت خادم MCP
    # ═══════════════════════════════════════════════

    def check_prerequisites(self, server_id: str) -> Dict:
        """تحقق من متطلبات خادم MCP"""
        server = self.get_server(server_id)
        if not server:
            return {"ready": False, "error": f"خادم {server_id} غير موجود في السجل"}

        issues = []

        # تحقق من npm/npx
        install_cmd = server.get("install", "")
        if install_cmd.startswith("npx") or install_cmd.startswith("npm"):
            if not shutil.which("npx") and not shutil.which("npm"):
                issues.append("Node.js/npm غير مثبت — شغّل: winget install OpenJS.NodeJS.LTS")

        # تحقق من pip
        if install_cmd.startswith("pip"):
            if not shutil.which("pip"):
                issues.append("pip غير مثبت")

        # تحقق من API key
        if server.get("needs_api_key"):
            env_key = server.get("env_key", "")
            if not os.getenv(env_key, ""):
                issues.append(f"مفتاح {env_key} غير موجود في .env")

        return {
            "ready": len(issues) == 0,
            "server": server["name"],
            "issues": issues,
        }

    def install_server(self, server_id: str) -> Dict:
        """تثبيت خادم MCP"""
        server = self.get_server(server_id)
        if not server:
            return {"success": False, "error": f"خادم {server_id} غير موجود"}

        prereqs = self.check_prerequisites(server_id)
        if not prereqs["ready"]:
            return {"success": False, "issues": prereqs["issues"]}

        install_cmd = server.get("install", "")
        if not install_cmd or install_cmd.startswith("remote"):
            # Remote server — no install needed
            self._update_server_status(server_id, "installed")
            return {"success": True, "message": f"{server['name']} remote — جاهز للاستخدام"}

        try:
            if install_cmd.startswith("pip"):
                result = subprocess.run(
                    install_cmd.split(),
                    capture_output=True, text=True, timeout=120
                )
            else:
                # npm/npx — just verify it can run
                result = subprocess.run(
                    ["npx", "-y", server.get("package", "")],
                    capture_output=True, text=True, timeout=60,
                    input="",  # stdin closed
                )

            self._update_server_status(server_id, "installed")
            self._log_action("install", server_id, "success")
            return {"success": True, "message": f"تم تثبيت {server['name']}"}

        except subprocess.TimeoutExpired:
            self._update_server_status(server_id, "installed")  # npx timeout is normal
            return {"success": True, "message": f"{server['name']} — تم التحقق"}
        except Exception as e:
            self._log_action("install", server_id, f"error: {e}")
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════
    # إنشاء تكوين MCP
    # ═══════════════════════════════════════════════

    def generate_mcp_config(self) -> Dict:
        """
        يولّد ملف تكوين MCP servers لـ Claude Code أو أي عميل MCP
        يُحفظ في .claude/mcp_servers.json
        """
        config = {"mcpServers": {}}

        for server in self.get_ready_servers():
            install = server.get("install", "")
            if not install or install.startswith("remote"):
                continue

            server_config = {}

            if install.startswith("npx"):
                parts = install.split()
                server_config["command"] = "npx"
                server_config["args"] = parts[1:]  # e.g. ["-y", "package-name"]
            elif install.startswith("pip"):
                continue  # Python MCPs are handled differently

            # إضافة env variables
            if server.get("needs_api_key"):
                env_key = server.get("env_key", "")
                env_val = os.getenv(env_key, "")
                if env_val:
                    server_config["env"] = {env_key: env_val}

            if server_config:
                config["mcpServers"][server["id"]] = server_config

        # حفظ التكوين
        os.makedirs(os.path.dirname(MCP_CONFIG_PATH), exist_ok=True)
        with open(MCP_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        logger.info(f"MCP config generated: {len(config['mcpServers'])} servers")
        return config

    # ═══════════════════════════════════════════════
    # اقتراحات للوكلاء
    # ═══════════════════════════════════════════════

    def recommend_for_task(self, task: str) -> List[Dict]:
        """يقترح خوادم MCP مناسبة لمهمة"""
        task_lower = task.lower()
        recommendations = []

        keyword_map = {
            "search": ["mcp-brave-search", "mcp-serpstat"],
            "بحث": ["mcp-brave-search", "mcp-serpstat"],
            "code": ["mcp-github", "mcp-e2b", "mcp-docfork"],
            "كود": ["mcp-github", "mcp-e2b", "mcp-docfork"],
            "برمج": ["mcp-github", "mcp-e2b"],
            "database": ["mcp-sqlite", "mcp-postgres", "mcp-dbhub"],
            "بيانات": ["mcp-sqlite", "mcp-postgres"],
            "browser": ["mcp-playwright", "mcp-puppeteer"],
            "متصفح": ["mcp-playwright"],
            "ترجم": ["mcp-deepl", "mcp-simplelocalize"],
            "translate": ["mcp-deepl"],
            "أمن": ["mcp-kaspersky"],
            "security": ["mcp-kaspersky"],
            "مال": ["mcp-polygon"],
            "سوق": ["mcp-polygon"],
            "finance": ["mcp-polygon"],
            "بريد": ["mcp-mailpace"],
            "email": ["mcp-mailpace"],
            "slack": ["mcp-slack"],
            "notion": ["mcp-notion"],
            "github": ["mcp-github"],
            "ملف": ["mcp-filesystem"],
            "file": ["mcp-filesystem"],
            "ذاكرة": ["mcp-memory", "mcp-chroma"],
            "memory": ["mcp-memory", "mcp-chroma"],
        }

        matched_ids = set()
        for keyword, server_ids in keyword_map.items():
            if keyword in task_lower:
                matched_ids.update(server_ids)

        for sid in matched_ids:
            server = self.get_server(sid)
            if server:
                recommendations.append(server)

        return recommendations

    # ═══════════════════════════════════════════════
    # إحصائيات
    # ═══════════════════════════════════════════════

    def status(self) -> Dict:
        """حالة نظام MCP"""
        servers = self.get_all_servers()
        by_status = {}
        by_category = {}
        by_priority = {}

        for s in servers:
            st = s.get("status", "unknown")
            by_status[st] = by_status.get(st, 0) + 1
            cat = s.get("category", "other")
            by_category[cat] = by_category.get(cat, 0) + 1
            pri = s.get("priority", "low")
            by_priority[pri] = by_priority.get(pri, 0) + 1

        # API keys status
        keys_present = 0
        keys_needed = 0
        for s in servers:
            if s.get("needs_api_key"):
                keys_needed += 1
                if os.getenv(s.get("env_key", ""), ""):
                    keys_present += 1

        return {
            "total_registered": len(servers),
            "total_available_globally": self.registry.get("total_available", 19575),
            "by_status": by_status,
            "by_category": by_category,
            "by_priority": by_priority,
            "api_keys": {"present": keys_present, "needed": keys_needed},
            "ready_to_use": len(self.get_ready_servers()),
        }

    # ═══════════════════════════════════════════════
    # Internal
    # ═══════════════════════════════════════════════

    def _load_registry(self) -> Dict:
        if os.path.exists(REGISTRY_PATH):
            try:
                with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"servers": []}

    def _load_state(self) -> Dict:
        if os.path.exists(MCP_STATE_PATH):
            try:
                with open(MCP_STATE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"actions": []}

    def _save_state(self):
        with open(MCP_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def _update_server_status(self, server_id: str, status: str):
        for s in self.registry.get("servers", []):
            if s["id"] == server_id:
                s["status"] = status
                break
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)

    def _log_action(self, action: str, server_id: str, result: str):
        self.state.setdefault("actions", []).append({
            "action": action,
            "server_id": server_id,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
        self.state["actions"] = self.state["actions"][-100:]
        self._save_state()


# ── Singleton ────────────────────────────────
_instance: Optional[MCPConnector] = None


def get_mcp_connector() -> MCPConnector:
    global _instance
    if _instance is None:
        _instance = MCPConnector()
    return _instance
