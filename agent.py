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

api_key = os.getenv("SAROVI_API_KEY")
base_url = os.getenv(
    "SAROVI_BASE_URL",
    "https://api.sarovi.ir/v1"
)
model = os.getenv(
    "SAROVI_MODEL",
    "anthropic/claude-sonnet-5"
)


if not api_key:
    raise ValueError(
        "SAROVI_API_KEY در فایل .env پیدا نشد."
    )

if not base_url:
    raise ValueError(
        "SAROVI_BASE_URL در فایل .env پیدا نشد."
    )

if not model:
    raise ValueError(
        "SAROVI_MODEL در فایل .env پیدا نشد."
    )


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


# ==========================================
# Tools Definition
# ==========================================

TOOLS = [

    # --------------------------------------
    # Web Search
    # --------------------------------------

    {
        "type": "function",
        "function": {
            "name": "search_web",

            "description": (
                "جستجوی اطلاعات واقعی و به‌روز در وب درباره "
                "پوست، مو، مراقبت پوستی، ترکیبات و موضوعات مرتبط. "
                "فقط زمانی استفاده شود که اطلاعات به‌روز یا منبع واقعی لازم است."
            ),

            "parameters": {
                "type": "object",

                "properties": {
                    "query": {
                        "type": "string",
                        "description": "عبارت مورد جستجو"
                    }
                },

                "required": [
                    "query"
                ]
            }
        }
    },


    # --------------------------------------
    # Product Search
    # --------------------------------------

    {
        "type": "function",
        "function": {
            "name": "search_products",

            "description": (
                "جستجوی محصولات واقعی پوست و مو. "
                "برای پیدا کردن محصول، برند، مشخصات، "
                "قیمت یا لینک واقعی استفاده شود. "
                "اطلاعات محصول نباید بدون نتیجه این ابزار ساخته شود."
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
                        "description": "نوع پوست در صورت مشخص بودن"
                    },

                    "category": {
                        "type": "string",
                        "description": "دسته محصول"
                    }
                },

                "required": [
                    "query"
                ]
            }
        }
    },


    # --------------------------------------
    # Ingredient Analysis
    # --------------------------------------

    {
        "type": "function",
        "function": {
            "name": "analyze_ingredients",

            "description": (
                "تحلیل ترکیبات محصولات پوست و مو. "
                "زمانی استفاده شود که کاربر لیست ترکیبات "
                "یک محصول را ارائه کرده یا درخواست تحلیل آنها را دارد."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "ingredients": {
                        "type": "string",
                        "description": "فهرست ترکیبات محصول"
                    }
                },

                "required": [
                    "ingredients"
                ]
            }
        }
    },


    # --------------------------------------
    # Routine Planner
    # --------------------------------------

    {
        "type": "function",
        "function": {
            "name": "create_routine",

            "description": (
                "ساخت چارچوب برنامه مراقبت از پوست و مو. "
                "برای درخواست برنامه‌های 3، 7، 14 یا 30 روزه استفاده شود."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "skin_type": {
                        "type": "string",
                        "description": "نوع پوست کاربر"
                    },

                    "hair_type": {
                        "type": "string",
                        "description": "نوع موی کاربر"
                    },

                    "days": {
                        "type": "integer",
                        "enum": [
                            3,
                            7,
                            14,
                            30
                        ],
                        "description": "تعداد روزهای برنامه"
                    }
                },

                "required": []
            }
        }
    },


    # --------------------------------------
    # Safety Check
    # --------------------------------------

    {
        "type": "function",
        "function": {
            "name": "safety_check",

            "description": (
                "بررسی علائم هشدار پوست، مو و پوست سر. "
                "اگر کاربر از درد شدید، خونریزی، زخم، "
                "عفونت، تورم شدید، واکنش شدید، "
                "ریزش ناگهانی مو یا علائم غیرعادی صحبت کرد "
                "از این ابزار استفاده شود."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "message": {
                        "type": "string",
                        "description": "شرح علائم یا سؤال کاربر"
                    },

                    "image_analysis": {
                        "type": "string",
                        "description": (
                            "توضیح ویژگی‌های قابل مشاهده تصویر "
                            "در صورت وجود"
                        )
                    }
                },

                "required": [
                    "message"
                ]
            }
        }
    }
]


# ==========================================
# Execute Tool
# ==========================================

def execute_tool(
    tool_name: str,
    arguments: dict
):

    if tool_name == "search_web":

        return search_web(
            query=arguments.get(
                "query",
                ""
            )
        )

    if tool_name == "search_products":

        return search_products(
            query=arguments.get(
                "query",
                ""
            ),
            skin_type=arguments.get(
                "skin_type"
            ),
            category=arguments.get(
                "category"
            )
        )

    if tool_name == "analyze_ingredients":

        return analyze_ingredients(
            ingredients=arguments.get(
                "ingredients",
                ""
            )
        )

    if tool_name == "create_routine":

        return create_routine(
            skin_type=arguments.get(
                "skin_type"
            ),
            hair_type=arguments.get(
                "hair_type"
            ),
            days=arguments.get(
                "days",
                7
            )
        )

    if tool_name == "safety_check":

        return safety_check(
            message=arguments.get(
                "message",
                ""
            ),
            image_analysis=arguments.get(
                "image_analysis"
            )
        )

    return {
        "success": False,
        "tool": tool_name,
        "error": f"Unknown tool: {tool_name}"
    }


# ==========================================
# Convert Assistant Message
# ==========================================

def assistant_message_to_dict(
    assistant_message
):

    message_dict = {
        "role": "assistant",
        "content": assistant_message.content
    }

    if assistant_message.tool_calls:

        message_dict["tool_calls"] = []

        for tool_call in assistant_message.tool_calls:

            message_dict["tool_calls"].append(
                {
                    "id": tool_call.id,

                    "type": "function",

                    "function": {
                        "name": tool_call.function.name,

                        "arguments": (
                            tool_call.function.arguments
                        )
                    }
                }
            )

    return message_dict


# ==========================================
# Run Agent
# ==========================================

def run_agent(
    message: str,
    image_bytes: bytes | None = None,
    image_type: str | None = None
):

    try:

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
            ).decode(
                "utf-8"
            )

            mime_type = (
                image_type
                or
                "image/jpeg"
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
            },

            {
                "role": "user",
                "content": user_content
            }
        ]


        # ======================================
        # Multi-Step Agent Loop
        # ======================================

        for round_number in range(
            1,
            MAX_TOOL_ROUNDS + 1
        ):

            print("\n")
            print("=" * 60)
            print(
                f"AGENT ROUND {round_number}"
            )
            print("=" * 60)

            response = (
                client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=MAX_TOKENS
                )
            )

            choice = response.choices[0]

            assistant_message = choice.message

            print(
                "FINISH REASON:",
                choice.finish_reason
            )


            # ==================================
            # No Tool Call -> Final Answer
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

                print(
                    "NO MORE TOOLS REQUIRED"
                )

                return final_answer


            # ==================================
            # Tool Calls
            # ==================================

            print("\nTOOLS CALLED:")

            messages.append(
                assistant_message_to_dict(
                    assistant_message
                )
            )


            for tool_call in (
                assistant_message.tool_calls
            ):

                tool_name = (
                    tool_call.function.name
                )


                # ------------------------------
                # Parse Arguments
                # ------------------------------

                try:

                    arguments = json.loads(
                        tool_call.function.arguments
                        or
                        "{}"
                    )

                except json.JSONDecodeError:

                    arguments = {}


                print(
                    "\nTOOL:",
                    tool_name
                )

                print(
                    "ARGUMENTS:",
                    arguments
                )


                # ------------------------------
                # Execute
                # ------------------------------

                try:

                    tool_result = execute_tool(
                        tool_name,
                        arguments
                    )

                except Exception as tool_error:

                    tool_result = {
                        "success": False,
                        "tool": tool_name,
                        "error": str(
                            tool_error
                        )
                    }


                print(
                    "TOOL SUCCESS:",
                    tool_result.get(
                        "success"
                    )
                )


                # ------------------------------
                # Add Tool Result
                # ------------------------------

                messages.append(
                    {
                        "role": "tool",

                        "tool_call_id": (
                            tool_call.id
                        ),

                        "content": json.dumps(
                            tool_result,
                            ensure_ascii=False
                        )
                    }
                )


        # ======================================
        # Maximum Tool Rounds Reached
        # ======================================

        print("\n")
        print("=" * 60)
        print(
            "MAX TOOL ROUNDS REACHED"
        )
        print("=" * 60)


        # One final request without tools.
        # Model must answer using information
        # already collected.

        final_response = (
            client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=MAX_TOKENS
            )
        )


        final_answer = (
            final_response
            .choices[0]
            .message
            .content
        )


        if final_answer:

            return final_answer


        return (
            "Agent نتوانست پاسخ نهایی "
            "مناسبی تولید کند."
        )


    # ==========================================
    # Agent Error
    # ==========================================

    except Exception as e:

        print("\n")
        print("=" * 60)
        print("AGENT ERROR")
        print("=" * 60)

        print(
            repr(e)
        )

        return (
            "متأسفانه هنگام پردازش درخواست شما "
            "مشکلی پیش آمد. لطفاً دوباره تلاش کنید."
        )