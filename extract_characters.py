#!/usr/bin/env python3
"""CLI wrapper — Extract character descriptions from story and generate search queries."""

import asyncio
import json
import sys

from neo_modules.extraction import extract_characters, generate_search_queries


async def main():
    # Read story
    try:
        with open("story.txt", "r") as f:
            story = f.read()
    except FileNotFoundError:
        print("❌ Error: story.txt not found")
        print("Create it first with your story text")
        sys.exit(1)

    print("🔍 Extracting characters from story...")
    print("(This may take 30-60 seconds with Ollama...)\n")

    characters = await extract_characters(story)

    print(f"\n✅ Found {len(characters['characters'])} characters\n")

    # Pretty print character details
    for char in characters["characters"]:
        print(f"📋 {char.get('name', 'Unknown')}")
        print(f"   Age: {char.get('age', 'N/A')}")
        print(f"   Ethnicity: {char.get('ethnicity', 'N/A')}")
        print(f"   Gender: {char.get('gender', 'N/A')}")

        features = char.get("facial_features")
        if features and isinstance(features, list):
            print(f"   Features: {', '.join(features)}")

        emotions = char.get("emotions")
        if emotions and isinstance(emotions, list):
            print(f"   Emotions: {', '.join(emotions)}")

        print()

    # Save character data
    with open("characters/character_data.json", "w") as f:
        json.dump(characters, f, indent=2)

    # Save to DB
    try:
        import db as db_module

        story_id = db_module.save_story(story)
        char_id_map = db_module.save_characters(characters, story_id)
        print("  Saved characters to database")
    except Exception as e:
        print(f"  Warning: Could not save to DB: {e}")
        char_id_map = None

    print("📝 Generating image search queries...")
    queries = generate_search_queries(characters)

    with open("characters/search_queries.json", "w") as f:
        json.dump(queries, f, indent=2)

    # Save queries to DB
    try:
        if char_id_map:
            import db as db_module

            db_module.save_search_queries(queries, char_id_map)
            print("  Saved search queries to database")
    except Exception as e:
        print(f"  Warning: Could not save queries to DB: {e}")

    print(f"\n🎯 Generated {len(queries)} search queries\n")

    # Show sample queries
    print("Sample queries:")
    print("-" * 60)
    for query in queries[:5]:
        print(f"Character: {query['character']}")
        print(f"Type: {query['type']}")
        print(f"Query: {query['query']}")
        print(f"Notes: {query.get('notes', '')}")
        print()

    if len(queries) > 5:
        print(f"... and {len(queries) - 5} more queries")

    print("\n" + "=" * 60)
    print("FILES CREATED:")
    print("=" * 60)
    print("✓ characters/character_data.json")
    print("✓ characters/search_queries.json")


if __name__ == "__main__":
    asyncio.run(main())
