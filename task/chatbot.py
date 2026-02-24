import re
import requests
from .models import Listing, SavedListing
from django.urls import reverse
from django.utils.html import escape

OLLAMA_URL = "http://localhost:11434/api/generate"


# -------------------------------
# 1️⃣ Abuse Detection
# -------------------------------
def contains_abuse(message):
    patterns = [
        r"\b(fuck|shit|bitch|asshole|idiot|stupid)\b",
        r"\b(f+u+c+k+|s+h+i+t+)\b",
    ]
    return any(re.search(p, message, re.IGNORECASE) for p in patterns)


# -------------------------------
# 2️⃣ Room Search
# -------------------------------
def handle_room_query(message):
    msg = message.lower()

    if not re.search(r"\b(room|rooms|rent|bhk|cheapest|cheap|expensive|costliest|under)\b", msg):
        return None

    cities = Listing.objects.filter(
        status="approved",
        is_active=True,
        is_available=True
    ).exclude(city__isnull=True).exclude(city__exact="") \
     .values_list("city", flat=True).distinct()

    city_detected = None
    for city in cities:
        if city and re.search(rf"\b{re.escape(city.lower())}\b", msg):
            city_detected = city
            break

    if not city_detected:
        return {
            "type": "text",
            "message": (
                "I couldn't find that city in our current listings.\n\n"
                "Please try searching with a city available on RoomSiftay, "
                "for example: Pokhara."
            )
        }

    listings = Listing.objects.filter(
        status="approved",
        is_active=True,
        is_available=True,
        city__icontains=city_detected
    )

    price_match = re.search(r"\b\d+\b", msg)
    if price_match:
        price = int(price_match.group())
        listings = listings.filter(monthly_rent__lte=price)

    # Sorting
    if re.search(r"\b(cheapest|cheap|lowest)\b", msg):
        listings = listings.order_by("monthly_rent")
    elif re.search(r"\b(expensive|costliest|highest)\b", msg):
        listings = listings.order_by("-monthly_rent")
    else:
        listings = listings.order_by("monthly_rent")

    total = listings.count()
    listings = listings[:6]

    if total == 0:
        return {
            "type": "text",
            "message": (
                "I couldn't find any rooms matching your criteria right now.\n\n"
                "You may try adjusting your price range or removing some filters."
            )
        }

    return {
        "type": "room_results",
        "city": city_detected,
        "total": total,
        "listings": [
            {
                "id": l.id,
                "title": l.title,
                "city": l.city,
                "rent": l.monthly_rent,
            }
            for l in listings
        ]
    }


# -------------------------------
# 3️⃣ Saved Listings
# -------------------------------
def handle_saved_listing(user):
    saved = SavedListing.objects.filter(
        user=user,
        listing__status="approved",
        listing__is_active=True,
        listing__is_available=True
    )

    count = saved.count()

    if count == 0:
        return {
            "type": "text",
            "message": "You currently do not have any active saved listings."
        }

    return {
        "type": "text",
        "message": (
            f"You have {count} active saved listing(s).\n\n"
            "You can view them in the 'Saved Listings' section of your dashboard."
        )
    }


# -------------------------------
# 4️⃣ Scripted Platform Responses
# -------------------------------
def scripted_response(message, user, mode):
    msg = message.lower()

    # Greeting
    if re.search(r"\b(hi|hello|hey|good morning|good evening)\b", msg):
        return {
            "type": "text",
            "message": (
                "Hello 👋 Welcome to RoomSiftay!\n\n"
                "I'm here to help you find rooms, check saved listings, "
                "learn about verification, or guide you through the platform.\n\n"
                "How can I assist you today?"
            )
        }

    # Help
    if "help" in msg:
        return {
            "type": "text",
            "message": (
                "Here are some things you can ask me:\n\n"
                "- room in pokhara\n"
                "- cheapest room in pokhara\n"
                "- room under 8000\n"
                "- how to add listing\n"
                "- how to verify account\n"
                "- show my saved listings"
            )
        }

    # About platform
    if "what is roomsiftay" in msg:
        return {
            "type": "text",
            "message": (
                "RoomSiftay is a Nepal-based rental platform that connects "
                "verified property owners and tenants with smart search features."
            )
        }

    # Chat with owner
    if re.search(r"\b(owner)\b.*\b(chat|message)\b|\b(chat|message)\b.*\bowner\b", msg):
        return {
            "type": "text",
            "message": (
                "Yes 😊 Owners and buyers can communicate directly through RoomSiftay.\n\n"
                "When a buyer opens a listing, they can click the 'Chat with Owner' "
                "button to start a conversation. The owner can then reply from their chat dashboard.\n\n"
                "This helps both parties discuss property details, availability, and other questions."
            )
        }

    if "verify" in msg:
        if mode == "owner":
            return {
                "type": "text",
                "message": (
                    "To verify your owner account, please follow these steps:\n\n"
                    "1. Go to the Verification page.\n"
                    "2. Upload your citizenship document.\n"
                    "3. Wait for admin approval.\n\n"
                    "Once approved, your listings will be marked as verified."
                )
            }

        return {
            "type": "text",
            "message": (
                "At the moment, verification is required only for property owners.\n\n"
                "If you plan to list a property in the future, you will need to complete the verification process."
            )
        }

    # Add listing
    if "add listing" in msg or "how to list" in msg:
        if mode == "owner":
            return {
                "type": "text",
                "message": (
                    "To add a new listing:\n\n"
                    "1. Go to the Owner Dashboard.\n"
                    "2. Click 'Add New Listing'.\n"
                    "3. Fill in the property details and submit."
                )
            }
        return {
            "type": "text",
            "message": "Only registered owners can add property listings."
        }

    return None


# -------------------------------
# 5️⃣ LLM Fallback
# -------------------------------
def ask_llm(message):
    prompt = f"""
    You are RoomSiftay Assistant.

    Only describe features that actually exist:
    - Room search
    - Saved listings
    - Owner verification
    - Chat between buyer and owner
    - Website Review
    - Report Issue
    - Owner Add Listing
    - Room search by map, own location
    - Generate password even after logging with Gmail 
    - Website details in about us or starting page

    Do NOT mention payments, transactions, or features not built.
    Do NOT write unnecessary answer.
    Be polite and professional.

    User question: {message}
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "phi",
            "prompt": prompt,
            "stream": False,
        },
    )

    return {
        "type": "text",
        "message": response.json().get(
            "response",
            "I'm sorry, I couldn't process that request at the moment."
        )
    }


# -------------------------------
# 6️⃣ Main Router
# -------------------------------
def process_message(message, user, mode="buyer", lat=None, lng=None):
    msg = message.lower().strip()

    # Abuse
    if contains_abuse(msg):
        return {
            "type": "text",
            "message": "Please use respectful language. I'm here to help you."
        }

    # Scripted responses
    scripted = scripted_response(msg, user, mode)
    if scripted:
        return scripted

    # Saved listings
    if re.search(r"\bsaved\b", msg):
        return handle_saved_listing(user)

    # Room search
    room_result = handle_room_query(msg)
    if room_result:
        return room_result

    # Soft restriction
    if not re.search(r"\b(room|rent|listing|owner|verify|add|contact|report)\b", msg):
        return {
            "type": "text",
            "message": (
                "I'm here to assist with RoomSiftay rental-related questions 😊\n\n"
                "You can ask about rooms, pricing, verification, or saved listings."
            )
        }

    return ask_llm(msg)