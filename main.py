from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from agent import run_agent
from tools import create_routine, create_home_mask


app = FastAPI(
    title="Skin & Hair AI Agent",
    description="AI Agent for skin and hair care",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Home
# ==========================================

@app.get("/")
async def home():

    return {
        "status": "online",
        "message": "Skin & Hair AI Agent is running"
    }


# ==========================================
# Agent
# ==========================================

@app.post("/agent")
async def agent(
    message: str = Form(...),

    # -----------------------------
    # User Profile
    # -----------------------------

    name: str | None = Form(None),
    age: int | None = Form(None),
    gender: str | None = Form(None),
    skin_type: str | None = Form(None),
    hair_type: str | None = Form(None),
    scalp_type: str | None = Form(None),
    allergies: str | None = Form(None),
    concerns: str | None = Form(None),
    goal: str | None = Form(None),
    products: str | None = Form(None),

    user_id: str | None = Form(None),

    # -----------------------------
    # Image
    # -----------------------------

    image: UploadFile | None = File(None)
):

    image_bytes = None
    image_type = None

    try:

        # ==========================================
        # Image Validation
        # ==========================================

        if image:

            allowed_types = [
                "image/jpeg",
                "image/png",
                "image/webp"
            ]

            if image.content_type not in allowed_types:

                return {
                    "success": False,
                    "answer": "فرمت تصویر باید JPG، PNG یا WEBP باشد.",
                    "session_id": user_id
                }

            image_bytes = await image.read()
            image_type = image.content_type

            if not image_bytes:

                return {
                    "success": False,
                    "answer": "تصویر خالی است.",
                    "session_id": user_id
                }

            print("IMAGE NAME:", image.filename)
            print("IMAGE TYPE:", image_type)
            print("IMAGE SIZE:", len(image_bytes), "bytes")

        # ==========================================
        # Run Agent
        # ==========================================

        answer = run_agent(
            message=message,

            image_bytes=image_bytes,
            image_type=image_type,

            user_id=user_id,

            name=name,
            age=age,
            gender=gender,
            skin_type=skin_type,
            hair_type=hair_type,
            scalp_type=scalp_type,
            allergies=allergies,
            concerns=concerns,
            goal=goal,
            products=products
        )

        print("AGENT ANSWER:", answer)

        return {
            "success": True,
            "answer": answer,
            "session_id": user_id,
            "image_received": image_bytes is not None
        }

    except Exception as e:

        print("AGENT ERROR:", repr(e))

        return {
            "success": False,
            "answer": f"خطا در اجرای Agent: {str(e)}",
            "session_id": user_id,
            "image_received": image_bytes is not None
        }


# ==========================================
# Routine
# ==========================================

@app.post("/routine")
async def routine(
    days: int = Form(7),

    name: str | None = Form(None),
    age: int | None = Form(None),
    gender: str | None = Form(None),
    skin_type: str | None = Form(None),
    hair_type: str | None = Form(None),
    scalp_type: str | None = Form(None),
    allergies: str | None = Form(None),
    concerns: str | None = Form(None),
    goal: str | None = Form(None),
    products: str | None = Form(None)
):

    try:

        result = create_routine(
            skin_type=skin_type,
            hair_type=hair_type,
            days=days
        )

        # ==========================================
        # Convert Backend Routine
        # To Android Routine Model
        # ==========================================

        morning_steps = []
        night_steps = []
        weekly_steps = []

        routine_days = result.get(
            "routine",
            []
        )

        if routine_days:

            first_day = routine_days[0]

            skin_data = first_day.get(
                "skin",
                {}
            )

            morning_data = skin_data.get(
                "morning",
                []
            )

            night_data = skin_data.get(
                "night",
                []
            )

            hair_data = first_day.get(
                "hair",
                []
            )

            # --------------------------------------
            # Morning
            # --------------------------------------

            step_id = 1

            for item in morning_data:

                morning_steps.append(
                    {
                        "id": step_id,
                        "title": item,
                        "category": "پوست",
                        "description": item,
                        "frequency": "هر روز صبح",
                        "done": False
                    }
                )

                step_id += 1

            # --------------------------------------
            # Hair
            # --------------------------------------

            for item in hair_data:

                morning_steps.append(
                    {
                        "id": step_id,
                        "title": item,
                        "category": "مو",
                        "description": item,
                        "frequency": "بر اساس نیاز",
                        "done": False
                    }
                )

                step_id += 1

            # --------------------------------------
            # Night
            # --------------------------------------

            for item in night_data:

                night_steps.append(
                    {
                        "id": step_id,
                        "title": item,
                        "category": "پوست",
                        "description": item,
                        "frequency": "هر شب",
                        "done": False
                    }
                )

                step_id += 1

        # ==========================================
        # Weekly
        # ==========================================

        weekly_steps.append(
            {
                "id": 100,
                "title": "بررسی وضعیت پوست و مو",
                "category": "مراقبت",
                "description": (
                    "وضعیت پوست و مو و تغییرات ایجادشده "
                    "در طول هفته بررسی شود."
                ),
                "frequency": "هفته‌ای یک بار",
                "done": False
            }
        )

        # ==========================================
        # Response
        # ==========================================

        return {
            "morning": morning_steps,
            "night": night_steps,
            "weekly": weekly_steps
        }

    except Exception as e:

        print(
            "ROUTINE ERROR:",
            repr(e)
        )

        return {
            "success": False,
            "error": str(e)
        }


# ==========================================
# Home Masks
# ==========================================

@app.post("/masks")
async def masks(
    category: str = Form("پوست"),

    name: str | None = Form(None),
    age: int | None = Form(None),
    gender: str | None = Form(None),
    skin_type: str | None = Form(None),
    hair_type: str | None = Form(None),
    scalp_type: str | None = Form(None),
    allergies: str | None = Form(None),
    concerns: str | None = Form(None),
    goal: str | None = Form(None),
    products: str | None = Form(None)
):

    try:

        result = create_home_mask(
            category=category,
            skin_type=skin_type,
            hair_type=hair_type,
            scalp_type=scalp_type,
            allergies=allergies,
            concerns=concerns,
            goal=goal
        )

        # ==========================================
        # Return Only Mask List
        # ==========================================

        return result.get(
            "masks",
            []
        )

    except Exception as e:

        print(
            "MASK ERROR:",
            repr(e)
        )

        return {
            "success": False,
            "error": str(e)
        }