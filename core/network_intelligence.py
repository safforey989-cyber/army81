"""
Army81 — Network Intelligence
الذكاء الشبكي — 81 وكيل يعملون كدماغ واحد
"""
import json, logging, time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("army81.network_intelligence")
WORKSPACE = Path("workspace")
NETWORK_DIR = WORKSPACE / "network_intelligence"

class NetworkIntelligence:
    """
    يحول 81 وكيل منفصلين إلى شبكة عصبية موحدة:
    - كل وكيل = عقدة (neuron)
    - التواصل = نبضات (signals)
    - القرارات = إجماع (consensus)
    - التعلم = تقوية الروابط (Hebbian learning)
    """

    def __init__(self):
        self.connections: Dict[str, Dict[str, float]] = {}  # agent_a -> {agent_b: weight}
        self.signals: List[Dict] = []
        self.consensus_log: List[Dict] = []
        NETWORK_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        conn_file = NETWORK_DIR / "connections.json"
        if conn_file.exists():
            try:
                self.connections = json.loads(conn_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save(self):
        conn_file = NETWORK_DIR / "connections.json"
        conn_file.write_text(json.dumps(self.connections, ensure_ascii=False, indent=2), encoding="utf-8")

    def strengthen_connection(self, agent_a: str, agent_b: str, amount: float = 0.1):
        """Hebbian learning: neurons that fire together wire together"""
        if agent_a not in self.connections:
            self.connections[agent_a] = {}
        if agent_b not in self.connections:
            self.connections[agent_b] = {}

        current_ab = self.connections[agent_a].get(agent_b, 0.5)
        current_ba = self.connections[agent_b].get(agent_a, 0.5)

        self.connections[agent_a][agent_b] = min(1.0, current_ab + amount)
        self.connections[agent_b][agent_a] = min(1.0, current_ba + amount)
        self._save()

    def weaken_connection(self, agent_a: str, agent_b: str, amount: float = 0.05):
        """Weaken unused connections"""
        if agent_a in self.connections and agent_b in self.connections[agent_a]:
            self.connections[agent_a][agent_b] = max(0, self.connections[agent_a][agent_b] - amount)
        if agent_b in self.connections and agent_a in self.connections[agent_b]:
            self.connections[agent_b][agent_a] = max(0, self.connections[agent_b][agent_a] - amount)
        self._save()

    def propagate_signal(self, source: str, signal_type: str, data: Dict, strength: float = 1.0):
        """نشر إشارة من وكيل لجيرانه"""
        signal = {
            "source": source, "type": signal_type, "data": data,
            "strength": strength, "timestamp": datetime.now().isoformat(),
            "reached": [],
        }

        if source in self.connections:
            for target, weight in self.connections[source].items():
                if weight * strength > 0.3:  # threshold
                    signal["reached"].append({"target": target, "effective_strength": weight * strength})

        self.signals.append(signal)
        self.signals = self.signals[-500:]
        return signal

    def find_best_team(self, task_type: str, team_size: int = 4) -> List[str]:
        """يجد أفضل فريق لمهمة بناءً على قوة الروابط"""
        # Specialists for this task type
        specialists = {
            "coding": ["A05", "A57", "A09", "A51", "A74"],
            "medical": ["A07", "A52", "A38", "A61"],
            "financial": ["A08", "A41", "A42", "A34"],
            "strategy": ["A01", "A28", "A29", "A33", "A34"],
            "research": ["A02", "A06", "A10", "A38"],
            "security": ["A09", "A31", "A71"],
            "creative": ["A12", "A46", "A30"],
        }

        candidates = specialists.get(task_type, ["A01", "A02", "A05", "A10"])

        # Sort by connection strength with each other
        scored = []
        for agent in candidates:
            total_connection = sum(
                self.connections.get(agent, {}).get(other, 0)
                for other in candidates if other != agent
            )
            scored.append((agent, total_connection))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored[:team_size]]

    def reach_consensus(self, question: str, voters: List[str], opinions: Dict[str, str]) -> Dict:
        """إجماع — التصويت المرجّح بالروابط"""
        weighted_opinions = {}

        for voter, opinion in opinions.items():
            # Weight = average connection strength with other voters
            weight = 1.0
            if voter in self.connections:
                weights = [self.connections[voter].get(v, 0.5) for v in voters if v != voter]
                weight = sum(weights) / max(len(weights), 1)
            weighted_opinions[voter] = {"opinion": opinion, "weight": weight}

        consensus = {
            "question": question[:200],
            "voters": voters,
            "weighted_opinions": weighted_opinions,
            "timestamp": datetime.now().isoformat(),
        }

        self.consensus_log.append(consensus)
        self.consensus_log = self.consensus_log[-100:]

        return consensus

    def get_network_health(self) -> Dict:
        total_connections = sum(len(v) for v in self.connections.values())
        avg_weight = 0
        weights = []
        for targets in self.connections.values():
            weights.extend(targets.values())
        if weights:
            avg_weight = sum(weights) / len(weights)

        return {
            "nodes": len(self.connections),
            "total_connections": total_connections,
            "avg_connection_weight": round(avg_weight, 3),
            "signals_processed": len(self.signals),
            "consensus_reached": len(self.consensus_log),
            "strongest_bonds": self._get_strongest_bonds(5),
        }

    def _get_strongest_bonds(self, k: int = 5) -> List[Dict]:
        bonds = []
        seen = set()
        for a, targets in self.connections.items():
            for b, weight in targets.items():
                pair = tuple(sorted([a, b]))
                if pair not in seen:
                    seen.add(pair)
                    bonds.append({"agents": list(pair), "weight": weight})
        return sorted(bonds, key=lambda x: x["weight"], reverse=True)[:k]

    def daily_maintenance(self):
        """صيانة يومية — إضعاف الروابط غير المستخدمة"""
        for agent, targets in self.connections.items():
            for target in list(targets.keys()):
                targets[target] = max(0.1, targets[target] * 0.98)  # 2% decay
        self._save()
        logger.info("Network maintenance: connection weights decayed 2%")

    def get_stats(self) -> Dict:
        return self.get_network_health()
