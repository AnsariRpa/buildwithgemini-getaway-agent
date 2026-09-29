# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import base64
import re
import uuid
import pathlib
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

try:
    from a2ui.basic_catalog.provider import BasicCatalog
    from a2ui.schema.manager import A2uiSchemaManager
    _HAS_A2UI_SDK = True
except ImportError:
    _HAS_A2UI_SDK = False

from google import genai
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types

from .a2ui_utils import a2ui_callback


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


MODEL = "gemini-3.6-flash"

# Hardcoded project ID for Firestore and Cloud Storage
FIRESTORE_PROJECT = "qwiklabs-gcp-03-6e0ce481a5e0"
STORAGE_BUCKET_NAME = "getaway-agent-media-qwiklabs-gcp-03-6e0ce481a5e0"
DESTINATIONS_COLLECTION = "destinations"
SANDBOX_RESOURCE_NAME = "projects/675926753631/locations/us-east1/reasoningEngines/5473929633999093760/sandboxEnvironments/7583015037422272512"


def _get_firestore_client() -> firestore.Client:
    return firestore.Client(project=FIRESTORE_PROJECT)


def list_destinations(
    max_drive_hours: Optional[float] = None,
    max_budget: Optional[float] = None,
    vibe: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List and filter getaway destinations from the catalog in Firestore.

    Args:
        max_drive_hours: Optional maximum drive time in hours to filter destinations.
        max_budget: Optional maximum estimated budget in dollars to filter destinations.
        vibe: Optional vibe/style to filter by (e.g. 'relaxation', 'adventure', 'romantic', 'nature').

    Returns:
        A list of matching destination dictionaries.
    """
    db = _get_firestore_client()
    query = db.collection(DESTINATIONS_COLLECTION)
    docs = query.stream()

    results: List[Dict[str, Any]] = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        if max_drive_hours is not None and data.get("drive_hours", 0) > max_drive_hours:
            continue
        if max_budget is not None and data.get("estimated_budget", 0) > max_budget:
            continue
        if vibe and vibe.lower() not in data.get("vibe", "").lower():
            continue

        results.append(data)

    return results


def get_destination_details(destination_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific getaway destination from Firestore.

    Args:
        destination_id: The unique ID or slug of the destination (e.g. 'sonoma-valley', 'lake-tahoe').

    Returns:
        The destination record dictionary or an error message if not found.
    """
    db = _get_firestore_client()
    doc_ref = db.collection(DESTINATIONS_COLLECTION).document(destination_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": f"Destination '{destination_id}' not found."}
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def save_destination(
    name: str,
    region: str,
    vibe: str,
    drive_hours: float,
    estimated_budget: float,
    highlights: List[str],
    description: str,
    destination_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Add or update a getaway destination in Firestore.

    Args:
        name: Name of the destination (e.g. 'Mendocino Coastal Haven').
        region: Geographic region (e.g. 'Northern Coast').
        vibe: Atmosphere or trip style (e.g. 'relaxation', 'adventure', 'romantic').
        drive_hours: Approximate drive time from the home city in hours.
        estimated_budget: Estimated weekend budget in dollars.
        highlights: Key activities or sights (list of strings).
        description: A short overview of the destination.
        destination_id: Optional slug or identifier; if omitted, generated from name.

    Returns:
        A confirmation dictionary with the saved destination details.
    """
    db = _get_firestore_client()
    doc_id = destination_id or name.lower().replace(" ", "-").replace("'", "")
    payload = {
        "id": doc_id,
        "name": name,
        "region": region,
        "vibe": vibe,
        "drive_hours": drive_hours,
        "estimated_budget": estimated_budget,
        "highlights": highlights,
        "description": description,
    }
    db.collection(DESTINATIONS_COLLECTION).document(doc_id).set(payload)
    return {"status": "success", "destination": payload}


import requests


def get_live_weather(location_name: str) -> Dict[str, Any]:
    """Fetch live real-time weather and forecast conditions for any getaway destination.

    Uses Open-Meteo public API (no API key required).

    Args:
        location_name: City or destination name (e.g. 'Lake Tahoe', 'Sonoma', 'Monterey').

    Returns:
        A dictionary with location details, temperature (°F), wind speed, and current weather description.
    """
    try:
        # Step 1: Geocode location name to latitude & longitude
        geo_resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location_name, "count": 1, "language": "en", "format": "json"},
            timeout=5,
        )
        geo_data = geo_resp.json()
        if not geo_data.get("results"):
            return {"error": f"Could not find coordinates for '{location_name}'."}

        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        resolved_name = f"{loc.get('name')}, {loc.get('admin1', '')}"

        # Step 2: Fetch current weather
        weather_resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
            },
            timeout=5,
        )
        weather_data = weather_resp.json()
        current = weather_data.get("current", {})

        # Simple WMO weather code mapping
        code = current.get("weather_code", 0)
        conditions = "Clear skies"
        if code in [1, 2, 3]:
            conditions = "Mainly clear to overcast"
        elif code in [45, 48]:
            conditions = "Foggy"
        elif code in [51, 53, 55, 61, 63, 65]:
            conditions = "Rainy / Showers"
        elif code in [71, 73, 75, 77, 85, 86]:
            conditions = "Snowy"
        elif code >= 95:
            conditions = "Thunderstorm"

        return {
            "location": resolved_name,
            "latitude": lat,
            "longitude": lon,
            "temperature_f": current.get("temperature_2m"),
            "feels_like_f": current.get("apparent_temperature"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "wind_speed_mph": current.get("wind_speed_10m"),
            "condition": conditions,
        }
    except Exception as e:
        return {"error": f"Failed to fetch weather for '{location_name}': {str(e)}"}


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def calculate_trip_budget(
    drive_hours: float,
    nights: int = 2,
    num_travelers: int = 2,
    lodging_tier: str = "moderate",
) -> Dict[str, Any]:
    """Calculate an estimated budget breakdown for a weekend getaway.

    Args:
        drive_hours: One-way driving time in hours.
        nights: Number of nights staying (default 2 for a weekend).
        num_travelers: Number of people traveling together (default 2).
        lodging_tier: Accommodation style: 'budget', 'moderate', or 'luxury'.

    Returns:
        A dictionary with estimated fuel, lodging, food/activity costs, total trip cost, and cost per person.
    """
    # Round-trip distance approx 60 mph average, 28 mpg average, $4.50/gal
    round_trip_miles = drive_hours * 60 * 2
    fuel_cost = round((round_trip_miles / 28.0) * 4.50, 2)

    tier_rates = {"budget": 120.0, "moderate": 220.0, "luxury": 450.0}
    nightly_rate = tier_rates.get(lodging_tier.lower(), 220.0)
    # Assume 1 room per 2 travelers
    rooms_needed = max(1, (num_travelers + 1) // 2)
    lodging_cost = round(nightly_rate * nights * rooms_needed, 2)

    # Food and activity daily per person ($60 budget, $100 moderate, $200 luxury)
    per_diem_rates = {"budget": 60.0, "moderate": 100.0, "luxury": 200.0}
    daily_per_person = per_diem_rates.get(lodging_tier.lower(), 100.0)
    trip_days = nights + 1
    food_activities_cost = round(daily_per_person * trip_days * num_travelers, 2)

    total_cost = round(fuel_cost + lodging_cost + food_activities_cost, 2)
    cost_per_person = round(total_cost / max(1, num_travelers), 2)

    return {
        "travelers": num_travelers,
        "nights": nights,
        "lodging_tier": lodging_tier,
        "breakdown": {
            "estimated_fuel": fuel_cost,
            "lodging": lodging_cost,
            "food_and_activities": food_activities_cost,
        },
        "total_estimated_cost": total_cost,
        "cost_per_person": cost_per_person,
    }


def check_place_facts(place_name: str) -> Dict[str, Any]:
    """Look up factual summary, background, and history about any destination or point of interest using Wikipedia.

    No API key required.

    Args:
        place_name: Name of the place, landmark, national park, or town (e.g. 'Lake Tahoe', 'Big Sur', 'Yosemite Valley').

    Returns:
        A dictionary containing the title, factual summary extract, and Wikipedia URL.
    """
    try:
        headers = {"User-Agent": "BuildWithGeminiWorkshopAgent/1.0 (travel-agent-student@workshop.google.com)"}
        # First query Wikipedia's search to find the best matching article title
        search_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": place_name,
                "srlimit": 1,
            },
            headers=headers,
            timeout=5,
        )
        search_data = search_resp.json()
        search_results = search_data.get("query", {}).get("search", [])
        if not search_results:
            return {"error": f"No Wikipedia article found for '{place_name}'."}

        title = search_results[0]["title"]

        # Fetch the introductory plain-text extract
        extract_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exintro": 1,
                "explaintext": 1,
                "titles": title,
                "redirects": 1,
            },
            headers=headers,
            timeout=5,
        )
        pages = extract_resp.json().get("query", {}).get("pages", {})
        extract = ""
        for _, page_info in pages.items():
            extract = page_info.get("extract", "")
            break

        return {
            "title": title,
            "summary": extract[:1000] + ("..." if len(extract) > 1000 else ""),
            "source_url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
        }
    except Exception as e:
        return {"error": f"Failed to fetch facts for '{place_name}': {str(e)}"}


async def generate_destination_image(
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generate a scenic getaway visual, postcard, or mood board image using Gemini and store it.

    Saves the image into ADK artifacts and uploads it to public Cloud Storage, returning the public HTTPS URL.

    Args:
        prompt: Description of the scene or destination to generate (e.g. 'Scenic sunset over Lake Tahoe emerald bay with pine trees, travel postcard style').
        tool_context: ADK ToolContext injected automatically by the runtime.

    Returns:
        A dictionary with the public image URL, artifact filename, and status.
    """
    try:
        # 1. Generate image with gemini-3.1-flash-lite-image in the global region
        genai_client = genai.Client(
            vertexai=True,
            project=FIRESTORE_PROJECT,
            location="global",
        )
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        image_bytes: Optional[bytes] = None
        mime_type = "image/jpeg"

        candidates = getattr(response, "candidates", [])
        if candidates and candidates[0].content and candidates[0].content.parts:
            for part in candidates[0].content.parts:
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not image_bytes:
            return {"error": "No image was generated by the model. Try refining the prompt."}

        # Clean prompt for filename
        slug = re.sub(r"[^a-zA-Z0-9_-]", "_", prompt[:25].strip().lower()).strip("_")
        unique_suffix = uuid.uuid4().hex[:6]
        ext = "png" if "png" in mime_type else "jpg"
        filename = f"{slug}_{unique_suffix}.{ext}"

        # 2. Save artifact with tool_context.save_artifact (shows up in Playground Artifacts panel)
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename, artifact_part)

        # 3. Upload bytes to public Cloud Storage bucket without local filesystem writes
        storage_client = storage.Client(project=FIRESTORE_PROJECT)
        bucket = storage_client.bucket(STORAGE_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{STORAGE_BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "public_url": public_url,
            "artifact_name": filename,
            "prompt": prompt,
        }
    except Exception as e:
        return {"error": f"Image generation failed: {str(e)}"}


async def generate_destination_video(
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generates a short cinematic preview video for a destination or getaway activity using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the video to the Playground's Artifacts panel and uploads it to the public Cloud Storage bucket.

    Args:
        prompt: Description of the scene or getaway experience (e.g. 'Cinematic 3-second aerial shot of turquoise alpine lake waters surrounded by pine trees at sunset').
        tool_context: ADK ToolContext injected automatically by the runtime.

    Returns:
        A dictionary with the public video URL, artifact filename, and status.
    """
    try:
        # 1. Generate video with gemini-omni-flash-preview in the global region
        genai_client = genai.Client(
            vertexai=True,
            project=FIRESTORE_PROJECT,
            location="global",
        )
        interaction = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        video_bytes: Optional[bytes] = None
        mime_type = "video/mp4"

        output_video = getattr(interaction, "output_video", None)
        if output_video and getattr(output_video, "data", None):
            raw_data = output_video.data
            video_bytes = base64.b64decode(raw_data) if isinstance(raw_data, str) else raw_data
            if getattr(output_video, "mime_type", None):
                mime_type = output_video.mime_type

        if not video_bytes:
            return {"error": "No video was generated by the model. Try refining the prompt."}

        # Clean prompt for filename
        slug = re.sub(r"[^a-zA-Z0-9_-]", "_", prompt[:25].strip().lower()).strip("_")
        unique_suffix = uuid.uuid4().hex[:6]
        filename = f"{slug}_{unique_suffix}.mp4"

        # 2. Save artifact with tool_context.save_artifact (shows up in Playground Artifacts panel)
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename, artifact_part)

        # 3. Upload bytes to public Cloud Storage bucket without local filesystem writes
        storage_client = storage.Client(project=FIRESTORE_PROJECT)
        bucket = storage_client.bucket(STORAGE_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{STORAGE_BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "public_url": public_url,
            "artifact_name": filename,
            "prompt": prompt,
        }
    except Exception as e:
        return {"error": f"Video generation failed: {str(e)}"}


_INSTRUCTION_FILE = pathlib.Path(__file__).parent / "instruction.txt"

if _HAS_A2UI_SDK:
    schema_manager = A2uiSchemaManager(
        version="0.8",
        catalogs=[BasicCatalog.get_config("0.8")],
    )

    instruction = schema_manager.generate_system_prompt(
        role_description=(
            "You are a Getaway & Weekend Travel Concierge agent. "
            "You help users discover, plan, and budget weekend getaways. "
            "CRITICAL: Always remember, track, and respect all user allergies (food, environmental, pet, medication, or severe dietary intolerances) across all conversations. "
            "Never recommend activities, restaurants, or lodging that conflict with the user's stated allergies. "
            "You also remember the user's travel preferences, budget limits, favorite regions, and facts from previous conversations to personalize your recommendations. "
            "Use your Firestore tools to list destinations and look up details, calculate trip budgets, check live weather, check facts/history about places using Wikipedia, and generate scenic destination imagery and short cinematic preview videos. "
            "You have Python code execution enabled via Agent Engine sandbox for custom calculations, complex itineraries, or data analysis."
        ),
        workflow_description="Analyze the user request, call necessary tools, and return structured A2UI when presenting destinations, itineraries, budgets, weather, or recommendations.",
        ui_description=(
            "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
            "Never nest a Card inside a Card. "
            "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
            "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
            "nothing in adk web). "
            "You may include one Image component, but only when you have a public https "
            "URL for the image (for example the URL an image tool returns after uploading "
            "to a public bucket). Set the Image url to that exact https link, for example "
            "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
            "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
            "not have a public URL, add a short Text line noting the image instead. "
            "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
            "headings and emphasis. "
            "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
            "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
        ),
        include_schema=True,
        include_examples=True,
    )
elif _INSTRUCTION_FILE.exists():
    instruction = _INSTRUCTION_FILE.read_text(encoding="utf-8")
else:
    instruction = (
        "You are a Getaway & Weekend Travel Concierge agent. "
        "You help users discover, plan, and budget weekend getaways. "
        "CRITICAL: Always remember, track, and respect all user allergies across all conversations. "
    )


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=AgentEngineSandboxCodeExecutor(sandbox_resource_name=SANDBOX_RESOURCE_NAME),
    tools=[
        PreloadMemoryTool(),
        list_destinations,
        get_destination_details,
        save_destination,
        calculate_trip_budget,
        get_live_weather,
        check_place_facts,
        generate_destination_image,
        generate_destination_video,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
