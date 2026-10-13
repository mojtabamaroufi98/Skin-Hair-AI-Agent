from typing import Optional
import os
import requests

from openai import OpenAI
from dotenv import load_dotenv


# ==========================================
# Environment
# ==========================================

load_dotenv()


# ==========================================
# Main AI Configuration
# ==========================================

AI_API_KEY = os.getenv("AI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL")
AI_MODEL = os.getenv("AI_MODEL")


# ==========================================
# Web Search Configuration
# ==========================================

WEB_SEARCH_API_KEY = os.getenv("WEB_SEARCH_API_KEY")
WEB_SEARCH_BASE_URL = os.getenv("WEB_SEARCH_BASE_URL")
WEB_SEARCH_MODEL = os.getenv("WEB_SEARCH_MODEL")


# ==========================================
# Validation
# ==========================================

if not AI_API_KEY:
    raise ValueError(
        "AI_API_KEY در فایل .env پیدا نشد."
    )

if not AI_BASE_URL:
    raise ValueError(
        "AI_BASE_URL در فایل .env پیدا نشد."
    )

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL در فایل .env پیدا نشد."
    )


# ==========================================
# Main LLM Client
# ==========================================

llm_client = OpenAI(
    api_key=AI_API_KEY,
    base_url=AI_BASE_URL,
    timeout=120.0
)


# ==========================================
# Web Search
# ==========================================

def search_web(query: str):
    """
    جستجوی واقعی وب برای پیدا کردن اطلاعات
    مرتبط با پوست، مو و مراقبت از آنها.
    """

    if not query or not query.strip():

        return {
            "success": False,
            "tool": "search_web",
            "query": query,
            "error": "عبارت جستجو خالی است.",
            "results": []
        }

    if not WEB_SEARCH_API_KEY:

        return {
            "success": False,
            "tool": "search_web",
            "query": query,
            "error": "WEB_SEARCH_API_KEY در فایل .env پیدا نشد.",
            "results": []
        }

    if not WEB_SEARCH_BASE_URL:

        return {
            "success": False,
            "tool": "search_web",
            "query": query,
            "error": "WEB_SEARCH_BASE_URL در فایل .env پیدا نشد.",
            "results": []
        }

    if not WEB_SEARCH_MODEL:

        return {
            "success": False,
            "tool": "search_web",
            "query": query,
            "error": "WEB_SEARCH_MODEL در فایل .env پیدا نشد.",
            "results": []
        }

    try:

        # ==========================================
        # Responses URL
        # ==========================================

        responses_url = (
            WEB_SEARCH_BASE_URL.rstrip("/")
            + "/responses"
        )

        # ==========================================
        # Payload
        # ==========================================

        payload = {
            "model": WEB_SEARCH_MODEL,

            "input": [
                {
                    "role": "user",
                    "content": query
                }
            ],

            "instructions": """
تو یک ابزار جستجوی وب برای یک دستیار هوشمند
پوست و مو هستی.

اطلاعات را فقط از منابع واقعی و قابل اعتماد وب
پیدا کن.

قوانین:

- اطلاعات را از خودت نساز.
- برای موضوعات پزشکی و مراقبت پوست و مو،
  منابع معتبر را ترجیح بده.
- اگر اطلاعات کافی پیدا نشد، صادقانه اعلام کن.
- قیمت محصول را بدون منبع معتبر اعلام نکن.
- موجودی محصول را بدون منبع معتبر اعلام نکن.
- مشخصات محصول را بدون منبع معتبر اعلام نکن.
- اگر لینک منبع در دسترس بود، آن را حفظ کن.
- پاسخ را به زبان فارسی ارائه کن.
""",

            "max_output_tokens": 1500,

            "web_search": True
        }

        # ==========================================
        # Headers
        # ==========================================

        headers = {
            "Authorization": (
                f"Bearer {WEB_SEARCH_API_KEY}"
            ),
            "Content-Type": "application/json"
        }

        # ==========================================
        # Request
        # ==========================================

        response = requests.post(
            responses_url,
            headers=headers,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        # ==========================================
        # Main Answer
        # ==========================================

        answer = data.get(
            "output_text",
            ""
        )

        # ==========================================
        # Extract Sources
        # ==========================================

        sources = []

        for output_item in data.get("output", []):

            if not isinstance(output_item, dict):
                continue

            content = output_item.get(
                "content",
                []
            )

            if not isinstance(content, list):
                continue

            for content_item in content:

                if not isinstance(content_item, dict):
                    continue

                annotations = content_item.get(
                    "annotations",
                    []
                )

                if not isinstance(annotations, list):
                    continue

                for annotation in annotations:

                    if not isinstance(annotation, dict):
                        continue

                    url = annotation.get("url")
                    title = annotation.get("title")

                    if url:

                        source = {
                            "title": (
                                title
                                or "منبع وب"
                            ),
                            "url": url
                        }

                        if source not in sources:

                            sources.append(
                                source
                            )

        # ==========================================
        # Result
        # ==========================================

        return {
            "success": True,
            "tool": "search_web",
            "query": query,
            "answer": answer,
            "sources": sources
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "tool": "search_web",
            "query": query,
            "error": str(e),
            "results": []
        }

    except Exception as e:

        return {
            "success": False,
            "tool": "search_web",
            "query": query,
            "error": str(e),
            "results": []
        }


# ==========================================
# Product Search
# ==========================================

def search_products(
    query: str,
    skin_type: Optional[str] = None,
    category: Optional[str] = None
):
    """
    جستجوی محصولات واقعی پوست و مو
    در بازار ایران با استفاده از Web Search.
    """

    if not query or not query.strip():

        return {
            "success": False,
            "tool": "search_products",
            "query": query,
            "error": "عبارت جستجوی محصول خالی است.",
            "results": []
        }

    try:

        search_query = query.strip()

        # ==========================================
        # Skin Type
        # ==========================================

        if skin_type:

            search_query += (
                f" برای پوست {skin_type}"
            )

        # ==========================================
        # Category
        # ==========================================

        if category:

            search_query += (
                f" {category}"
            )

        # ==========================================
        # Iran Market
        # ==========================================

        search_query += """

محصولات موجود در ایران.
نام دقیق محصول.
نام برند.
مشخصات محصول.
قیمت در صورت وجود.
لینک صفحه محصول در صورت وجود.
"""

        # ==========================================
        # Web Search
        # ==========================================

        result = search_web(
            search_query
        )

        if not result.get("success"):

            return {
                "success": False,
                "tool": "search_products",
                "query": query,
                "skin_type": skin_type,
                "category": category,
                "error": result.get("error"),
                "results": []
            }

        return {
            "success": True,
            "tool": "search_products",
            "query": query,
            "skin_type": skin_type,
            "category": category,
            "answer": result.get(
                "answer",
                ""
            ),
            "sources": result.get(
                "sources",
                []
            )
        }

    except Exception as e:

        return {
            "success": False,
            "tool": "search_products",
            "query": query,
            "skin_type": skin_type,
            "category": category,
            "error": str(e),
            "results": []
        }


# ==========================================
# Ingredient Analysis
# ==========================================

def analyze_ingredients(
    ingredients: str
):
    """
    تحلیل ترکیبات یک محصول پوستی یا مویی
    با استفاده از مدل زبانی.

    این تابع تشخیص پزشکی یا تجویز درمانی
    انجام نمی‌دهد.
    """

    if not ingredients or not ingredients.strip():

        return {
            "success": False,
            "tool": "analyze_ingredients",
            "ingredients": ingredients,
            "error": "فهرست ترکیبات خالی است."
        }

    if not AI_API_KEY:

        return {
            "success": False,
            "tool": "analyze_ingredients",
            "ingredients": ingredients,
            "error": "AI_API_KEY در فایل .env پیدا نشد."
        }

    if not AI_MODEL:

        return {
            "success": False,
            "tool": "analyze_ingredients",
            "ingredients": ingredients,
            "error": "AI_MODEL در فایل .env پیدا نشد."
        }

    try:

        prompt = f"""
تو یک دستیار علمی برای بررسی ترکیبات محصولات
پوست، مو و مراقبت شخصی هستی.

ترکیبات زیر را بررسی کن:

{ingredients}

برای هر ترکیب مهم توضیح بده:

1. نام ترکیب
2. کاربرد عمومی
3. مناسب بودن برای چه نوع پوست یا مو
4. نکات احتیاطی
5. احتمال تحریک در صورت مطرح بودن

قوانین مهم:

- تشخیص پزشکی نده.
- ادعای درمان قطعی نکن.
- درباره اثرات ترکیبات اغراق نکن.
- اگر درباره یک ترکیب اطلاعات کافی نداری،
  صادقانه بگو.
- اگر ماده‌ای می‌تواند برای پوست حساس
  تحریک‌کننده باشد، آن را ذکر کن.
- پاسخ فارسی باشد.
- پاسخ را واضح و قابل فهم برای کاربر عادی بنویس.
"""

        response = llm_client.chat.completions.create(
            model=AI_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": """
تو متخصص بررسی علمی و عمومی ترکیبات
محصولات مراقبت پوست و مو هستی.

هدف تو آموزش و ارائه اطلاعات عمومی است،
نه تشخیص بیماری و نه تجویز دارو.
"""
                },

                {
                    "role": "user",
                    "content": prompt
                }
            ],

            max_tokens=1200
        )

        analysis = (
            response
            .choices[0]
            .message
            .content
        )

        return {
            "success": True,
            "tool": "analyze_ingredients",
            "ingredients": ingredients,
            "analysis": analysis
        }

    except Exception as e:

        return {
            "success": False,
            "tool": "analyze_ingredients",
            "ingredients": ingredients,
            "error": str(e)
        }


# ==========================================
# Routine Planner
# ==========================================

def create_routine(
    skin_type: Optional[str] = None,
    hair_type: Optional[str] = None,
    days: int = 7
):
    """
    ساخت چارچوب روتین مراقبت از پوست و مو.

    این Tool مستقل از Provider است و مستقیماً
    هیچ مدل هوش مصنوعی را فراخوانی نمی‌کند.
    """

    allowed_days = [3, 7, 14, 30]

    if days not in allowed_days:
        days = 7

    # ==========================================
    # Normalize Inputs
    # ==========================================

    skin = (
        skin_type or ""
    ).strip().lower()

    hair = (
        hair_type or ""
    ).strip().lower()

    # ==========================================
    # Skin Routine
    # ==========================================

    morning_skin = []
    night_skin = []
    skin_notes = []

    if skin:

        # ---------- Oily Skin ----------

        if any(word in skin for word in [
            "چرب",
            "oily"
        ]):

            morning_skin = [
                "شست‌وشوی ملایم صورت",
                "مرطوب‌کننده سبک و غیرکومدون‌زا",
                "ضدآفتاب مناسب پوست چرب"
            ]

            night_skin = [
                "پاکسازی و شست‌وشوی ملایم صورت",
                "استفاده از محصولات مراقبتی متناسب با نیاز پوست",
                "مرطوب‌کننده سبک"
            ]

            skin_notes.append(
                "از شست‌وشوی بیش از حد و محصولات بسیار خشک‌کننده خودداری شود."
            )

        # ---------- Dry Skin ----------

        elif any(word in skin for word in [
            "خشک",
            "dry"
        ]):

            morning_skin = [
                "شست‌وشوی ملایم یا پاکسازی بدون ایجاد خشکی",
                "مرطوب‌کننده مناسب پوست خشک",
                "ضدآفتاب"
            ]

            night_skin = [
                "پاکسازی ملایم صورت",
                "استفاده از محصول آبرسان در صورت نیاز",
                "مرطوب‌کننده مناسب برای حمایت از سد پوستی"
            ]

            skin_notes.append(
                "از شوینده‌های قوی و شست‌وشوی مکرر با آب بسیار داغ خودداری شود."
            )

        # ---------- Combination Skin ----------

        elif any(word in skin for word in [
            "مختلط",
            "combination"
        ]):

            morning_skin = [
                "شست‌وشوی ملایم صورت",
                "مرطوب‌کننده سبک",
                "ضدآفتاب"
            ]

            night_skin = [
                "پاکسازی ملایم صورت",
                "مراقبت متناسب با نواحی چرب و خشک",
                "مرطوب‌کننده"
            ]

            skin_notes.append(
                "نیاز نواحی مختلف صورت ممکن است متفاوت باشد."
            )

        # ---------- Sensitive Skin ----------

        elif any(word in skin for word in [
            "حساس",
            "sensitive"
        ]):

            morning_skin = [
                "پاکسازی بسیار ملایم",
                "مرطوب‌کننده ساده و مناسب پوست حساس",
                "ضدآفتاب مناسب پوست حساس"
            ]

            night_skin = [
                "پاکسازی ملایم",
                "مرطوب‌کننده ساده"
            ]

            skin_notes.append(
                "محصولات جدید بهتر است به‌تدریج وارد روتین شوند."
            )

            skin_notes.append(
                "از استفاده همزمان چند ماده فعال تحریک‌کننده خودداری شود."
            )

        # ---------- Normal Skin ----------

        else:

            morning_skin = [
                "شست‌وشوی ملایم صورت",
                "مرطوب‌کننده",
                "ضدآفتاب"
            ]

            night_skin = [
                "پاکسازی صورت",
                "مرطوب‌کننده"
            ]

    # ==========================================
    # Hair Routine
    # ==========================================

    hair_routine = []
    hair_notes = []

    if hair:

        # ---------- Oily Hair ----------

        if any(word in hair for word in [
            "چرب",
            "oily"
        ]):

            hair_routine = [
                "شست‌وشوی مو بر اساس میزان چربی پوست سر",
                "استفاده از شامپوی ملایم مناسب پوست سر چرب",
                "استفاده از نرم‌کننده بیشتر روی ساقه و انتهای مو"
            ]

            hair_notes.append(
                "از استفاده زیاد محصولات سنگین و چرب روی پوست سر خودداری شود."
            )

        # ---------- Dry Hair ----------

        elif any(word in hair for word in [
            "خشک",
            "dry"
        ]):

            hair_routine = [
                "شست‌وشوی ملایم مو",
                "استفاده از نرم‌کننده پس از شست‌وشو",
                "مراقبت بیشتر از ساقه و انتهای خشک مو"
            ]

            hair_notes.append(
                "حرارت زیاد سشوار و ابزارهای حرارتی می‌تواند خشکی مو را بیشتر کند."
            )

        # ---------- Damaged Hair ----------

        elif any(word in hair for word in [
            "آسیب",
            "آسیب دیده",
            "damaged"
        ]):

            hair_routine = [
                "شست‌وشوی ملایم",
                "استفاده منظم از نرم‌کننده",
                "کاهش استفاده از ابزارهای حرارتی",
                "مراقبت از ساقه‌های آسیب‌دیده"
            ]

            hair_notes.append(
                "در صورت شکستگی شدید یا آسیب مداوم، علت آسیب باید بررسی شود."
            )

        # ---------- Normal Hair ----------

        else:

            hair_routine = [
                "شست‌وشوی مو بر اساس نیاز",
                "استفاده از شامپوی ملایم",
                "استفاده از نرم‌کننده در صورت نیاز"
            ]

    # ==========================================
    # Build Daily Plan
    # ==========================================

    routine = []

    for day in range(1, days + 1):

        routine.append(
            {
                "day": day,

                "skin": {
                    "morning": morning_skin.copy(),
                    "night": night_skin.copy()
                },

                "hair": hair_routine.copy()
            }
        )

    # ==========================================
    # Result
    # ==========================================

    return {
        "success": True,
        "tool": "create_routine",

        "profile": {
            "skin_type": skin_type,
            "hair_type": hair_type
        },

        "days": days,

        "routine": routine,

        "notes": {
            "skin": skin_notes,
            "hair": hair_notes
        },

        "safety": (
            "این برنامه برای مراقبت عمومی طراحی شده است. "
            "در صورت وجود علائم شدید، ناگهانی، دردناک یا غیرعادی، "
            "ارزیابی پزشک یا متخصص پوست مناسب‌تر است."
        )
    }


# ==========================================
# Safety Check
# ==========================================

def safety_check(
    message: str,
    image_analysis: Optional[str] = None
):
    """
    بررسی اولیه علائم هشدار در مشکلات پوست،
    مو و پوست سر.

    این تابع تشخیص پزشکی انجام نمی‌دهد.
    هدف آن شناسایی نشانه‌هایی است که ممکن است
    نیاز به ارزیابی پزشک داشته باشند.
    """

    if not message:

        return {
            "success": False,
            "tool": "safety_check",
            "needs_doctor": False,
            "reason": "پیام کاربر خالی است."
        }

    # ==========================================
    # Warning Signs
    # ==========================================

    warning_groups = {

        "severe_pain": [
            "درد شدید",
            "درد خیلی شدید",
            "درد غیرقابل تحمل",
            "painful"
        ],

        "rapid_change": [
            "تغییر سریع",
            "به سرعت بزرگ شد",
            "سریع بزرگ شد",
            "ناگهانی ایجاد شد",
            "rapidly changing"
        ],

        "bleeding": [
            "خونریزی",
            "خون میاد",
            "خون آمد",
            "bleeding"
        ],

        "ulcer": [
            "زخم باز",
            "زخم شده",
            "زخم",
            "ulcer"
        ],

        "severe_swelling": [
            "تورم شدید",
            "ورم شدید",
            "swelling"
        ],

        "infection": [
            "چرک",
            "ترشح چرکی",
            "عفونت",
            "تب",
            "گرمی شدید پوست",
            "pus",
            "infection"
        ],

        "severe_reaction": [
            "تورم صورت",
            "تورم لب",
            "تورم زبان",
            "تنگی نفس",
            "مشکل تنفسی",
            "واکنش شدید",
            "allergic reaction"
        ],

        "sudden_hair_loss": [
            "ریزش ناگهانی مو",
            "ریزش ناگهانی موی",
            "ریزش شدید مو",
            "ریزش شدید موی",
            "ریزش خیلی شدید مو",
            "ریزش خیلی شدید موی",
            "ریزش مو به صورت ناگهانی",
            "ریزش موی من به صورت ناگهانی",
            "ناگهان موهام میریزه",
            "ناگهانی موهام میریزه",
            "موهام ناگهانی میریزه",
            "sudden hair loss",
            "severe hair loss"
        ]
    }

    # ==========================================
    # Combine Text
    # ==========================================

    combined_text = message

    if image_analysis:

        combined_text += (
            "\n" + image_analysis
        )

    combined_text = combined_text.lower()

    # ==========================================
    # Detect Warnings
    # ==========================================

    detected = []

    for group_name, keywords in warning_groups.items():

        for keyword in keywords:

            if keyword.lower() in combined_text:

                detected.append(
                    group_name
                )

                break

    # ==========================================
    # Doctor Required
    # ==========================================

    needs_doctor = len(detected) > 0

    # ==========================================
    # Reason
    # ==========================================

    if needs_doctor:

        reason = (
            "برخی از علائم ذکرشده می‌توانند نیازمند "
            "ارزیابی پزشک یا متخصص پوست باشند."
        )

    else:

        reason = (
            "در متن ارسال‌شده علامت هشدار واضحی "
            "شناسایی نشد."
        )

    # ==========================================
    # Result
    # ==========================================

    return {
        "success": True,
        "tool": "safety_check",
        "needs_doctor": needs_doctor,
        "detected_warnings": detected,
        "reason": reason
    }