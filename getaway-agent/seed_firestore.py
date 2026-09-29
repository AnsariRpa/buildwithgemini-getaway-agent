#!/usr/bin/env python3
"""Seed script to populate Firestore with initial getaway destinations."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-6e0ce481a5e0"
COLLECTION_NAME = "destinations"

DESTINATIONS = [
    {
        "id": "sonoma-valley",
        "name": "Sonoma Valley Wine Country",
        "region": "Northern California",
        "vibe": "relaxation",
        "drive_hours": 1.5,
        "estimated_budget": 550,
        "highlights": ["Vineyard bike tour", "Artisan cheese tasting", "Historic plaza dinner"],
        "description": "Quiet rolling hills, rustic tasting rooms, and world-class farm-to-table dining."
    },
    {
        "id": "lake-tahoe",
        "name": "Lake Tahoe Alpine Escape",
        "region": "Sierra Nevada",
        "vibe": "adventure",
        "drive_hours": 3.5,
        "estimated_budget": 650,
        "highlights": ["Emerald Bay kayaking", "Eagle Rock sunset hike", "Lakeside dining"],
        "description": "Crystal-clear alpine waters surrounded by mountain trails and outdoor adventures."
    },
    {
        "id": "carmel-by-the-sea",
        "name": "Carmel-by-the-Sea Coastal Retreat",
        "region": "Central Coast",
        "vibe": "romantic",
        "drive_hours": 2.0,
        "estimated_budget": 700,
        "highlights": ["17-Mile Drive scenic view", "Point Lobos coastal walk", "Fairy-tale cottage strolls"],
        "description": "Charming storybook cottages, white sand beaches, and boutique ocean-side bistros."
    },
    {
        "id": "yosemite-valley",
        "name": "Yosemite National Park Expedition",
        "region": "Central Sierra",
        "vibe": "nature",
        "drive_hours": 4.0,
        "estimated_budget": 450,
        "highlights": ["Mist Trail waterfall hike", "Tunnel View photography", "Valley floor stargazing"],
        "description": "Iconic granite peaks, dramatic waterfalls, and serene ancient sequoias."
    },
    {
        "id": "big-sur",
        "name": "Big Sur Coastal Wilderness",
        "region": "Central Coast",
        "vibe": "adventure",
        "drive_hours": 2.5,
        "estimated_budget": 600,
        "highlights": ["McWay Falls cliffside view", "Pfeiffer Beach purple sand", "Coastal redwoods hike"],
        "description": "Dramatic coastal cliffs dropping into the Pacific Ocean with ancient redwood canyons."
    }
]


def seed_destinations():
    print(f"Connecting to Firestore in project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection(COLLECTION_NAME)

    for item in DESTINATIONS:
        doc_id = item["id"]
        doc_ref = collection.document(doc_id)
        doc_ref.set(item)
        print(f"  ✓ Seeded destination: {item['name']} ({doc_id})")

    print(f"\nSuccessfully seeded {len(DESTINATIONS)} getaway destinations into '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    seed_destinations()
