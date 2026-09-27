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

import base64
import datetime
import json
import math
import os
import urllib.parse
import urllib.request
import uuid
from zoneinfo import ZoneInfo

from google import genai
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import storage
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback



PROJECT_ID = "qwiklabs-gcp-01-33c05f9db6da"
GCS_BUCKET_NAME = "stargazer-cosmic-guide-qwiklabs-gcp-01-33c05f9db6da"


from app.firestore_tools import (
    add_or_update_celestial_object,
    get_celestial_object_details,
    search_celestial_objects,
)


def get_astronomy_picture_of_the_day(date: str = "") -> str:
    """Fetches NASA's Astronomy Picture of the Day (APOD) metadata, including image URL, title, and explanation.

    Args:
        date: Optional date string in 'YYYY-MM-DD' format (e.g. '2026-09-27'). Leave empty for today's picture.

    Returns:
        Formatted string containing the APOD title, image URL, date, copyright, and summary explanation.
    """
    try:
        api_key = os.environ.get("NASA_API_KEY", "DEMO_KEY")
        url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
        if date and date.strip():
            url += f"&date={date.strip()}"

        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        title = data.get("title", "NASA Astronomy Picture of the Day")
        img_url = data.get("hdurl") or data.get("url", "")
        media_type = data.get("media_type", "image")
        apod_date = data.get("date", "")
        explanation = data.get("explanation", "")
        copyright_info = data.get("copyright", "Public Domain / NASA")

        if len(explanation) > 300:
            explanation = explanation[:297] + "..."

        return (
            f"--- NASA Astronomy Picture of the Day ({apod_date}) ---\n"
            f"Title: {title}\n"
            f"Media Type: {media_type}\n"
            f"Image URL: {img_url}\n"
            f"Credit/Copyright: {copyright_info}\n"
            f"Explanation: {explanation}"
        )

    except Exception as e:
        return f"Error fetching NASA APOD data: {e}"


def get_stargazing_conditions(location: str) -> str:
    """Fetches real-time cloud cover, temperature, humidity, and stargazing visibility for a given location.

    Args:
        location: City or place name (e.g. 'San Francisco', 'Tokyo', 'London', 'Santiago').

    Returns:
        A formatted summary of current stargazing weather conditions and a viewing recommendation.
    """
    try:
        encoded_loc = urllib.parse.quote(location.strip())
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_loc}&count=1"
        with urllib.request.urlopen(geo_url, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode())

        results = geo_data.get("results")
        if not results:
            return f"Location '{location}' could not be found for stargazing weather lookup."

        place = results[0]
        name = place.get("name")
        country = place.get("country", "")
        lat = place.get("latitude")
        lon = place.get("longitude")

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,cloud_cover,visibility"
        )
        with urllib.request.urlopen(weather_url, timeout=5) as resp:
            w_data = json.loads(resp.read().decode())

        current = w_data.get("current", {})
        cloud_cover = current.get("cloud_cover", 0)
        temp_c = current.get("temperature_2m", 0)
        humidity = current.get("relative_humidity_2m", 0)
        visibility_m = current.get("visibility", 0)
        visibility_km = round(visibility_m / 1000.0, 1) if visibility_m else 0

        if cloud_cover < 20:
            rating = "EXCELLENT (Clear skies)"
        elif cloud_cover < 50:
            rating = "FAIR (Partly cloudy)"
        else:
            rating = "POOR (Heavy cloud cover)"

        return (
            f"--- Stargazing Weather for {name}, {country} ---\n"
            f"Stargazing Suitability: {rating}\n"
            f"Cloud Cover: {cloud_cover}%\n"
            f"Temperature: {temp_c}°C ({round(temp_c * 9/5 + 32, 1)}°F)\n"
            f"Relative Humidity: {humidity}%\n"
            f"Atmospheric Visibility: {visibility_km} km\n"
            f"Coordinates: {lat:.2f}°N, {lon:.2f}°E"
        )

    except Exception as e:
        return f"Error retrieving stargazing conditions for '{location}': {e}"


def calculate(expression: str) -> str:
    """Evaluates a mathematical arithmetic or optical physics expression safely.

    Args:
        expression: Mathematical expression to evaluate, e.g. '1200 / 10' or 'sqrt(16)'.

    Returns:
        The calculated result as a string.
    """
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed_names.update({"abs": abs, "round": round, "min": min, "max": max, "pow": pow})

    clean_expr = expression.replace("^", "**")
    try:
        result = eval(clean_expr, {"__builtins__": None}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating expression '{expression}': {e}"


def get_near_earth_asteroids(date: str = "") -> str:
    """Fetches Near-Earth Objects (asteroids) making close approaches to Earth via NASA's NeoWs API.

    Args:
        date: Date string in 'YYYY-MM-DD' format (e.g. '2026-09-27'). Defaults to today if left empty.

    Returns:
        Formatted list of near-Earth asteroids, their estimated sizes, close approach distances, and hazard status.
    """
    try:
        api_key = os.environ.get("NASA_API_KEY", "DEMO_KEY")
        target_date = date.strip() if date and date.strip() else datetime.date.today().strftime("%Y-%m-%d")
        url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={target_date}&end_date={target_date}&api_key={api_key}"

        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        neo_dict = data.get("near_earth_objects", {})
        neos = neo_dict.get(target_date, [])
        element_count = data.get("element_count", len(neos))

        if not neos:
            return f"No tracked Near-Earth Objects found for date {target_date}."

        lines = [
            f"--- NASA Near-Earth Objects / Close Approaches ({target_date}) ---",
            f"Total Tracked Asteroids Today: {element_count}\n",
        ]

        for neo in neos[:5]:
            name = neo.get("name", "Unknown Asteroid")
            dia = neo.get("estimated_diameter", {}).get("meters", {})
            min_d = dia.get("estimated_diameter_min", 0)
            max_d = dia.get("estimated_diameter_max", 0)
            ca_list = neo.get("close_approach_data", [])
            miss_km_str = "N/A"
            relative_velocity_kmh = "N/A"
            if ca_list:
                ca = ca_list[0]
                miss_km = ca.get("miss_distance", {}).get("kilometers")
                if miss_km:
                    miss_km_str = f"{float(miss_km):,.0f}"
                vel_kmh = ca.get("relative_velocity", {}).get("kilometers_per_hour")
                if vel_kmh:
                    relative_velocity_kmh = f"{float(vel_kmh):,.0f}"

            is_hazard = neo.get("is_potentially_hazardous_asteroid", False)
            hazard_flag = "⚠️ YES (Potentially Hazardous)" if is_hazard else "NO (Safe pass)"

            lines.append(
                f"• Asteroid {name}:\n"
                f"  - Est. Diameter: {min_d:.1f} - {max_d:.1f} meters\n"
                f"  - Close Approach Distance: {miss_km_str} km\n"
                f"  - Relative Velocity: {relative_velocity_kmh} km/h\n"
                f"  - Potentially Hazardous: {hazard_flag}"
            )

        return "\n".join(lines)

    except Exception as e:
        return f"Error retrieving Near-Earth Objects from NASA NeoWs API: {e}"


def get_iss_location() -> str:
    """Fetches real-time position, altitude, velocity, and visibility state of the International Space Station (ISS).

    Returns:
        Formatted summary of ISS coordinates, orbital altitude, velocity, and visibility state.
    """
    try:
        url = "https://api.wheretheiss.at/v1/satellites/25544"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        lat = data.get("latitude", 0)
        lon = data.get("longitude", 0)
        alt_km = round(data.get("altitude", 0), 1)
        vel_kmh = round(data.get("velocity", 0), 1)
        visibility = data.get("visibility", "unknown")

        return (
            f"--- International Space Station (ISS) Real-Time Location ---\n"
            f"Coordinates: {lat:.4f}°, {lon:.4f}°\n"
            f"Altitude: {alt_km} km\n"
            f"Velocity: {vel_kmh:,.1f} km/h\n"
            f"Visibility state: {visibility.title()}"
        )

    except Exception as e:
        return f"Error fetching ISS location data: {e}"


def geocode_address(address: str) -> str:
    """Turns an address, landmark, or city name into latitude and longitude coordinates using Google Maps Geocoding API.

    Args:
        address: The address or place name to geocode (e.g., 'Mauna Kea Observatory, Hawaii').

    Returns:
        Formatted summary with address and latitude/longitude coordinates.
    """
    try:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY", os.environ.get("NASA_API_KEY", ""))
        if not api_key:
            return "Error: GOOGLE_MAPS_API_KEY is not set in environment."

        encoded_address = urllib.parse.quote(address.strip())
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        status = data.get("status", "")
        if status != "OK":
            err_msg = data.get("error_message", f"API returned status '{status}'")
            return f"Geocoding failed for '{address}': {err_msg}"

        results = data.get("results", [])
        if not results:
            return f"No geocoding results found for '{address}'."

        first = results[0]
        formatted_address = first.get("formatted_address", address)
        location = first.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")

        return (
            f"--- Geocoding Result ---\n"
            f"Address: {formatted_address}\n"
            f"Coordinates: Latitude {lat}, Longitude {lng}"
        )

    except Exception as e:
        return f"Error executing Geocoding lookup for '{address}': {e}"


def find_nearby_places(latitude: float, longitude: float, place_type: str = "park", radius: float = 5000.0) -> str:
    """Finds nearby places of a given type around coordinates using Google Places API (New).

    Args:
        latitude: Latitude of the search location center.
        longitude: Longitude of the search location center.
        place_type: Type of place to search for (e.g., 'park', 'tourist_attraction', 'museum', 'campground').
        radius: Search radius in meters (default is 5000.0 meters).

    Returns:
        Formatted list of nearby places with name, formatted address, and location coordinates.
    """
    try:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY", os.environ.get("NASA_API_KEY", ""))
        if not api_key:
            return "Error: GOOGLE_MAPS_API_KEY is not set in environment."

        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
        }
        body = {
            "includedTypes": [place_type.strip().lower()],
            "maxResultCount": 10,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                    },
                    "radius": float(radius),
                }
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        places = data.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found within {radius}m of ({latitude}, {longitude})."

        lines = [f"--- Nearby Places ({place_type.title()}) within {radius}m ---"]
        for place in places:
            name = place.get("displayName", {}).get("text", "Unknown Name")
            address = place.get("formattedAddress", "Address Unavailable")
            loc = place.get("location", {})
            lat = loc.get("latitude", "N/A")
            lng = loc.get("longitude", "N/A")

            lines.append(
                f"• Name: {name}\n"
                f"  Address: {address}\n"
                f"  Location: ({lat}, {lng})"
            )

        return "\n".join(lines)

    except urllib.error.HTTPError as he:
        try:
            err_data = json.loads(he.read().decode())
            err_detail = err_data.get("error", {}).get("message", str(he))
        except Exception:
            err_detail = str(he)
        return f"Google Places API Error ({he.code}): {err_detail}"
    except Exception as e:
        return f"Error executing Nearby Places search: {e}"



async def generate_astrophotography_image(
    prompt: str,
    tool_context: ToolContext = None,
) -> str:
    """Generates a deep-space astrophotography concept or telescopic view image (nebula, galaxy, star cluster, planet) using gemini-3.1-flash-lite-image in global region.

    Args:
        prompt: Description of the celestial object or deep-space scene to generate (e.g., 'Andromeda Galaxy', 'Orion Nebula', 'Ring Nebula M57', 'Saturn with rings').
        tool_context: ADK ToolContext injected automatically by the agent runner to save artifacts.

    Returns:
        Public Cloud Storage HTTPS URL of the generated image.
    """
    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
        full_prompt = (
            f"Deep-space astrophotography view of {prompt}. High resolution, vivid cosmic colors, astronomical details."
        )

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=full_prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

        image_bytes = None
        mime_type = "image/jpeg"
        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
        ):
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not image_bytes:
            return f"Failed to generate image bytes for '{prompt}'."

        filename = f"astro_{uuid.uuid4().hex[:8]}.jpg"

        # (1) Save artifact in ToolContext for Playground Artifacts panel
        if tool_context:
            try:
                artifact_part = types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                )
                await tool_context.save_artifact(
                    filename=filename,
                    artifact=artifact_part,
                )
            except Exception as artifact_err:
                print(f"Warning: Failed to save artifact in tool_context: {artifact_err}")

        # (2) Upload directly to public Cloud Storage bucket
        gcs_client = storage.Client(project=PROJECT_ID)
        bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        return public_url

    except Exception as e:
        return f"Error generating astrophotography image for '{prompt}': {e}"


async def generate_astrophotography_video(
    prompt: str,
    tool_context: ToolContext = None,
) -> str:
    """Generates a short cosmic video clip of a celestial object or astronomical event using Google's Omni model (gemini-omni-flash-preview) in global region.

    Args:
        prompt: Description of the celestial object or cosmic scene to generate a video for (e.g. 'Spinning view of Saturn and its rings', 'Orbiting around Andromeda Galaxy', 'Supernova explosion in deep space').
        tool_context: ADK ToolContext injected automatically by the agent runner to save artifacts.

    Returns:
        Public Cloud Storage HTTPS URL of the generated video.
    """
    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
        full_prompt = (
            f"Cinematic astronomical video of {prompt}. Smooth motion, vivid deep-space detail, high resolution."
        )

        video_bytes = None
        mime_type = "video/mp4"

        try:
            interaction = client.interactions.create(
                model="gemini-omni-flash-preview",
                input=full_prompt,
                response_format={"type": "video"},
            )
            if hasattr(interaction, "output_video") and interaction.output_video:
                raw_data = getattr(interaction.output_video, "data", None) or getattr(interaction.output_video, "bytes", None)
                if isinstance(raw_data, str):
                    video_bytes = base64.b64decode(raw_data)
                elif isinstance(raw_data, bytes):
                    video_bytes = raw_data
                if getattr(interaction.output_video, "mime_type", None):
                    mime_type = interaction.output_video.mime_type
            elif hasattr(interaction, "outputs") and interaction.outputs:
                for out in interaction.outputs:
                    raw_data = getattr(out, "data", None) or getattr(out, "bytes", None)
                    if raw_data:
                        if isinstance(raw_data, str):
                            video_bytes = base64.b64decode(raw_data)
                        elif isinstance(raw_data, bytes):
                            video_bytes = raw_data
                        break
        except Exception as inter_err:
            print(f"Interactions API video generation error: {inter_err}")

        if not video_bytes:
            return f"Failed to generate video bytes for '{prompt}'."

        filename = f"astro_video_{uuid.uuid4().hex[:8]}.mp4"

        # (1) Save artifact in ToolContext for Playground Artifacts panel
        if tool_context:
            try:
                artifact_part = types.Part.from_bytes(
                    data=video_bytes,
                    mime_type=mime_type,
                )
                await tool_context.save_artifact(
                    filename=filename,
                    artifact=artifact_part,
                )
            except Exception as artifact_err:
                print(f"Warning: Failed to save artifact in tool_context: {artifact_err}")

        # (2) Upload directly to public Cloud Storage bucket
        gcs_client = storage.Client(project=PROJECT_ID)
        bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        return public_url

    except Exception as e:
        return f"Error generating astrophotography video for '{prompt}': {e}"


# Load Agent Engine resource name from deployment_metadata.json if available
_agent_engine_resource_name = None
_metadata_path = os.path.join(os.path.dirname(__file__), "..", "deployment_metadata.json")
if os.path.exists(_metadata_path):
    try:
        with open(_metadata_path, "r") as f:
            _meta = json.load(f)
            _agent_engine_resource_name = _meta.get("remote_agent_runtime_id") or _meta.get("agent_engine_resource_name")
    except Exception as e:
        print(f"Warning: Could not read deployment_metadata.json: {e}")

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=_agent_engine_resource_name
)


# WRITE: after each turn, send the session events to Memory Bank for extraction
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


a2ui_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = a2ui_schema_manager.generate_system_prompt(
    role_description=(
        "You are the Stargazer & Cosmic Guide assistant. You help stargazers and amateur "
        "astronomers explore the cosmos, look up sky targets, check live stargazing weather conditions, "
        "fetch NASA Astronomy Pictures of the Day (APOD), track near-Earth asteroids and ISS passes/location, "
        "generate AI astrophotography concept images of celestial targets, geocode addresses to coordinates, "
        "find nearby observation locations/parks, perform optical calculations, and manage a Firestore catalog of celestial objects. "
        "You remember user preferences, facts, and ALL user allergies or dietary/medical restrictions across sessions using your Memory Bank. "
        "Always pay special attention to remembering any allergies mentioned by the user, storing them, and taking them into account during all interactions."
    ),
    workflow_description=(
        "Analyze the user's request and return structured UI when appropriate.\n"
        "Always use your available tools when needed:\n"
        "- get_astronomy_picture_of_the_day: to fetch NASA's APOD image link, title, and explanation.\n"
        "- get_stargazing_conditions: to check live weather, cloud cover, and viewing suitability for any city.\n"
        "- get_near_earth_asteroids: to check close-approach Near-Earth Objects (asteroids) and space hazards for a date.\n"
        "- get_iss_location: to fetch real-time ISS latitude, longitude, altitude, velocity, and visibility state.\n"
        "- generate_astrophotography_image: to generate a deep-space astrophotography image using gemini-3.1-flash-lite-image and return a public HTTPS URL.\n"
        "- generate_astrophotography_video: to generate a short cosmic video clip using gemini-omni-flash-preview and return a public HTTPS URL.\n"
        "- geocode_address: to turn an address or landmark into latitude and longitude coordinates.\n"
        "- find_nearby_places: to search nearby places of a given type around coordinates using Google Places API (New).\n"
        "- search_celestial_objects, get_celestial_object_details, add_or_update_celestial_object: to query or save catalog objects in Firestore.\n"
        "- calculate: for telescope optical or mathematical calculations."
    ),
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


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        get_astronomy_picture_of_the_day,
        get_stargazing_conditions,
        get_near_earth_asteroids,
        get_iss_location,
        generate_astrophotography_image,
        generate_astrophotography_video,
        geocode_address,
        find_nearby_places,
        search_celestial_objects,
        get_celestial_object_details,
        add_or_update_celestial_object,
        calculate,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

