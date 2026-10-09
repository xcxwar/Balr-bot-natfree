from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any

import httpx

# ============================================================
# چت جی پی تی | ChatGPT — Pydroid 3 / Polling
# ============================================================
# All credentials are supplied only through environment variables.

BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "").strip()
BOT_NAME = os.getenv("BOT_NAME", "چت جی پی تی | ChatGPT")
ADMIN_ID = os.getenv("ADMIN_ID", "955311935").strip()

OWEN_DISABLED_MESSAGE = (
    "این سرویس در حال حاضر غیرفعال است. "
    "لطفاً از یکی دیگر از مدل‌های هوش مصنوعی استفاده کنید."
)

GAPGPT_API_KEY = os.getenv("GAPGPT_API_KEY", "").strip()
GAPGPT_BASE_URL = os.getenv(
    "GAPGPT_BASE_URL", "https://api.gapgpt.app/v1"
).strip()
GAPGPT_MODEL = os.getenv("GAPGPT_MODEL", "").strip()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
).strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "").strip()

AI_PROFILES = {
    1: {
        "name": "ChatGPT",
        "key": GAPGPT_API_KEY,
        "base": GAPGPT_BASE_URL,
        "model": GAPGPT_MODEL,
        "enabled": True,
    },
    2: {
        "name": "OWEN",
        "key": "",
        "base": "",
        "model": "",
        "enabled": False,
    },
    3: {
        "name": "Gemini",
        "key": OPENROUTER_API_KEY,
        "base": OPENROUTER_BASE_URL,
        "model": OPENROUTER_MODEL,
        "enabled": True,
    },
}

BALE_API = os.getenv(
    "BALE_API_BASE", "https://tapi.bale.ai/bot"
)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()

DB_PATH = os.getenv(
    "SQLITE_PATH",
    "/var/data/bot.sqlite3" if os.getenv("RENDER") else "bot.sqlite3",
)

MAX_INPUT = int(os.getenv("MAX_INPUT_CHARS", "8000"))

RATE_LIMITS = {
    1: (4, 6 * 60 * 60),
    2: (2, 4 * 60 * 60),
    3: (3, 6 * 60 * 60),
}

MEMORY_TTL = 86400

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("bale-bot")

LANGS = {
    "fa": "🇮🇷 فارسی",
    "en": "🇬🇧 English",
    "ar": "🇸🇦 العربية",
    "es": "🇪🇸 Español",
    "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch",
    "ru": "🇷🇺 Русский",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
    "hi": "🇮🇳 हिन्दी",
}

# Compact built-in localization.
T: dict[str, dict[str, str]] = {
    "fa": {
        "choose": "🌍 لطفاً زبان چت را انتخاب کنید",
        "welcome": "🤖 به دستیار هوشمند خوش آمدید!\n\nمن {name} هستم؛ یک دستیار هوش مصنوعی چندمنظوره برای گفتگو، ترجمه، تصویر، ویدیو، صدا، آب‌وهوا و اخبار.\n\n🚀 آماده‌ام! یکی از گزینه‌های زیر را انتخاب کنید.",
        "ai": "🤖 هوش مصنوعی",
        "image": "🎨 ساخت تصویر",
        "video": "🎬 ساخت ویدیو",
        "voice": "🎙️ ساخت صدا",
        "translate": "🌍 ترجمه",
        "weather": "🌤️ آب‌وهوا",
        "news": "📰 اخبار",
        "memory": "🧠 حافظه",
        "settings": "⚙️ تنظیمات",
        "about": "ℹ️ درباره ربات",
        "language": "🌐 تغییر زبان",
        "back": "🔙 بازگشت",
        "ai_select": "🤖 هوش مصنوعی موردنظر را انتخاب کنید",
        "ai_selected": "✅ هوش مصنوعی {n} انتخاب شد.",
        "prompt": "📝 توضیح موردنظر را ارسال کنید.",
        "text": "📝 متن موردنظر را ارسال کنید.",
        "thinking": "⏳ در حال فکر کردن...",
        "processing": "⏳ در حال پردازش...",
        "done": "✅ انجام شد!",
        "error": "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.",
        "rate": "⛔ محدودیت مصرف: در هر ۲ ساعت فقط ۵ پیام مجاز است.",
        "invalid": "❌ ورودی نامعتبر یا بیش از حد طولانی است.",
        "memory_status": "🧠 مدیریت حافظه",
        "memory_empty": "حافظه فعالی وجود ندارد.",
        "memory_count": "تعداد پیام‌های حافظه: {n}",
        "memory_clear": "🗑️ پاک کردن حافظه",
        "memory_cleared": "✅ حافظه شما پاک شد.",
        "memory_info": "ℹ️ حافظه فقط ۲۴ ساعت نگهداری می‌شود.",
        "settings_text": "⚙️ تنظیمات",
        "notify": "🔔 اعلان‌ها",
        "notify_on": "🔔 اعلان‌ها فعال شد.",
        "notify_off": "🔕 اعلان‌ها غیرفعال شد.",
        "about_text": "🤖 {name}\n\nدستیار چندمنظوره هوش مصنوعی برای پیام‌رسان بله.",
        "weather_city": "🏙️ نام شهر را ارسال کنید.",
        "weather_result": "🌤️ {city}\n\n🌡️ دما: {temp}°C\n💨 باد: {wind} km/h\n💧 رطوبت: {humidity}%\n☁️ وضعیت: {condition}",
        "weather_error": "❌ دریافت آب‌وهوا ناموفق بود.",
        "news_cat": "📰 دسته اخبار را انتخاب کنید.",
        "general": "📰 عمومی",
        "technology": "💻 تکنولوژی",
        "ai_news": "🤖 هوش مصنوعی",
        "sports": "⚽ ورزش",
        "world": "🌍 جهان",
        "news_error": "❌ دریافت اخبار ناموفق بود.",
        "target": "🌍 زبان مقصد را انتخاب کنید.",
        "translation_error": "❌ ترجمه ناموفق بود.",
    },
    "en": {
        "choose": "🌍 Please choose the chat language",
        "welcome": "🤖 Welcome to the smart assistant!\n\nI am {name}, a multilingual AI assistant for chat, translation, images, video, voice, weather and news.\n\n🚀 Ready! Choose an option below.",
        "ai": "🤖 AI",
        "image": "🎨 Image",
        "video": "🎬 Video",
        "voice": "🎙️ Voice",
        "translate": "🌍 Translate",
        "weather": "🌤️ Weather",
        "news": "📰 News",
        "memory": "🧠 Memory",
        "settings": "⚙️ Settings",
        "about": "ℹ️ About",
        "language": "🌐 Change language",
        "back": "🔙 Back",
        "ai_select": "🤖 Choose an AI model",
        "ai_selected": "✅ AI {n} selected.",
        "prompt": "📝 Send your prompt.",
        "text": "📝 Send the text.",
        "thinking": "⏳ Thinking...",
        "processing": "⏳ Processing...",
        "done": "✅ Done!",
        "error": "❌ Something went wrong. Please try again.",
        "rate": "⛔ Limit: only 5 messages every 2 hours.",
        "invalid": "❌ Invalid or too-long input.",
        "memory_status": "🧠 Memory management",
        "memory_empty": "No active memory.",
        "memory_count": "Memory messages: {n}",
        "memory_clear": "🗑️ Clear memory",
        "memory_cleared": "✅ Memory cleared.",
        "memory_info": "ℹ️ Memory is kept for 24 hours.",
        "settings_text": "⚙️ Settings",
        "notify": "🔔 Notifications",
        "notify_on": "🔔 Notifications enabled.",
        "notify_off": "🔕 Notifications disabled.",
        "about_text": "🤖 {name}\n\nMultifunctional AI assistant for Bale.",
        "weather_city": "🏙️ Send a city name.",
        "weather_result": "🌤️ {city}\n\n🌡️ Temperature: {temp}°C\n💨 Wind: {wind} km/h\n💧 Humidity: {humidity}%\n☁️ Condition: {condition}",
        "weather_error": "❌ Could not get weather.",
        "news_cat": "📰 Choose a news category.",
        "general": "📰 General",
        "technology": "💻 Technology",
        "ai_news": "🤖 AI",
        "sports": "⚽ Sports",
        "world": "🌍 World",
        "news_error": "❌ Could not get news.",
        "target": "🌍 Choose target language.",
        "translation_error": "❌ Translation failed.",
    },
}

# UI translations for the other supported languages.
_TRANSLATIONS = {
    "ar": {
        "choose": "🌍 اختر لغة المحادثة",
        "welcome": "🤖 أهلاً بك في المساعد الذكي!\n\nأنا {name}، مساعد ذكاء اصطناعي متعدد الاستخدامات.",
        "ai": "🤖 الذكاء الاصطناعي",
        "image": "🎨 إنشاء صورة",
        "video": "🎬 إنشاء فيديو",
        "voice": "🎙️ إنشاء صوت",
        "translate": "🌍 ترجمة",
        "weather": "🌤️ الطقس",
        "news": "📰 الأخبار",
        "memory": "🧠 الذاكرة",
        "settings": "⚙️ الإعدادات",
        "about": "ℹ️ حول البوت",
        "language": "🌐 تغيير اللغة",
        "back": "🔙 رجوع",
        "prompt": "📝 أرسل وصفك.",
        "text": "📝 أرسل النص.",
        "thinking": "⏳ جارٍ التفكير...",
        "processing": "⏳ جارٍ المعالجة...",
        "error": "❌ حدث خطأ. حاول مجدداً.",
        "rate": "⛔ الحد: 5 رسائل كل ساعتين.",
        "weather_city": "🏙️ أرسل اسم المدينة.",
        "weather_error": "❌ تعذر جلب الطقس.",
        "news_cat": "📰 اختر فئة الأخبار.",
        "general": "📰 عام",
        "technology": "💻 التقنية",
        "ai_news": "🤖 الذكاء الاصطناعي",
        "sports": "⚽ الرياضة",
        "world": "🌍 العالم",
        "target": "🌍 اختر اللغة المستهدفة.",
        "translation_error": "❌ فشلت الترجمة.",
    },
    "es": {
        "choose": "🌍 Elige el idioma del chat",
        "welcome": "🤖 ¡Bienvenido al asistente inteligente!\n\nSoy {name}, un asistente de IA multilingüe.",
        "ai": "🤖 IA",
        "image": "🎨 Crear imagen",
        "video": "🎬 Crear vídeo",
        "voice": "🎙️ Crear voz",
        "translate": "🌍 Traducir",
        "weather": "🌤️ Tiempo",
        "news": "📰 Noticias",
        "memory": "🧠 Memoria",
        "settings": "⚙️ Ajustes",
        "about": "ℹ️ Acerca de",
        "language": "🌐 Cambiar idioma",
        "back": "🔙 Volver",
        "prompt": "📝 Envía tu descripción.",
        "text": "📝 Envía el texto.",
        "thinking": "⏳ Pensando...",
        "processing": "⏳ Procesando...",
        "error": "❌ Ocurrió un error. Inténtalo de nuevo.",
        "rate": "⛔ Límite: 5 mensajes cada 2 horas.",
        "weather_city": "🏙️ Envía el nombre de una ciudad.",
        "weather_error": "❌ No se pudo obtener el tiempo.",
        "news_cat": "📰 Elige una categoría de noticias.",
        "general": "📰 General",
        "technology": "💻 Tecnología",
        "ai_news": "🤖 IA",
        "sports": "⚽ Deportes",
        "world": "🌍 Mundo",
        "target": "🌍 Elige el idioma de destino.",
        "translation_error": "❌ Falló la traducción.",
    },
    "fr": {
        "choose": "🌍 Choisissez la langue du chat",
        "welcome": "🤖 Bienvenue dans l’assistant intelligent !\n\nJe suis {name}, un assistant IA multilingue.",
        "ai": "🤖 IA",
        "image": "🎨 Créer une image",
        "video": "🎬 Créer une vidéo",
        "voice": "🎙️ Créer une voix",
        "translate": "🌍 Traduire",
        "weather": "🌤️ Météo",
        "news": "📰 Actualités",
        "memory": "🧠 Mémoire",
        "settings": "⚙️ Paramètres",
        "about": "ℹ️ À propos",
        "language": "🌐 Changer de langue",
        "back": "🔙 Retour",
        "prompt": "📝 Envoyez votre description.",
        "text": "📝 Envoyez le texte.",
        "thinking": "⏳ Réflexion...",
        "processing": "⏳ Traitement...",
        "error": "❌ Une erreur s’est produite. Réessayez.",
        "rate": "⛔ Limite : 5 messages toutes les 2 heures.",
        "weather_city": "🏙️ Envoyez le nom d’une ville.",
        "weather_error": "❌ Météo indisponible.",
        "news_cat": "📰 Choisissez une catégorie d’actualités.",
        "general": "📰 Général",
        "technology": "💻 Technologie",
        "ai_news": "🤖 IA",
        "sports": "⚽ Sports",
        "world": "🌍 Monde",
        "target": "🌍 Choisissez la langue cible.",
        "translation_error": "❌ Échec de la traduction.",
    },
    "de": {
        "choose": "🌍 Bitte Chatsprache wählen",
        "welcome": "🤖 Willkommen beim intelligenten Assistenten!\n\nIch bin {name}, ein mehrsprachiger KI-Assistent.",
        "ai": "🤖 KI",
        "image": "🎨 Bild erstellen",
        "video": "🎬 Video erstellen",
        "voice": "🎙️ Stimme erstellen",
        "translate": "🌍 Übersetzen",
        "weather": "🌤️ Wetter",
        "news": "📰 Nachrichten",
        "memory": "🧠 Speicher",
        "settings": "⚙️ Einstellungen",
        "about": "ℹ️ Über den Bot",
        "language": "🌐 Sprache ändern",
        "back": "🔙 Zurück",
        "prompt": "📝 Bitte Beschreibung senden.",
        "text": "📝 Bitte Text senden.",
        "thinking": "⏳ Denke nach...",
        "processing": "⏳ Verarbeitung...",
        "error": "❌ Fehler aufgetreten. Bitte erneut versuchen.",
        "rate": "⛔ Limit: 5 Nachrichten alle 2 Stunden.",
        "weather_city": "🏙️ Stadtnamen senden.",
        "weather_error": "❌ Wetter konnte nicht geladen werden.",
        "news_cat": "📰 Nachrichtenkategorie wählen.",
        "general": "📰 Allgemein",
        "technology": "💻 Technik",
        "ai_news": "🤖 KI",
        "sports": "⚽ Sport",
        "world": "🌍 Welt",
        "target": "🌍 Zielsprache wählen.",
        "translation_error": "❌ Übersetzung fehlgeschlagen.",
    },
    "ru": {
        "choose": "🌍 Выберите язык чата",
        "welcome": "🤖 Добро пожаловать в умного помощника!\n\nЯ — {name}, многоязычный ИИ-помощник.",
        "ai": "🤖 ИИ",
        "image": "🎨 Создать изображение",
        "video": "🎬 Создать видео",
        "voice": "🎙️ Создать голос",
        "translate": "🌍 Перевести",
        "weather": "🌤️ Погода",
        "news": "📰 Новости",
        "memory": "🧠 Память",
        "settings": "⚙️ Настройки",
        "about": "ℹ️ О боте",
        "language": "🌐 Сменить язык",
        "back": "🔙 Назад",
        "prompt": "📝 Отправьте описание.",
        "text": "📝 Отправьте текст.",
        "thinking": "⏳ Думаю...",
        "processing": "⏳ Обработка...",
        "error": "❌ Ошибка. Попробуйте ещё раз.",
        "rate": "⛔ Лимит: 5 сообщений за 2 часа.",
        "weather_city": "🏙️ Отправьте название города.",
        "weather_error": "❌ Не удалось получить погоду.",
        "news_cat": "📰 Выберите категорию новостей.",
        "general": "📰 Общее",
        "technology": "💻 Технологии",
        "ai_news": "🤖 ИИ",
        "sports": "⚽ Спорт",
        "world": "🌍 Мир",
        "target": "🌍 Выберите язык перевода.",
        "translation_error": "❌ Перевод не удался.",
    },
    "zh": {
        "choose": "🌍 请选择聊天语言",
        "welcome": "🤖 欢迎使用智能助手！\n\n我是 {name}，多语言人工智能助手。",
        "ai": "🤖 人工智能",
        "image": "🎨 生成图片",
        "video": "🎬 生成视频",
        "voice": "🎙️ 生成语音",
        "translate": "🌍 翻译",
        "weather": "🌤️ 天气",
        "news": "📰 新闻",
        "memory": "🧠 记忆",
        "settings": "⚙️ 设置",
        "about": "ℹ️ 关于",
        "language": "🌐 更改语言",
        "back": "🔙 返回",
        "prompt": "📝 请发送描述。",
        "text": "📝 请发送文本。",
        "thinking": "⏳ 思考中...",
        "processing": "⏳ 处理中...",
        "error": "❌ 出错了，请重试。",
        "rate": "⛔ 限制：每两小时最多5条消息。",
        "weather_city": "🏙️ 请发送城市名称。",
        "weather_error": "❌ 无法获取天气。",
        "news_cat": "📰 请选择新闻类别。",
        "general": "📰 综合",
        "technology": "💻 科技",
        "ai_news": "🤖 人工智能",
        "sports": "⚽ 体育",
        "world": "🌍 国际",
        "target": "🌍 请选择目标语言。",
        "translation_error": "❌ 翻译失败。",
    },
    "ja": {
        "choose": "🌍 チャットの言語を選択してください",
        "welcome": "🤖 スマートアシスタントへようこそ！\n\n私は{name}、多言語AIアシスタントです。",
        "ai": "🤖 AI",
        "image": "🎨 画像生成",
        "video": "🎬 動画生成",
        "voice": "🎙️ 音声生成",
        "translate": "🌍 翻訳",
        "weather": "🌤️ 天気",
        "news": "📰 ニュース",
        "memory": "🧠 メモリ",
        "settings": "⚙️ 設定",
        "about": "ℹ️ このボットについて",
        "language": "🌐 言語変更",
        "back": "🔙 戻る",
        "prompt": "📝 説明を送信してください。",
        "text": "📝 テキストを送信してください。",
        "thinking": "⏳ 考えています...",
        "processing": "⏳ 処理中...",
        "error": "❌ エラーが発生しました。もう一度お試しください。",
        "rate": "⛔ 2時間あたり5メッセージまでです。",
        "weather_city": "🏙️ 都市名を送信してください。",
        "weather_error": "❌ 天気を取得できませんでした。",
        "news_cat": "📰 ニュースのカテゴリを選択してください。",
        "general": "📰 総合",
        "technology": "💻 テクノロジー",
        "ai_news": "🤖 AI",
        "sports": "⚽ スポーツ",
        "world": "🌍 世界",
        "target": "🌍 翻訳先の言語を選択してください。",
        "translation_error": "❌ 翻訳に失敗しました。",
    },
    "hi": {
        "choose": "🌍 चैट की भाषा चुनें",
        "welcome": "🤖 स्मार्ट सहायक में आपका स्वागत है!\n\nमैं {name}, एक बहुभाषी AI सहायक हूँ।",
        "ai": "🤖 AI",
        "image": "🎨 चित्र बनाएँ",
        "video": "🎬 वीडियो बनाएँ",
        "voice": "🎙️ आवाज़ बनाएँ",
        "translate": "🌍 अनुवाद",
        "weather": "🌤️ मौसम",
        "news": "📰 समाचार",
        "memory": "🧠 मेमोरी",
        "settings": "⚙️ सेटिंग्स",
        "about": "ℹ️ जानकारी",
        "language": "🌐 भाषा बदलें",
        "back": "🔙 वापस",
        "prompt": "📝 अपना विवरण भेजें।",
        "text": "📝 पाठ भेजें।",
        "thinking": "⏳ सोच रहा हूँ...",
        "processing": "⏳ प्रक्रिया जारी है...",
        "error": "❌ त्रुटि हुई। फिर कोशिश करें।",
        "rate": "⛔ सीमा: हर 2 घंटे में 5 संदेश।",
        "weather_city": "🏙️ शहर का नाम भेजें।",
        "weather_error": "❌ मौसम नहीं मिल सका।",
        "news_cat": "📰 समाचार श्रेणी चुनें।",
        "general": "📰 सामान्य",
        "technology": "💻 तकनीक",
        "ai_news": "🤖 AI",
        "sports": "⚽ खेल",
        "world": "🌍 दुनिया",
        "target": "🌍 लक्ष्य भाषा चुनें।",
        "translation_error": "❌ अनुवाद विफल हुआ।",
    },
}

for _code, _strings in _TRANSLATIONS.items():
    T[_code] = {**T["en"], **_strings}

for _code in LANGS:
    T.setdefault(_code, T["en"].copy())


def tr(lang: str, key: str, **kw: Any) -> str:
    return T.get(lang, T["en"]).get(
        key, T["en"].get(key, key)
    ).format(**kw)


def is_admin_user(user_id: Any) -> bool:
    """Admin exemption is based only on the configured numeric user ID."""
    return str(user_id) == ADMIN_ID


def inline(rows):
    return {"inline_keyboard": rows}


def btn(text, data):
    return {"text": text, "callback_data": data}


def lang_kb():
    items = list(LANGS.items())
    rows = []

    for i in range(0, len(items), 2):
        row = [btn(items[i][1], f"lang:{items[i][0]}")]

        if i + 1 < len(items):
            row.append(btn(items[i + 1][1], f"lang:{items[i + 1][0]}"))

        rows.append(row)

    return inline(rows)


def main_kb(lang):
    return inline([
        [btn(tr(lang, "ai"), "menu:ai"),
         btn(tr(lang, "image"), "menu:image")],
        [btn(tr(lang, "video"), "menu:video"),
         btn(tr(lang, "voice"), "menu:voice")],
        [btn(tr(lang, "translate"), "menu:translate"),
         btn(tr(lang, "weather"), "menu:weather")],
        [btn(tr(lang, "news"), "menu:news"),
         btn(tr(lang, "memory"), "menu:memory")],
        [btn(tr(lang, "settings"), "menu:settings"),
         btn(tr(lang, "about"), "menu:about")],
    ])


def back_kb(lang):
    return inline([[btn(tr(lang, "back"), "menu:main")]])


def ai_kb(lang):
    return inline([
        [
            btn(f"🧠 1 {AI_PROFILES[1]['name']}", "ai:1"),
            btn(f"🧠 2 {AI_PROFILES[2]['name']}", "ai:2"),
        ],
        [btn(f"🧠 3 {AI_PROFILES[3]['name']}", "ai:3")],
        [btn(tr(lang, "back"), "menu:main")],
    ])


def settings_kb(lang):
    return inline([
        [btn(tr(lang, "language"), "settings:language"),
         btn(tr(lang, "ai"), "menu:ai")],
        [btn(tr(lang, "memory"), "menu:memory"),
         btn(tr(lang, "notify"), "settings:notify")],
        [btn(tr(lang, "about"), "menu:about")],
        [btn(tr(lang, "back"), "menu:main")],
    ])


def memory_kb(lang):
    return inline([
        [btn(tr(lang, "memory_status"), "memory:status")],
        [btn(tr(lang, "memory_clear"), "memory:clear"),
         btn(tr(lang, "memory_info"), "memory:info")],
        [btn(tr(lang, "back"), "menu:main")],
    ])


def translate_kb(lang):
    items = list(LANGS.items())
    rows = []

    for i in range(0, len(items), 2):
        row = [btn(items[i][1], f"target:{items[i][0]}")]

        if i + 1 < len(items):
            row.append(btn(items[i + 1][1], f"target:{items[i + 1][0]}"))

        rows.append(row)

    rows.append([btn(tr(lang, "back"), "menu:main")])
    return inline(rows)


def news_kb(lang):
    return inline([
        [btn(tr(lang, "general"), "news:general"),
         btn(tr(lang, "technology"), "news:technology")],
        [btn(tr(lang, "ai_news"), "news:ai"),
         btn(tr(lang, "sports"), "news:sports")],
        [btn(tr(lang, "world"), "news:world")],
        [btn(tr(lang, "back"), "menu:main")],
    ])


class DB:
    def __init__(self, path):
        self.path = path
        self.lock = asyncio.Lock()
        self.init()

    def conn(self):
        c = sqlite3.connect(self.path, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def init(self):
        with self.conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS users(
                user_id TEXT PRIMARY KEY,
                language TEXT,
                selected_ai INTEGER DEFAULT 1,
                created_at REAL,
                last_activity REAL,
                notifications INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS memory(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                content TEXT,
                created_at REAL
            );

            CREATE TABLE IF NOT EXISTS usage(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                profile_id INTEGER NOT NULL DEFAULT 1,
                created_at REAL
            );

            CREATE TABLE IF NOT EXISTS bot_runtime(
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """)

            columns = {
                row["name"]
                for row in c.execute("PRAGMA table_info(usage)").fetchall()
            }

            if "profile_id" not in columns:
                c.execute(
                    "ALTER TABLE usage ADD COLUMN "
                    "profile_id INTEGER NOT NULL DEFAULT 1"
                )

    def set_last_chat(self, chat_id):
        with self.conn() as c:
            c.execute(
                "INSERT INTO bot_runtime(key, value) "
                "VALUES('last_chat', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(chat_id),),
            )

    def get_last_chat(self):
        with self.conn() as c:
            row = c.execute(
                "SELECT value FROM bot_runtime WHERE key='last_chat'"
            ).fetchone()

            return row["value"] if row else None

    def user(self, uid):
        now = time.time()

        with self.conn() as c:
            r = c.execute(
                "SELECT * FROM users WHERE user_id=?",
                (uid,),
            ).fetchone()

            if not r:
                c.execute(
                    "INSERT INTO users(user_id,created_at,last_activity) "
                    "VALUES(?,?,?)",
                    (uid, now, now),
                )
                r = c.execute(
                    "SELECT * FROM users WHERE user_id=?",
                    (uid,),
                ).fetchone()
            else:
                c.execute(
                    "UPDATE users SET last_activity=? WHERE user_id=?",
                    (now, uid),
                )

            return dict(r)

    def update(self, uid, **vals):
        self.user(uid)
        vals["last_activity"] = time.time()

        with self.conn() as c:
            c.execute(
                "UPDATE users SET "
                + ",".join(f"{k}=?" for k in vals)
                + " WHERE user_id=?",
                (*vals.values(), uid),
            )

    def memory(self, uid):
        cutoff = time.time() - MEMORY_TTL

        with self.conn() as c:
            c.execute(
                "DELETE FROM memory WHERE created_at<?",
                (cutoff,),
            )

            rows = c.execute(
                "SELECT role,content FROM memory "
                "WHERE user_id=? AND created_at>=? ORDER BY id",
                (uid, cutoff),
            ).fetchall()

            return [dict(x) for x in rows]

    def add_memory(self, uid, role, content):
        with self.conn() as c:
            c.execute(
                "INSERT INTO memory(user_id,role,content,created_at) "
                "VALUES(?,?,?,?)",
                (uid, role, content, time.time()),
            )

    def clear_memory(self, uid):
        with self.conn() as c:
            c.execute(
                "DELETE FROM memory WHERE user_id=?",
                (uid,),
            )

    def count_memory(self, uid):
        return len(self.memory(uid))

    def allowed(self, uid, profile_id):
        limit, window = RATE_LIMITS[int(profile_id)]
        cutoff = time.time() - window

        with self.conn() as c:
            rows = c.execute(
                "SELECT created_at FROM usage "
                "WHERE user_id=? AND profile_id=? AND created_at>=? "
                "ORDER BY created_at",
                (str(uid), int(profile_id), cutoff),
            ).fetchall()

            count = len(rows)

            seconds_left = (
                max(
                    0,
                    int(rows[0]["created_at"] + window - time.time()),
                )
                if count >= limit
                else 0
            )

            return count < limit, max(0, limit - count), seconds_left

    def consume(self, uid, profile_id):
        with self.conn() as c:
            c.execute(
                "INSERT INTO usage(user_id,profile_id,created_at) "
                "VALUES(?,?,?)",
                (str(uid), int(profile_id), time.time()),
            )


class Bale:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60)
        self.base = BALE_API.rstrip("/") + BOT_TOKEN

    async def close(self):
        await self.client.aclose()

    async def call(self, method, payload=None, files=None):
        url = f"{self.base}/{method}"

        if files:
            r = await self.client.post(
                url,
                data=payload or {},
                files=files,
            )
        else:
            r = await self.client.post(
                url,
                json=payload or {},
            )

        r.raise_for_status()
        d = r.json()

        if not d.get("ok"):
            raise RuntimeError(d.get("description", "Bale API error"))

        return d.get("result")

    async def msg(self, cid, text, markup=None):
        payload = {
            "chat_id": cid,
            "text": text[:4096],
        }

        if markup:
            payload["reply_markup"] = markup

        return await self.call("sendMessage", payload)

    async def edit(self, cid, mid, text, markup=None):
        payload = {
            "chat_id": cid,
            "message_id": mid,
            "text": text[:4096],
        }

        if markup:
            payload["reply_markup"] = markup

        return await self.call("editMessageText", payload)

    async def delete(self, cid, mid):
        return await self.call(
            "deleteMessage",
            {"chat_id": cid, "message_id": mid},
        )

    async def answer(self, qid):
        try:
            await self.call(
                "answerCallbackQuery",
                {"callback_query_id": qid},
            )
        except Exception:
            pass

    async def upload(
        self, method, cid, data, field, filename, mime, caption=None
    ):
        payload = {"chat_id": str(cid)}

        if caption:
            payload["caption"] = caption[:1024]

        return await self.call(
            method,
            payload,
            {field: (filename, data, mime)},
        )

    async def updates(self, offset=None):
        payload = {"timeout": 25, "limit": 100}

        if offset is not None:
            payload["offset"] = offset

        return await self.call("getUpdates", payload)

    async def webhook(self, url):
        payload = {"url": url}

        if WEBHOOK_SECRET:
            payload["secret_token"] = WEBHOOK_SECRET

        return await self.call("setWebhook", payload)


class AI:
    def cfg(self, n):
        p = AI_PROFILES[int(n)]
        return p["key"], p["base"], p["model"]

    async def one(self, n, messages, lang):
        p = AI_PROFILES[int(n)]

        if not p.get("enabled"):
            return OWEN_DISABLED_MESSAGE

        key, base, model = self.cfg(n)

        if not key:
            raise RuntimeError(
                f"API key is not configured for {p['name']}"
            )

        if not base or not model:
            raise RuntimeError(
                f"Endpoint/model is not configured for {p['name']}"
            )

        system = (
            f"You are {BOT_NAME}, a professional multilingual AI "
            f"assistant inside Bale. Reply naturally in the user's "
            f"selected language ({lang}). If asked who you are, "
            f"say {BOT_NAME}."
        )

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        if int(n) == 3:
            headers["HTTP-Referer"] = os.getenv(
                "OPENROUTER_SITE_URL", "https://bale.ai"
            )
            headers["X-OpenRouter-Title"] = BOT_NAME

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=15.0)
            ) as client:
                response = await client.post(
                    base.rstrip("/") + "/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system},
                            *messages,
                        ],
                    },
                )

                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "درخواست هوش مصنوعی بیش از حد طول کشید. "
                "کمی بعد دوباره تلاش کنید."
            ) from exc

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code

            if status == 401:
                detail = "کلید API معتبر نیست یا دسترسی ندارد."
            elif status == 402:
                detail = "اعتبار یا پرداخت سرویس API کافی نیست."
            elif status == 404:
                detail = "مدل یا endpoint پیدا نشد؛ تنظیمات سرویس را بررسی کنید."
            elif status == 429:
                detail = "محدودیت درخواست سرویس API فعال شده است."
            elif status in (500, 502, 503, 504):
                detail = "سرویس هوش مصنوعی موقتاً در دسترس نیست."
            else:
                detail = (
                    f"سرویس هوش مصنوعی پاسخ خطا داد "
                    f"(HTTP {status})."
                )

            raise RuntimeError(detail) from exc

        except (httpx.RequestError, ValueError) as exc:
            raise RuntimeError(
                "اتصال به سرویس هوش مصنوعی ناموفق بود "
                "یا پاسخ نامعتبر دریافت شد."
            ) from exc

        choices = data.get("choices")

        if not isinstance(choices, list) or not choices:
            raise RuntimeError(
                "پاسخ سرویس هوش مصنوعی ساختار معتبری ندارد."
            )

        message = (
            choices[0].get("message")
            if isinstance(choices[0], dict)
            else None
        )

        content = (
            message.get("content")
            if isinstance(message, dict)
            else None
        )

        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(
                "سرویس هوش مصنوعی پاسخ متنی معتبری برنگرداند."
            )

        return content.strip()

    async def chat(self, n, messages, lang):
        n = int(n)

        if not AI_PROFILES[n].get("enabled"):
            return OWEN_DISABLED_MESSAGE

        # Do not silently switch providers.
        return await self.one(n, messages, lang)

    async def translate(self, n, text, target, lang):
        return await self.chat(
            n,
            [{
                "role": "user",
                "content": (
                    f"Translate the following text into {target}. "
                    "Preserve meaning and formatting. "
                    "Return only the translation, no explanation.\n\n"
                    f"{text}"
                ),
            }],
            lang,
        )


async def image_generate(prompt):
    key = os.getenv("IMAGE_API_KEY", "")
    url = os.getenv(
        "IMAGE_API_URL",
        "https://api.openai.com/v1/images/generations",
    )
    model = os.getenv("IMAGE_MODEL", "gpt-image-1")

    if not key:
        raise RuntimeError("IMAGE_API_KEY is not configured")

    async with httpx.AsyncClient(timeout=180) as c:
        r = await c.post(
            url,
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "prompt": prompt,
                "size": "1024x1024",
            },
        )
        r.raise_for_status()
        item = r.json().get("data", [{}])[0]

        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"])

        if item.get("url"):
            rr = await c.get(item["url"])
            rr.raise_for_status()
            return rr.content

    raise RuntimeError("No image returned")


async def voice_generate(text):
    key = os.getenv("VOICE_API_KEY", "")
    url = os.getenv(
        "VOICE_API_URL",
        "https://api.openai.com/v1/audio/speech",
    )
    model = os.getenv("VOICE_MODEL", "gpt-4o-mini-tts")

    if not key:
        raise RuntimeError("VOICE_API_KEY is not configured")

    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(
            url,
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "input": text,
                "voice": os.getenv("VOICE_NAME", "alloy"),
                "response_format": "mp3",
            },
        )
        r.raise_for_status()
        return r.content


async def weather(city):
    """Live weather using Open-Meteo; no API key required."""

    async with httpx.AsyncClient(
        timeout=25,
        follow_redirects=True,
    ) as c:
        geo = await c.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city,
                "count": 1,
                "language": "fa",
                "format": "json",
            },
        )
        geo.raise_for_status()
        results = geo.json().get("results") or []

        # Retry in English for city names not indexed in Persian.
        if not results:
            geo = await c.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": city,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
            )
            geo.raise_for_status()
            results = geo.json().get("results") or []

        if not results:
            raise RuntimeError("City not found")

        place = results[0]
        lat, lon = place["latitude"], place["longitude"]

        r = await c.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "apparent_temperature,is_day,precipitation,"
                    "weather_code,wind_speed_10m"
                ),
                "timezone": "auto",
            },
        )
        r.raise_for_status()
        d = r.json()
        cur = d.get("current", {})

    codes = {
        0: "صاف",
        1: "عمدتاً صاف",
        2: "نیمه‌ابری",
        3: "ابری",
        45: "مه‌آلود",
        48: "مه یخ‌زن",
        51: "نم‌نم باران",
        53: "باران ریز",
        55: "باران ریز شدید",
        61: "باران خفیف",
        63: "باران",
        65: "باران شدید",
        71: "برف خفیف",
        73: "برف",
        75: "برف شدید",
        80: "رگبار خفیف",
        81: "رگبار",
        82: "رگبار شدید",
        95: "رعدوبرق",
        96: "رعدوبرق و تگرگ",
        99: "رعدوبرق شدید",
    }

    return {
        "city": place.get("name", city),
        "temp": round(cur.get("temperature_2m", 0)),
        "wind": round(cur.get("wind_speed_10m", 0)),
        "humidity": cur.get("relative_humidity_2m", 0),
        "condition": codes.get(cur.get("weather_code"), "نامشخص"),
    }


# Iranian/Persian-language news feeds.
IRAN_NEWS_FEEDS = [
    "https://www.irna.ir/rss",
    "https://www.isna.ir/rss",
    "https://www.mehrnews.com/rss",
    "https://www.tasnimnews.com/fa/rss",
    "https://www.yjc.ir/fa/rss/allnews",
    "https://www.tabnak.ir/fa/rss/allnews",
    "https://www.khabaronline.ir/rss",
    "https://www.asriran.com/fa/rss/allnews",
    "https://www.iribnews.ir/fa/rss/allnews",
    "https://www.farsnews.ir/rss",
]


async def news(category):
    import xml.etree.ElementTree as ET

    # Poll several Persian feeds in parallel.
    async def fetch(c, url):
        try:
            r = await c.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; BaleBot/1.0)"
                },
                timeout=12,
            )
            r.raise_for_status()
            root = ET.fromstring(r.content)
            items = []

            for item in root.findall(".//item")[:15]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                desc = (item.findtext("description") or "").strip()

                if title and link:
                    items.append({
                        "title": title,
                        "url": link,
                        "description": desc,
                    })

            return items

        except Exception as e:
            log.debug("RSS source unavailable: %s", e)
            return []

    async with httpx.AsyncClient(follow_redirects=True) as c:
        groups = await asyncio.gather(
            *(fetch(c, u) for u in IRAN_NEWS_FEEDS)
        )

    all_items = []
    seen = set()

    keywords = {
        "technology": [
            "فناوری", "تکنولوژی", "دانش‌بنیان", "مخابرات",
            "گوشی", "اینترنت",
        ],
        "ai": [
            "هوش مصنوعی", "هوش‌مصنوعی",
            "مدل زبانی", "ربات هوشمند",
        ],
        "sports": [
            "ورزش", "فوتبال", "والیبال",
            "بسکتبال", "کشتی", "تیم ملی",
        ],
        "world": [
            "جهان", "بین‌الملل", "منطقه", "خارجی",
        ],
    }.get(category, [])

    for group in groups:
        for item in group:
            key = item["url"] or item["title"]

            if key in seen:
                continue

            seen.add(key)

            if keywords and not any(
                k in (item["title"] + " " + item["description"])
                for k in keywords
            ):
                continue

            all_items.append(item)

    return all_items[:5]


async def video_generate(prompt):
    key = os.getenv("VIDEO_API_KEY", "")
    create = os.getenv("VIDEO_CREATE_URL", "")
    status_tpl = os.getenv("VIDEO_STATUS_URL_TEMPLATE", "")

    if not all((key, create, status_tpl)):
        raise RuntimeError("VIDEO API is not configured")

    headers = {"Authorization": f"Bearer {key}"}

    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            create,
            headers=headers,
            json={"prompt": prompt},
        )
        r.raise_for_status()
        d = r.json()
        jid = d.get("id") or d.get("job_id")

        if not jid:
            raise RuntimeError("No video job id")

        deadline = time.time() + int(
            os.getenv("VIDEO_TIMEOUT_SECONDS", "600")
        )
        interval = float(os.getenv("VIDEO_POLL_SECONDS", "5"))

        while time.time() < deadline:
            await asyncio.sleep(interval)

            rr = await c.get(
                status_tpl.format(job_id=jid),
                headers=headers,
            )
            rr.raise_for_status()
            x = rr.json()
            s = str(x.get("status", "")).lower()

            if s in {
                "completed", "complete", "succeeded", "success"
            }:
                u = (
                    x.get("video_url")
                    or x.get("url")
                    or x.get("output")
                )

                if not u:
                    raise RuntimeError("Video completed without URL")

                v = await c.get(u)
                v.raise_for_status()
                return v.content

            if s in {
                "failed", "error", "cancelled", "canceled"
            }:
                raise RuntimeError("Video generation failed")

    raise TimeoutError("Video generation timed out")


class BotApp:
    def __init__(self):
        self.b = Bale()
        self.db = DB(DB_PATH)
        self.ai = AI()
        self.states = {}

    def user(self, uid):
        return self.db.user(uid)

    def lang(self, uid):
        return self.user(uid).get("language") or "en"

    async def start(self, m):
        uid = str(m["from"]["id"])
        cid = str(m["chat"]["id"])
        u = self.user(uid)

        if not u.get("language"):
            self.states[uid] = {"state": "lang"}
            await self.b.msg(cid, tr("fa", "choose"), lang_kb())
            return

        await self.b.msg(
            cid,
            tr(u["language"], "welcome", name=BOT_NAME),
            main_kb(u["language"]),
        )

    async def callback(self, q):
        uid = str(q["from"]["id"])
        cid = str(q["message"]["chat"]["id"])
        mid = q["message"]["message_id"]
        data = q.get("data", "")

        await self.b.answer(q["id"])

        if data.startswith("lang:"):
            lang = data.split(":", 1)[1]

            if lang in LANGS:
                self.db.update(uid, language=lang)
                self.states.pop(uid, None)
                await self.b.edit(
                    cid,
                    mid,
                    tr(lang, "welcome", name=BOT_NAME),
                    main_kb(lang),
                )
            return

        lang = self.lang(uid)

        if data == "menu:main":
            self.states.pop(uid, None)
            await self.b.edit(
                cid,
                mid,
                tr(lang, "welcome", name=BOT_NAME),
                main_kb(lang),
            )

        elif data == "menu:ai":
            await self.b.edit(
                cid, mid, tr(lang, "ai_select"), ai_kb(lang)
            )

        elif data.startswith("ai:"):
            selected = int(data.split(":", 1)[1])
            self.db.update(uid, selected_ai=selected)

            if selected == 2:
                await self.b.edit(
                    cid, mid, OWEN_DISABLED_MESSAGE, main_kb(lang)
                )
            else:
                await self.b.edit(
                    cid,
                    mid,
                    tr(
                        lang,
                        "ai_selected",
                        n=AI_PROFILES[selected]["name"],
                    ),
                    main_kb(lang),
                )

        elif data in ("menu:image", "menu:video", "menu:voice"):
            st = {
                "menu:image": "image",
                "menu:video": "video",
                "menu:voice": "voice",
            }[data]

            self.states[uid] = {"state": st}

            await self.b.edit(
                cid,
                mid,
                tr(lang, "prompt" if st in ("image", "video") else "text"),
                back_kb(lang),
            )

        elif data == "menu:translate":
            self.states[uid] = {"state": "translate"}
            await self.b.edit(
                cid,
                mid,
                tr(lang, "text"),
                translate_kb(lang),
            )

        elif data.startswith("target:"):
            st = self.states.get(uid, {})

            self.states[uid] = {
                "state": "translate_target",
                "text": st.get("text", ""),
                "target": data.split(":", 1)[1],
            }

            await self.b.msg(cid, tr(lang, "text"), back_kb(lang))

        elif data == "menu:weather":
            self.states[uid] = {"state": "weather"}
            await self.b.edit(
                cid, mid, tr(lang, "weather_city"), back_kb(lang)
            )

        elif data == "menu:news":
            await self.b.edit(
                cid, mid, tr(lang, "news_cat"), news_kb(lang)
            )

        elif data.startswith("news:"):
            await self.do_news(cid, lang, data.split(":", 1)[1])

        elif data == "menu:memory":
            await self.b.edit(
                cid, mid, tr(lang, "memory_status"), memory_kb(lang)
            )

        elif data == "memory:status":
            n = self.db.count_memory(uid)

            await self.b.edit(
                cid,
                mid,
                tr(lang, "memory_empty")
                if not n
                else tr(lang, "memory_count", n=n),
                memory_kb(lang),
            )

        elif data == "memory:clear":
            self.db.clear_memory(uid)
            await self.b.edit(
                cid, mid, tr(lang, "memory_cleared"), memory_kb(lang)
            )

        elif data == "memory:info":
            await self.b.edit(
                cid, mid, tr(lang, "memory_info"), memory_kb(lang)
            )

        elif data == "menu:settings":
            await self.b.edit(
                cid, mid, tr(lang, "settings_text"), settings_kb(lang)
            )

        elif data == "settings:language":
            await self.b.edit(
                cid, mid, tr(lang, "choose"), lang_kb()
            )

        elif data == "settings:notify":
            u = self.user(uid)
            en = not bool(u.get("notifications", 1))

            self.db.update(uid, notifications=int(en))

            await self.b.edit(
                cid,
                mid,
                tr(lang, "notify_on" if en else "notify_off"),
                settings_kb(lang),
            )

        elif data == "menu:about":
            await self.b.edit(
                cid,
                mid,
                tr(lang, "about_text", name=BOT_NAME),
                back_kb(lang),
            )

    async def do_news(self, cid, lang, cat):
        try:
            a = await news(cat)

            text = "\n\n".join(
                f"📰 {x.get('title', '')}\n"
                f"{(x.get('description') or '')[:250]}"
                for x in a
            ) or tr(lang, "news_error")

            await self.b.msg(cid, text, back_kb(lang))

        except Exception:
            log.exception("news")
            await self.b.msg(cid, tr(lang, "news_error"), back_kb(lang))

    async def message(self, m):
        uid = str(m["from"]["id"])
        cid = str(m["chat"]["id"])
        text = (m.get("text") or "").strip()
        self.user(uid)

        # Added: remember the most recently active chat.
        self.db.set_last_chat(cid)

        if text.startswith("/start"):
            await self.start(m)
            return

        if not text:
            return

        lang = self.lang(uid)

        if len(text) > MAX_INPUT:
            await self.b.msg(cid, tr(lang, "invalid"))
            return

        st = self.states.get(uid, {}).get("state")
        u = self.user(uid)
        profile_id = int(u.get("selected_ai") or 1)
        is_admin = is_admin_user(uid)
        consumes_ai = st in (None, "translate_target")

        if consumes_ai and not is_admin:
            allowed, remaining, seconds_left = self.db.allowed(
                uid, profile_id
            )

            if not allowed:
                minutes = max(1, int((seconds_left + 59) // 60))

                await self.b.msg(
                    cid,
                    f"⛔ سهمیه پروفایل "
                    f"{AI_PROFILES[profile_id]['name']} تمام شده است. "
                    f"حدود {minutes} دقیقه دیگر دوباره تلاش کنید.",
                )
                return

        try:
            if st == "image":
                await self.run_file(
                    cid, lang, image_generate(text),
                    "sendPhoto", "photo", "image.png", "image/png",
                )

            elif st == "video":
                await self.run_file(
                    cid, lang, video_generate(text),
                    "sendVideo", "video", "video.mp4", "video/mp4",
                )

            elif st == "voice":
                await self.run_file(
                    cid, lang, voice_generate(text),
                    "sendVoice", "voice", "voice.mp3", "audio/mpeg",
                )

            elif st == "translate":
                self.states[uid] = {
                    "state": "translate_target",
                    "text": text,
                }

                await self.b.msg(
                    cid, tr(lang, "target"), translate_kb(lang)
                )

            elif st == "translate_target":
                target = self.states[uid].get("target", lang)

                if profile_id == 2:
                    answer = OWEN_DISABLED_MESSAGE
                else:
                    answer = await self.ai.translate(
                        profile_id,
                        self.states[uid].get("text", text),
                        LANGS.get(target, target),
                        lang,
                    )

                if not is_admin:
                    self.db.consume(uid, profile_id)

                self.states.pop(uid, None)
                await self.b.msg(cid, answer, back_kb(lang))

            elif st == "weather":
                self.states.pop(uid, None)
                d = await weather(text)

                await self.b.msg(
                    cid,
                    tr(lang, "weather_result", **d),
                    back_kb(lang),
                )

            else:
                if profile_id == 2:
                    if not is_admin:
                        self.db.consume(uid, profile_id)

                    await self.b.msg(
                        cid, OWEN_DISABLED_MESSAGE, back_kb(lang)
                    )

                else:
                    await self.chat(cid, uid, text, lang)

                    if not is_admin:
                        self.db.consume(uid, profile_id)

        except Exception as exc:
            log.warning(
                "message processing failed (%s)",
                type(exc).__name__,
            )

            await self.b.msg(
                cid,
                str(exc)
                if isinstance(exc, RuntimeError)
                else tr(lang, "error"),
                back_kb(lang),
            )

    async def run_file(
        self, cid, lang, coro, method, field, filename, mime
    ):
        s = await self.b.msg(cid, tr(lang, "processing"))

        try:
            data = await coro

            await self.b.delete(cid, s["message_id"])

            await self.b.upload(
                method,
                cid,
                data,
                field,
                filename,
                mime,
                tr(lang, "done"),
            )

        except Exception:
            try:
                await self.b.delete(cid, s["message_id"])
            except Exception:
                pass

            raise

    async def chat(self, cid, uid, text, lang):
        thinking = await self.b.msg(cid, tr(lang, "thinking"))
        self.db.add_memory(uid, "user", text)

        try:
            u = self.user(uid)

            ans = await self.ai.chat(
                u.get("selected_ai", 1),
                self.db.memory(uid),
                lang,
            )

            self.db.add_memory(uid, "assistant", ans)

            try:
                await self.b.delete(cid, thinking["message_id"])
            except Exception:
                pass

            await self.b.msg(cid, ans)

        except Exception:
            try:
                await self.b.delete(cid, thinking["message_id"])
            except Exception:
                pass

            raise

    async def update(self, u):
        if "callback_query" in u:
            await self.callback(u["callback_query"])
        elif "message" in u:
            await self.message(u["message"])


app_logic = BotApp()


async def polling():
    offset = None

    print("\n========================================")
    print(f"  {BOT_NAME}")
    print("  Pydroid 3 / Polling mode")
    print("  ربات در حال اجراست...\n")
    print("  برای توقف: Ctrl+C")
    print("========================================\n")

    while True:
        try:
            updates = await app_logic.b.updates(offset)

            for u in updates:
                offset = int(u["update_id"]) + 1

                try:
                    await app_logic.update(u)
                except Exception:
                    log.exception("update")

        except asyncio.CancelledError:
            raise

        except KeyboardInterrupt:
            raise

        except Exception:
            log.exception("polling")
            await asyncio.sleep(3)


# Added: send a normal visible time message every hour.
async def hourly_time_notifier():
    while True:
        await asyncio.sleep(3600)

        try:
            chat_id = app_logic.db.get_last_chat()

            if not chat_id:
                continue

            now = datetime.now().astimezone()

            message = (
                "🕒 گزارش خودکار زمان\n\n"
                f"📅 تاریخ: {now.strftime('%Y-%m-%d')}\n"
                f"⏰ ساعت: {now.strftime('%H:%M:%S')}\n"
                f"🌐 منطقه زمانی: {now.tzname() or 'محلی'}"
            )

            await app_logic.b.msg(chat_id, message)
            log.info("Hourly time message sent")

        except asyncio.CancelledError:
            raise

        except Exception:
            log.exception("Hourly time notification failed")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BALE_BOT_TOKEN تنظیم نشده است. "
            "آن را در Environment Variables وارد کنید."
        )

    notifier_task = asyncio.create_task(hourly_time_notifier())

    try:
        await polling()

    finally:
        notifier_task.cancel()

        await asyncio.gather(
            notifier_task,
            return_exceptions=True,
        )

        await app_logic.b.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nربات متوقف شد.")
