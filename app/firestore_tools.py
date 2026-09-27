"""Firestore database interface and function tools for Stargazer & Cosmic Guide."""

from typing import Any, Dict, List, Optional
from google.cloud import firestore

# Hardcoded GCP Project ID (Agent Platform requires explicit project ID string)
PROJECT_ID = "qwiklabs-gcp-01-33c05f9db6da"
COLLECTION_NAME = "celestial_objects"

# Initialize Firestore client with hardcoded project ID
db = firestore.Client(project=PROJECT_ID)


def search_celestial_objects(
    query: str = "",
    constellation: str = "",
    object_type: str = "",
) -> str:
    """Searches the Firestore catalog of celestial objects by name, catalog ID, constellation, or object type.

    Args:
        query: Optional keyword search for object name or catalog ID (e.g. 'Andromeda', 'M42', 'Galaxy').
        constellation: Optional filter for constellation name (e.g. 'Orion', 'Andromeda', 'Taurus').
        object_type: Optional filter for object type (e.g. 'Spiral Galaxy', 'Open Star Cluster', 'Planet').

    Returns:
        Formatted string containing matching celestial objects from the database.
    """
    try:
        collection_ref = db.collection(COLLECTION_NAME)
        docs = collection_ref.stream()

        results = []
        q_lower = query.lower().strip()
        const_lower = constellation.lower().strip()
        type_lower = object_type.lower().strip()

        for doc in docs:
            data = doc.to_dict()
            doc_id = doc.id
            name = str(data.get("name", "")).lower()
            cat_id = str(data.get("catalog_id", "")).lower()
            doc_const = str(data.get("constellation", "")).lower()
            doc_type = str(data.get("type", "")).lower()
            desc = str(data.get("description", "")).lower()

            if q_lower and (q_lower not in name and q_lower not in cat_id and q_lower not in desc and q_lower not in doc_id):
                continue
            if const_lower and const_lower not in doc_const:
                continue
            if type_lower and type_lower not in doc_type:
                continue

            results.append(data)

        if not results:
            return f"No celestial objects found in Firestore matching query='{query}', constellation='{constellation}', type='{object_type}'."

        formatted_output = [f"Found {len(results)} object(s) in Firestore collection '{COLLECTION_NAME}':\n"]
        for item in results:
            formatted_output.append(
                f"• {item.get('name')} [{item.get('catalog_id')}] - ID: {item.get('object_id')}\n"
                f"  Type: {item.get('type')} | Constellation: {item.get('constellation')}\n"
                f"  Magnitude: {item.get('apparent_magnitude')} | Best Season: {item.get('best_season')} | Min Aperture: {item.get('min_aperture_mm')}mm\n"
                f"  Coordinates: {item.get('coordinates')}\n"
                f"  Description: {item.get('description')}\n"
            )

        return "\n".join(formatted_output)

    except Exception as e:
        return f"Error querying Firestore collection '{COLLECTION_NAME}': {e}"


def get_celestial_object_details(object_id: str) -> str:
    """Retrieves full details for a specific celestial object from Firestore by its document ID or catalog name.

    Args:
        object_id: Unique document ID or catalog identifier (e.g. 'm31', 'm42', 'jupiter').

    Returns:
        Formatted string containing all properties of the target celestial object.
    """
    try:
        clean_id = object_id.lower().strip()
        doc_ref = db.collection(COLLECTION_NAME).document(clean_id)
        doc = doc_ref.get()

        if not doc.exists:
            # Fallback search by catalog_id or name if exact doc ID isn't found
            search_res = search_celestial_objects(query=clean_id)
            if "No celestial objects found" not in search_res:
                return search_res
            return f"Celestial object with ID or catalog name '{object_id}' was not found in Firestore."

        data = doc.to_dict()
        return (
            f"--- Celestial Object Details: {data.get('name')} ---\n"
            f"Document ID: {clean_id}\n"
            f"Catalog ID: {data.get('catalog_id')}\n"
            f"Type: {data.get('type')}\n"
            f"Constellation: {data.get('constellation')}\n"
            f"Apparent Magnitude: {data.get('apparent_magnitude')}\n"
            f"Distance: {data.get('distance_light_years')} light years\n"
            f"Best Viewing Season: {data.get('best_season')}\n"
            f"Minimum Aperture Required: {data.get('min_aperture_mm')} mm\n"
            f"Sky Coordinates: {data.get('coordinates')}\n"
            f"Description: {data.get('description')}"
        )

    except Exception as e:
        return f"Error retrieving document '{object_id}' from Firestore: {e}"


def add_or_update_celestial_object(
    object_id: str,
    name: str,
    catalog_id: str,
    object_type: str,
    constellation: str,
    apparent_magnitude: float,
    best_season: str,
    min_aperture_mm: int,
    coordinates: str,
    description: str,
) -> str:
    """Adds a new celestial object or updates an existing document in the Firestore catalog.

    Args:
        object_id: Unique document ID slug (e.g. 'm57', 'saturn', 'ngc7000').
        name: Common name of the celestial object (e.g. 'Ring Nebula', 'Saturn').
        catalog_id: Formal catalog designation (e.g. 'M57 / NGC 6720').
        object_type: Classification (e.g. 'Planetary Nebula', 'Planet', 'Globular Cluster').
        constellation: Constellation location (e.g. 'Lyra', 'Cygnus').
        apparent_magnitude: Visual brightness magnitude (e.g. 8.8).
        best_season: Best viewing season (e.g. 'Summer', 'Autumn', 'Winter', 'Spring').
        min_aperture_mm: Recommended minimum scope aperture in mm (e.g. 100).
        coordinates: Sky position (e.g. 'RA 18h 53m | Dec +33° 01′').
        description: Informative summary and observing recommendations.

    Returns:
        Status message confirming the Firestore write operation.
    """
    try:
        clean_id = object_id.lower().strip().replace(" ", "_")
        doc_data = {
            "object_id": clean_id,
            "name": name,
            "catalog_id": catalog_id,
            "type": object_type,
            "constellation": constellation,
            "apparent_magnitude": float(apparent_magnitude),
            "best_season": best_season,
            "min_aperture_mm": int(min_aperture_mm),
            "coordinates": coordinates,
            "description": description,
        }

        doc_ref = db.collection(COLLECTION_NAME).document(clean_id)
        doc_ref.set(doc_data, merge=True)

        return f"Successfully saved celestial object '{name}' (ID: {clean_id}) in Firestore collection '{COLLECTION_NAME}'."

    except Exception as e:
        return f"Error saving object '{object_id}' to Firestore: {e}"
