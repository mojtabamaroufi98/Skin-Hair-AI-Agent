from dotenv import load_dotenv
from openai import OpenAI

import os
import base64
import json

from system_prompt import system_prompt

from tools import (
    search_web,
    search_products,
    analyze_ingredients,
    create_routine,
    safety_check
)


# ==========================================
# Environment
# ==========================================

load_dotenv()

api_key = os.getenv("AI_API_KEY")
base_url = os.getenv("AI_BASE_URL")
model = os.getenv("AI_MODEL")

if not api_key:
    raise ValueError("AI_API_KEY در فایل .env پیدا نشد.")

if not base_url:
    raise ValueError("AI_BASE_URL در فایل .env پیدا نشد.")

if not model:
    raise ValueError("AI_MODEL در فایل .env پیدا نشد.")

# ==========================================
# Client
# ==========================================

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=120.0
)


# ==========================================
# Agent Settings
# ==========================================

MAX_TOOL_ROUNDS = 5
MAX_TOKENS = 1500

MAX_HISTORY_MESSAGES = 8


# ==========================================
# Conversation Memory
# ==========================================

conversation_memory: dict[str, list[dict]] = {}


# ==========================================
# User Profile Memory
# ==========================================

user_profiles: dict[str, dict] = {}


# ==========================================
# Tools Definition
# ==========================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "جستجوی اطلاعات واقعی و به‌روز در وب درباره "
                "پوست، مو، مراقبت پوستی، ترکیبات و موضوعات مرتبط."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "عبارت مورد جستجو"
                    }
                },
                "required": ["query"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "جستجوی محصولات واقعی پوست و مو. "
                "برای پیدا کردن محصول، برند، مشخصات، "
                "قیمت یا لینک واقعی استفاده شود."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "محصول مورد نظر"
                    },
                    "skin_type": {
                        "type": "string",
                        "description": "نوع پوست"
                    },
                    "category": {
                        "type": "string",
                        "description": "دسته محصول"
                    }
                },
                "required": ["query"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "analyze_ingredients",
            "description": (
                "تحلیل ترکیبات محصولات پوست و مو."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredients": {
                        "type": "string",
                        "description": "فهرست ترکیبات"
                    }
                },
                "required": ["ingredients"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "create_routine",
            "description": (
                "ساخت برنامه مراقبت از پوست و مو."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skin_type": {
                        "type": "string"
                    },
                    "hair_type": {
                        "type": "string"
                    },
                    "days": {
                        "type": "integer",
                        "enum": [3, 7, 14, 30]
                    }
                },
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "safety_check",
            "description": (
                "بررسی علائم هشدار پوست، مو و پوست سر."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "image_analysis": {
                        "type": "string"
                    }
                },
                "required": ["message"]
            }
        }
    }
]


# ==========================================
# Execute Tool
# ==========================================

def execute_tool(tool_name: str, arguments: dict):

    if tool_name == "search_web":
        return search_web(
            query=arguments.get("query", "")
        )

    if tool_name == "search_products":
        return search_products(
            query=arguments.get("query", ""),
            skin_type=arguments.get("skin_type"),
            category=arguments.get("category")
        )

    if tool_name == "analyze_ingredients":
        return analyze_ingredients(
            ingredients=arguments.get("ingredients", "")
        )

    if tool_name == "create_routine":
        return create_routine(
            skin_type=arguments.get("skin_type"),
            hair_type=arguments.get("hair_type"),
            days=arguments.get("days", 7)
        )

    if tool_name == "safety_check":
        return safety_check(
            message=arguments.get("message", ""),
            image_analysis=arguments.get("image_analysis")
        )

    return {
        "success": False,
        "error": f"Unknown tool: {tool_name}"
    }


# ==========================================
# Assistant Message Converter
# ==========================================

def assistant_message_to_dict(assistant_message):

    result = {
        "role": "assistant",
        "content": assistant_message.content
    }

    if assistant_message.tool_calls:

        result["tool_calls"] = []

        for tool_call in assistant_message.tool_calls:

            result["tool_calls"].append(
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
            )

    return result


# ==========================================
# Conversation Memory
# ==========================================

def save_conversation(
    user_id: str | None,
    user_message: str,
    assistant_message: str
):

    if not user_id:
        return

    if user_id not in conversation_memory:
        conversation_memory[user_id] = []

    conversation_memory[user_id].append(
        {
            "role": "user",
            "content": user_message
        }
    )

    conversation_memory[user_id].append(
        {
            "role": "assistant",
            "content": assistant_message
        }
    )

    conversation_memory[user_id] = (
        conversation_memory[user_id]
        [-MAX_HISTORY_MESSAGES:]
    )


def get_conversation_history(
    user_id: str | None
):

    if not user_id:
        return []

    return conversation_memory.get(
        user_id,
        []
    )[-MAX_HISTORY_MESSAGES:]


# ==========================================
# User Profile Memory
# ==========================================

def update_user_profile(
    user_id: str | None,
    age=None,
    skin_type=None,
    hair_type=None
):

    if not user_id:
        return

    if user_id not in user_profiles:
        user_profiles[user_id] = {}

    profile = user_profiles[user_id]

    if age is not None:
        profile["age"] = age

    if skin_type:
        profile["skin_type"] = skin_type

    if hair_type:
        profile["hair_type"] = hair_type


def get_user_profile(
    user_id: str | None
):

    if not user_id:
        return {}

    return user_profiles.get(
        user_id,
        {}
    )


# ==========================================
# Build Profile Context
# ==========================================

def build_profile_context(
    user_id: str | None
):

    profile = get_user_profile(user_id)

    if not profile:
        return ""

    context = "\n\nاطلاعات ذخیره‌شده کاربر:\n"

    if profile.get("age") is not None:
        context += f"- سن: {profile['age']}\n"

    if profile.get("skin_type"):
        context += f"- نوع پوست: {profile['skin_type']}\n"

    if profile.get("hair_type"):
        context += f"- نوع مو: {profile['hair_type']}\n"

    return context


# ==========================================
# Run Agent
# ==========================================

def run_agent(
    message: str,
    image_bytes: bytes | None = None,
    image_type: str | None = None,
    user_id: str | None = None,
    age: int | None = None,
    skin_type: str | None = None,
    hair_type: str | None = None
):

    try:

        # ======================================
        # Update User Profile
        # ======================================

        update_user_profile(
            user_id=user_id,
            age=age,
            skin_type=skin_type,
            hair_type=hair_type
        )

        # ======================================
        # User Content
        # ======================================

        user_content = [
            {
                "type": "text",
                "text": message
            }
        ]

        # ======================================
        # Image
        # ======================================

        if image_bytes:

            image_base64 = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            mime_type = (
                image_type
                or "image/jpeg"
            )

            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            f"data:{mime_type};"
                            f"base64,{image_base64}"
                        )
                    }
                }
            )

        # ======================================
        # Messages
        # ======================================

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # ======================================
        # Profile Context
        # ======================================

        profile_context = build_profile_context(
            user_id
        )

        if profile_context:

            messages.append(
                {
                    "role": "system",
                    "content": profile_context
                }
            )

        # ======================================
        # Previous Conversation
        # ======================================

        history = get_conversation_history(
            user_id
        )

        messages.extend(history)

        # ======================================
        # Current User Message
        # ======================================

        messages.append(
            {
                "role": "user",
                "content": user_content
            }
        )

        # ======================================
        # Agent Loop
        # ======================================

        for round_number in range(
            1,
            MAX_TOOL_ROUNDS + 1
        ):

            print("\n")
            print("=" * 60)
            print(f"AGENT ROUND {round_number}")
            print("=" * 60)

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=MAX_TOKENS
            )

            choice = response.choices[0]

            assistant_message = choice.message

            print(
                "FINISH REASON:",
                choice.finish_reason
            )

            # ==================================
            # Final Answer
            # ==================================

            if not assistant_message.tool_calls:

                final_answer = (
                    assistant_message.content
                )

                if not final_answer:

                    return (
                        "پاسخ معتبری از مدل "
                        "دریافت نشد."
                    )

                save_conversation(
                    user_id=user_id,
                    user_message=message,
                    assistant_message=final_answer
                )

                return final_answer

            # ==================================
            # Tool Calls
            # ==================================

            messages.append(
                assistant_message_to_dict(
                    assistant_message
                )
            )

            for tool_call in assistant_message.tool_calls:

                tool_name = (
                    tool_call.function.name
                )

                try:

                    arguments = json.loads(
                        tool_call.function.arguments
                        or "{}"
                    )

                except json.JSONDecodeError:

                    arguments = {}

                print(
                    "TOOL:",
                    tool_name
                )

                print(
                    "ARGUMENTS:",
                    arguments
                )

                try:

                    tool_result = execute_tool(
                        tool_name,
                        arguments
                    )

                except Exception as tool_error:

                    tool_result = {
                        "success": False,
                        "error": str(tool_error)
                    }

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            tool_result,
                            ensure_ascii=False
                        )
                    }
                )

        # ======================================
        # Final Attempt
        # ======================================

        final_response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=MAX_TOKENS
        )

        final_answer = (
            final_response
            .choices[0]
            .message
            .content
        )

        if final_answer:

            save_conversation(
                user_id=user_id,
                user_message=message,
                assistant_message=final_answer
            )

            return final_answer

        return (
            "Agent نتوانست پاسخ مناسبی تولید کند."
        )

    except Exception as e:

        print("\nAGENT ERROR:")
        print(repr(e))

        return (
            "متأسفانه هنگام پردازش درخواست شما "
            "مشکلی پیش آمد. لطفاً دوباره تلاش کنید."
        )