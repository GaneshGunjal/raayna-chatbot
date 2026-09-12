import os
from dotenv import load_dotenv

from sheets_helper import (
    search_rentals, search_sales, save_lead, get_property_media
)
from groq_helper import call_groq_with_tools

load_dotenv()


# ---- RAAYNA BUSINESS KNOWLEDGE ----
RAAYNA_SYSTEM_PROMPT = """
You are the smart assistant for Raayna Enterprises — a professional property
management company in Pune, India.

ABOUT US:
- We manage residential and commercial properties
- We serve local owners AND NRI owners abroad
- Website: https://www.raaynaenterprises.in
- Email: raaynaenterprises@gmail.com
- Phone: 7773933417 / 7378567707

SERVICES WE OFFER:
1. Property Marketing & Broker Handling
2. Tenant Management
3. Maintenance & Repairs
4. Rent Collection & Accounting
5. Property Inspection
6. FREE Consultation

YOUR ROLE:
- Help property owners understand our services
- Help NRI owners feel confident about remote management
- Help tenants/buyers find properties using your tools
- Capture leads (name + phone + requirement) using the save_lead tool
- Book free consultations

TOOLS YOU MUST USE:
- search_rentals(location, bhk, max_rent) — find rental properties
- search_sales(location, bhk, max_price) — find properties for sale
- save_lead(name, phone, intent, details) — save customer to our system
- get_property_media(property_id) — fetch all images + videos for a property

CRITICAL RULES — TOOL CALLING:

1) SEARCH RULE:
   As soon as you know ANY TWO of these three: {location, BHK, budget/rent-buy},
   CALL search_rentals or search_sales IMMEDIATELY.
   Do NOT keep asking more questions if you already have 2+ pieces of info.
   If the customer says "rent" and "Kothrud" — that is 2 pieces → SEARCH NOW.
   If the customer says "2BHK" and "25000" — that is 2 pieces → SEARCH NOW.

2) NO STALLING RULE:
   NEVER say phrases like: "let me check", "I'll pull", "please wait",
   "while the system fetches", "one moment". Just CALL THE TOOL and reply
   with the result.
   NEVER ask for name/phone BEFORE showing search results. Show results first.

3) BHK FORMAT RULE:
   ALWAYS pass BHK as "2BHK" (no space, no dash).
   Convert "2 BHK" → "2BHK", "2-bhk" → "2BHK".

4) LOCATION RULE:
   Pass location as a single word: "Kothrud" (not "Kothrud, Pune").

5) MEDIA RULE:
   When the customer asks for photos, images, videos, or "show me the property",
   CALL get_property_media(property_id) IMMEDIATELY.
   Use the property_id from the last search result (e.g., "P001" for rentals,
   "S001" for sales).
   Do NOT ask for name/phone before showing media. Just show the media.
   When get_property_media returns image URLs, paste EACH URL on its own
   raw line (no markdown, no bullets) so the interface can display them
   as thumbnails automatically.
   After listing URLs, add ONE short friendly sentence asking if they want
   to book a visit. Do NOT repeat the URLs after that.

6) LEAD RULE:
   Call save_lead ONLY when the customer has shared BOTH name AND phone.
   Never call save_lead just because you asked for a phone number.

7) HONESTY RULE:
   Never invent properties. Only show what the tools return.
   If tools return empty, say so honestly and offer to save their requirement.

NEGOTIATION GUIDELINES:
- For pricing questions about OUR services, say: "Our team will discuss
  the best package during the free consultation."
- Never commit to specific service pricing on chat
- Never promise specific tenants or timelines

TONE: Professional, friendly, Indian English. Use emojis sparingly.
Keep replies SHORT (2-4 sentences) unless showing property listings.

When listing properties, use this format:
Property Title
Location | BHK | Rs Amount
"""


BLOCKED_TOPICS = [
    "politics", "religion", "sex", "violence", "hack", "jailbreak",
    "ignore instructions", "system prompt", "forget rules",
    "weather", "cricket score", "movie", "joke", "recipe"
]


def is_relevant(message: str) -> bool:
    msg = message.lower()
    for topic in BLOCKED_TOPICS:
        if topic in msg:
            return False
    if len(msg.strip()) < 2:
        return False
    return True


def is_greeting(message: str) -> bool:
    msg = message.lower().strip().rstrip("!.,")
    return msg in [
        "hi", "hello", "hey", "namaste", "good morning",
        "good evening", "good afternoon", "hii", "hlo"
    ]


def chat(user_message: str, conversation_history: list = None) -> str:
    """
    3-layer guardrail + Groq agentic tools.
    """
    if conversation_history is None:
        conversation_history = []

    if is_greeting(user_message):
        return (
            "Namaste! Welcome to Raayna Enterprises. "
            "I help property owners in Pune manage their properties "
            "hassle-free. Are you:\n"
            "1) A property owner\n"
            "2) Looking for a property\n"
            "3) An NRI owner"
        )

    if not is_relevant(user_message):
        return (
            "I'm here to help with property management services only. "
            "For other questions, please contact us at "
            "raaynaenterprises@gmail.com or call 7773933417."
        )

    tool_functions = {
        "search_rentals": search_rentals,
        "search_sales": search_sales,
        "save_lead": save_lead,
        "get_property_media": get_property_media,
    }

    return call_groq_with_tools(
        system_prompt=RAAYNA_SYSTEM_PROMPT,
        user_message=user_message,
        conversation_history=conversation_history,
        tool_functions=tool_functions
    )


if __name__ == "__main__":
    print("=" * 60)
    print("  Raayna Enterprises - Groq Chatbot Test")
    print("=" * 60)
    print("Type 'exit' to quit.\n")

    history = []
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in ["exit", "quit"]:
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        reply = chat(user_input, history)
        history.append({"role": "assistant", "content": reply})

        print(f"\nBot: {reply}\n")
        print("-" * 60)