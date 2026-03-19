"""
Army81 Voice Interface — التواصل الصوتي مع القائد
يستخدم: ElevenLabs (TTS) + OpenRouter/MiniMax (TTS بديل) + Whisper (STT)
"""
import os
import io
import json
import time
import wave
import logging
import tempfile
import threading
import requests
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("army81.voice")

# ─── تحميل المفاتيح ───
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY", "")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8181")

# ─── ElevenLabs TTS ───
class ElevenLabsTTS:
    """تحويل النص إلى صوت عبر ElevenLabs"""
    BASE = "https://api.elevenlabs.io/v1"

    def __init__(self):
        self.key = ELEVENLABS_KEY
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - صوت واضح
        self.model = "eleven_multilingual_v2"  # يدعم العربية

    def list_voices(self):
        """قائمة الأصوات المتاحة"""
        try:
            r = requests.get(f"{self.BASE}/voices",
                           headers={"xi-api-key": self.key}, timeout=10)
            if r.ok:
                voices = r.json().get("voices", [])
                return [{"id": v["voice_id"], "name": v["name"]} for v in voices[:10]]
        except:
            pass
        return []

    def speak(self, text: str, output_path: str = None) -> str:
        """تحويل نص إلى ملف صوتي MP3"""
        if not self.key:
            logger.warning("ElevenLabs key missing")
            return ""

        try:
            r = requests.post(
                f"{self.BASE}/text-to-speech/{self.voice_id}",
                headers={
                    "xi-api-key": self.key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text[:5000],
                    "model_id": self.model,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.3
                    }
                },
                timeout=30
            )

            if r.ok:
                if not output_path:
                    output_path = os.path.join(
                        tempfile.gettempdir(),
                        f"army81_voice_{int(time.time())}.mp3"
                    )
                with open(output_path, "wb") as f:
                    f.write(r.content)
                logger.info(f"🔊 Voice generated: {output_path} ({len(r.content)} bytes)")
                return output_path
            else:
                logger.warning(f"ElevenLabs error {r.status_code}: {r.text[:200]}")
        except Exception as e:
            logger.warning(f"ElevenLabs TTS failed: {e}")
        return ""


# ─── MiniMax TTS (عبر OpenRouter) ───
class MiniMaxTTS:
    """تحويل نص لصوت عبر MiniMax من OpenRouter"""

    def __init__(self):
        self.key = OPENROUTER_KEY

    def speak(self, text: str) -> str:
        """يولّد صوت باستخدام minimax عبر OpenRouter"""
        # MiniMax لا يدعم TTS مباشر عبر OpenRouter
        # نستخدمه كـ fallback للنص الذكي
        return ""


# ─── Whisper STT (تحويل صوت لنص) ───
class WhisperSTT:
    """تحويل الصوت إلى نص — Whisper عبر Google/OpenRouter"""

    def __init__(self):
        self.google_key = GOOGLE_KEY

    def transcribe_file(self, audio_path: str) -> str:
        """تحويل ملف صوتي إلى نص"""
        # استخدام Gemini للتعرف على الصوت
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.google_key)
            model = genai.GenerativeModel("gemini-2.0-flash")

            with open(audio_path, "rb") as f:
                audio_data = f.read()

            response = model.generate_content([
                "حوّل هذا الصوت إلى نص بالعربية. أعد النص فقط بدون أي إضافات.",
                {"mime_type": "audio/mp3", "data": audio_data}
            ])
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Whisper/Gemini STT failed: {e}")
        return ""


# ─── Voice Commander ───
class VoiceCommander:
    """
    القائد يتحدث ← النظام يسمع ← يرد صوتياً
    """

    def __init__(self):
        self.tts = ElevenLabsTTS()
        self.stt = WhisperSTT()
        self.minimax = MiniMaxTTS()
        self.conversation_history = []
        self.is_listening = False

        logger.info("🎙️ VoiceCommander initialized")
        logger.info(f"   ElevenLabs: {'✅' if ELEVENLABS_KEY else '❌'}")
        logger.info(f"   Google STT: {'✅' if GOOGLE_KEY else '❌'}")

    def process_text_to_voice(self, text: str) -> dict:
        """حوّل نص إلى صوت وأعد المسار"""
        audio_path = self.tts.speak(text)

        return {
            "text": text,
            "audio_path": audio_path,
            "audio_available": bool(audio_path),
            "timestamp": datetime.now().isoformat()
        }

    def process_voice_to_text(self, audio_path: str) -> str:
        """حوّل صوت إلى نص"""
        return self.stt.transcribe_file(audio_path)

    def ask_agent(self, text: str, agent_id: str = None) -> dict:
        """أرسل سؤال للوكيل واحصل على رد صوتي"""
        # 1. أرسل للـ gateway
        try:
            payload = {"task": text}
            if agent_id:
                payload["preferred_agent"] = agent_id

            r = requests.post(f"{GATEWAY_URL}/task", json=payload, timeout=120)
            result = r.json()

            agent_name = result.get("agent_name", "وكيل")
            response_text = result.get("result", "لم أستطع المعالجة")

            # 2. حوّل الرد لصوت
            # اقتطع لأول 500 حرف للسرعة
            voice_text = f"{agent_name} يقول: {response_text[:500]}"
            audio_path = self.tts.speak(voice_text)

            entry = {
                "role": "user",
                "text": text,
                "agent": agent_id or "auto",
                "response": response_text,
                "agent_name": agent_name,
                "audio_path": audio_path,
                "timestamp": datetime.now().isoformat()
            }
            self.conversation_history.append(entry)

            return entry

        except Exception as e:
            logger.error(f"Voice ask failed: {e}")
            return {"error": str(e)}

    def generate_morning_report_voice(self) -> dict:
        """يولّد تقرير صباحي صوتي"""
        try:
            # جلب حالة النظام
            r = requests.get(f"{GATEWAY_URL}/status", timeout=10)
            status = r.json()

            # جلب إحصائيات الذاكرة
            r2 = requests.get(f"{GATEWAY_URL}/memory/stats", timeout=10)
            mem = r2.json()

            # جلب التطور
            r3 = requests.get(f"{GATEWAY_URL}/evolution/stats", timeout=10)
            evo = r3.json()

            agents = status.get("agents_count", 81)
            episodes = mem.get("episodic", {}).get("episodes", 0)
            experiments = evo.get("components", {}).get("auto_research", {}).get("total_experiments", 0)

            report_text = f"""
            صباح الخير سيدي. هذا تقرير Army81 اليومي.
            النظام يعمل بكامل طاقته. {agents} وكيل نشط.
            أنجزنا {episodes} حلقة تعلم و {experiments} تجربة.
            الذاكرة تنمو والتطور مستمر.
            هل تريد تفعيل دورة تطور جديدة؟
            """

            audio_path = self.tts.speak(report_text.strip())

            return {
                "type": "morning_report",
                "text": report_text.strip(),
                "audio_path": audio_path,
                "agents": agents,
                "episodes": episodes,
                "experiments": experiments
            }
        except Exception as e:
            return {"error": str(e)}

    def send_voice_to_telegram(self, audio_path: str, caption: str = ""):
        """أرسل ملف صوتي عبر Telegram"""
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        if not token or not chat_id:
            return False

        try:
            with open(audio_path, "rb") as f:
                r = requests.post(
                    f"https://api.telegram.org/bot{token}/sendVoice",
                    data={"chat_id": chat_id, "caption": caption[:200]},
                    files={"voice": f},
                    timeout=30
                )
            return r.ok
        except:
            return False


# ─── FastAPI endpoints for voice ───
def register_voice_endpoints(app):
    """أضف endpoints الصوت لـ gateway"""
    from fastapi import Request
    from fastapi.responses import FileResponse

    vc = VoiceCommander()

    @app.post("/voice/speak")
    async def voice_speak(request: Request):
        """حوّل نص إلى صوت"""
        data = await request.json()
        text = data.get("text", "")
        result = vc.process_text_to_voice(text)
        return result

    @app.post("/voice/ask")
    async def voice_ask(request: Request):
        """اسأل وكيل واحصل على رد صوتي"""
        data = await request.json()
        text = data.get("text", "")
        agent_id = data.get("agent_id")
        result = vc.ask_agent(text, agent_id)
        return result

    @app.get("/voice/audio/{filename}")
    async def get_audio(filename: str):
        """حمّل ملف صوتي"""
        path = os.path.join(tempfile.gettempdir(), filename)
        if os.path.exists(path):
            return FileResponse(path, media_type="audio/mpeg")
        return {"error": "file not found"}

    @app.post("/voice/morning-report")
    async def morning_report():
        """تقرير صباحي صوتي"""
        result = vc.generate_morning_report_voice()
        # أرسل لـ Telegram
        if result.get("audio_path"):
            vc.send_voice_to_telegram(
                result["audio_path"],
                f"📊 تقرير صباحي — {result.get('agents',81)} وكيل"
            )
        return result

    @app.get("/voice/history")
    async def voice_history():
        """سجل المحادثات الصوتية"""
        return {"history": vc.conversation_history[-20:]}

    @app.get("/voice/status")
    async def voice_status():
        """حالة نظام الصوت"""
        return {
            "elevenlabs": bool(ELEVENLABS_KEY),
            "google_stt": bool(GOOGLE_KEY),
            "openrouter": bool(OPENROUTER_KEY),
            "conversations": len(vc.conversation_history)
        }

    logger.info("🎙️ Voice endpoints registered: /voice/speak, /voice/ask, /voice/morning-report")
    return vc


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vc = VoiceCommander()

    # اختبار
    print("🎙️ Testing Voice Interface...")
    result = vc.process_text_to_voice("مرحباً سيدي. Army81 جاهز للعمل.")
    if result["audio_available"]:
        print(f"✅ Audio: {result['audio_path']}")
    else:
        print("❌ Audio generation failed")
