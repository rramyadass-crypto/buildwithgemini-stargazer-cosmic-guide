"""Seed script to populate Firestore with initial celestial objects for Stargazer & Cosmic Guide."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-33c05f9db6da"
COLLECTION_NAME = "celestial_objects"

SEED_DATA = [
    {
        "object_id": "m31",
        "name": "Andromeda Galaxy",
        "catalog_id": "M31 / NGC 224",
        "type": "Spiral Galaxy",
        "constellation": "Andromeda",
        "apparent_magnitude": 3.44,
        "distance_light_years": 2500000,
        "best_season": "Autumn",
        "min_aperture_mm": 50,
        "coordinates": "RA 00h 42m 44s | Dec +41° 16′ 09″",
        "description": "The nearest major galaxy to the Milky Way, visible to the naked eye under dark skies.",
    },
    {
        "object_id": "m42",
        "name": "Orion Nebula",
        "catalog_id": "M42 / NGC 1976",
        "type": "Diffuse Emission Nebula",
        "constellation": "Orion",
        "apparent_magnitude": 4.0,
        "distance_light_years": 1344,
        "best_season": "Winter",
        "min_aperture_mm": 60,
        "coordinates": "RA 05h 35m 17s | Dec -05° 23′ 28″",
        "description": "A vibrant stellar nursery containing the famous Trapezium cluster at its heart.",
    },
    {
        "object_id": "m45",
        "name": "Pleiades Star Cluster",
        "catalog_id": "M45",
        "type": "Open Star Cluster",
        "constellation": "Taurus",
        "apparent_magnitude": 1.6,
        "distance_light_years": 444,
        "best_season": "Winter",
        "min_aperture_mm": 0,
        "coordinates": "RA 03h 47m 24s | Dec +24° 07′ 00″",
        "description": "The Seven Sisters, an extremely bright open star cluster visible with binoculars or naked eyes.",
    },
    {
        "object_id": "m13",
        "name": "Great Globular Cluster in Hercules",
        "catalog_id": "M13 / NGC 6205",
        "type": "Globular Star Cluster",
        "constellation": "Hercules",
        "apparent_magnitude": 5.8,
        "distance_light_years": 22200,
        "best_season": "Summer",
        "min_aperture_mm": 80,
        "coordinates": "RA 16h 41m 41s | Dec +36° 27′ 35″",
        "description": "A dense spherical cluster of hundreds of thousands of ancient stars in Hercules.",
    },
    {
        "object_id": "jupiter",
        "name": "Jupiter",
        "catalog_id": "Planet Jupiter",
        "type": "Gas Giant Planet",
        "constellation": "Varies",
        "apparent_magnitude": -2.7,
        "distance_light_years": 0,
        "best_season": "Autumn/Winter",
        "min_aperture_mm": 60,
        "coordinates": "Ecliptic Planet",
        "description": "The largest planet in the Solar System with cloud bands, Great Red Spot, and 4 Galilean moons.",
    },
]


def seed_database():
    print(f"Connecting to Firestore using hardcoded project ID: '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection(COLLECTION_NAME)

    for item in SEED_DATA:
        doc_id = item["object_id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        print(f"Seeded object: {item['name']} ({doc_id}) -> collection '{COLLECTION_NAME}'")

    print("Firestore seeding complete!")


if __name__ == "__main__":
    seed_database()
