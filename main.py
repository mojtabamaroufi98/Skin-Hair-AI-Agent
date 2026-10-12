from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from agent import run_agent


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


@app.get("/")
async def home():

    return {
        "status": "online",
        "message": "Skin & Hair AI Agent is running"
    }


@app.post("/agent")
async def agent(
    message: str = Form(...),
    age: int | None = Form(None),
    skin_type: str | None = Form(None),
    hair_type: str | None = Form(None),
    user_id: str | None = Form(None),
    image: UploadFile | None = File(None)
):

    try:

        # -----------------------------
        # User profile
        # -----------------------------

        user_context = ""

        if age is not None:
            user_context += f"\nسن کاربر: {age}"

        if skin_type:
            user_context += f"\nنوع پوست: {skin_type}"

        if hair_type:
            user_context += f"\nنوع مو: {hair_type}"


        # -----------------------------
        # Image
        # -----------------------------

        image_bytes = None
        image_type = None

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


        # -----------------------------
        # Final message
        # -----------------------------

        final_message = message + user_context


        # -----------------------------
        # Run Agent
        # -----------------------------

        answer = run_agent(
            final_message,
            image_bytes=image_bytes,
            image_type=image_type
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