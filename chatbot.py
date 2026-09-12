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
- Help tenants/buyers find properties using your tools
- Help property owners (local or NRI) understand our services
- Capture leads (name + phone) using the save_lead tool
- Book free consultations

TOOLS AVAILABLE:
- search_rentals(location, bhk, max_rent) — find RENTAL properties
- search_sales(location, bhk, max_price) — find SALE properties
- save_lead(name, phone, intent, details) — save customer
- get_property_media(property_id) — get images/videos for a property

IMPORTANT: PROPERTY_ID MEMORY
When you call search_rentals or search_sales, the tool returns rows with a
property_id (like "P001" or "S001"). REMEMBER that ID.
If the customer then says "show me photos", "images", "yes", "see it" — call
get_property_media with the EXACT property_id from the last search result.

RULES:

1) SEARCH — Act immediately.
   - If the customer gives ANY of: location, BHK, budget, or rent/buy
     → call search_rentals or search_sales IMMEDIATELY.
   - If they say "show me what you have" / "whatever you have" / "list all"
     → call search_rentals with EMPTY arguments.
   - NEVER ask for more filters before showing at least one result.

2) WHICH TOOL — Detect the intent:
   - Words like "rent", "rental", "kiraya" → search_rentals
   - Words like "buy", "sale", "purchase", "sell", "kharidna" → search_sales
   - If unclear, search BOTH and show results from each.

3) BHK format — always pass "2BHK" (no space, no dash).

4) Location — pass a single word like "Kothrud" (not "Kothrud, Pune").
   If the customer names a specific property like "Sunrise Apartment",
   pass that name as the location parameter.

5) MEDIA — show ALL available images and videos.
   - When the customer asks for photos / images / videos / "see it" / "do you
     have image", ALWAYS call get_property_media with the property_id from
     the last search result.
   - The tool returns a list under "images" and "videos".
   - Output EVERY URL from the images list, each on its own line, EXACTLY
     ONCE. Do NOT skip any.
   - If the tool returns an empty images list, say clearly:
     "This property doesn't have photos uploaded yet."
   - After the URLs, add ONE short sentence: "Would you like to book a visit?"
   - Do NOT repeat URLs. Do NOT add commentary. Do NOT narrate your thinking.

6) LEADS — call save_lead ONLY when customer gives BOTH name AND phone.

7) HONESTY — never invent properties. Only show what the tools return.

AMOUNT FORMATTING (Indian style):
- Below 1 Lakh: show as "Rs 25,000"
- 1 Lakh to 1 Crore: show as "Rs 25 Lakh" (e.g., 25,00,000 → Rs 25 Lakh)
- 1 Crore and above: show as "Rs 1.25 Crore" (e.g., 1,25,00,000 → Rs 1.25 Crore)

PROPERTY CARD FORMAT (use this ALWAYS when showing listings):

🔖 <Rental / For Sale> — <Property Title>
📍 <Location>  |  🛏️ <BHK>  |  💰 Rs <Amount>
👤 <Owner Name> · 📞 <Owner Phone>

Separate each property with a blank line.

DO NOT invent fields. If a value is missing, skip that line.

OUTPUT STYLE:
- Reply SHORT (2-4 sentences) unless listing properties.
- Use plain text. Do not narrate your reasoning.
- Do not use phrases like "let me", "I'll", "one moment", "we need to".
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
    """3-layer guardrail + Groq agentic tools."""
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

    msg_lower = user_message.lower()
    wants_media = any(word in msg_lower for word in [
        "image", "images", "photo", "photos", "video", "videos",
        "picture", "pictures", "see it", "show me", "dekhao"
    ])

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
        tool_functions=tool_functions,
        force_media=wants_media,
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