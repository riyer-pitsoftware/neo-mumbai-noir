#!/usr/bin/env python3
"""
Tests for the SQLite database layer.
Run inside Docker: docker compose exec noir-pipeline python test_db.py
"""
import json
import sys
import traceback
from pathlib import Path

# Reset DB state for clean test run
from db.connection import ConnectionManager, DB_PATH


def reset_db():
    """Drop and recreate the DB for a clean test."""
    ConnectionManager.close()
    ConnectionManager._schema_applied = False
    if DB_PATH.exists():
        DB_PATH.unlink()
    wal = DB_PATH.parent / (DB_PATH.name + "-wal")
    shm = DB_PATH.parent / (DB_PATH.name + "-shm")
    if wal.exists():
        wal.unlink()
    if shm.exists():
        shm.unlink()
    # Force new connection
    ConnectionManager._local = __import__("threading").local()
    ConnectionManager.init_schema()


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def test(self, name, fn):
        try:
            fn()
            self.passed += 1
            print(f"  PASS  {name}")
        except AssertionError as e:
            self.failed += 1
            self.errors.append((name, str(e)))
            print(f"  FAIL  {name}: {e}")
        except Exception as e:
            self.failed += 1
            self.errors.append((name, traceback.format_exc()))
            print(f"  ERROR {name}: {e}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Results: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print(f"\nFailures:")
            for name, err in self.errors:
                print(f"  - {name}: {err}")
        print(f"{'='*60}")
        return self.failed == 0


runner = TestRunner()


# ── Schema & Initialization ──────────────────────────────────────────────

def test_schema_created():
    """Schema version table exists and has version 1."""
    rows = ConnectionManager.execute("SELECT version FROM schema_version")
    assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
    assert rows[0]["version"] == 1, f"Expected version 1, got {rows[0]['version']}"


def test_all_tables_exist():
    """All expected tables are created."""
    rows = ConnectionManager.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {r["name"] for r in rows}
    expected = {
        "characters", "face_swaps", "image_prompts", "images",
        "projects", "scenes", "schema_version", "search_queries",
        "stories", "users",
    }
    missing = expected - tables
    assert not missing, f"Missing tables: {missing}"


def test_all_views_exist():
    """All expected views are created."""
    rows = ConnectionManager.execute(
        "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
    )
    views = {r["name"] for r in rows}
    expected = {"v_characters_with_images", "v_image_gallery", "v_storyboard"}
    missing = expected - views
    assert not missing, f"Missing views: {missing}"


def test_default_user_exists():
    """Default user (id=1) is auto-created."""
    rows = ConnectionManager.execute("SELECT * FROM users WHERE id = 1")
    assert len(rows) == 1
    assert rows[0]["username"] == "default"


def test_default_project_exists():
    """Default project (id=1) is auto-created."""
    rows = ConnectionManager.execute("SELECT * FROM projects WHERE id = 1")
    assert len(rows) == 1
    assert rows[0]["name"] == "Neo-Mumbai Noir"
    assert rows[0]["is_active"] == 1


def test_foreign_keys_enabled():
    """PRAGMA foreign_keys is ON."""
    rows = ConnectionManager.execute("PRAGMA foreign_keys")
    assert rows[0][0] == 1, "Foreign keys not enabled"


def test_wal_mode():
    """WAL journal mode is active."""
    rows = ConnectionManager.execute("PRAGMA journal_mode")
    assert rows[0][0] == "wal", f"Expected wal, got {rows[0][0]}"


def test_db_file_in_data_dir():
    """DB file lives under data/ directory."""
    assert "data" in str(DB_PATH), f"DB_PATH doesn't contain 'data': {DB_PATH}"
    assert DB_PATH.exists(), f"DB file not found at {DB_PATH}"


print("\n== Schema & Initialization ==")
runner.test("schema_created", test_schema_created)
runner.test("all_tables_exist", test_all_tables_exist)
runner.test("all_views_exist", test_all_views_exist)
runner.test("default_user_exists", test_default_user_exists)
runner.test("default_project_exists", test_default_project_exists)
runner.test("foreign_keys_enabled", test_foreign_keys_enabled)
runner.test("wal_mode", test_wal_mode)
runner.test("db_file_in_data_dir", test_db_file_in_data_dir)


# ── Story CRUD ───────────────────────────────────────────────────────────

import db

def test_save_and_load_story():
    """save_story() then load_story() returns same content."""
    text = "It was a dark and stormy night in Neo-Mumbai..."
    db.save_story(text)
    result = db.load_story()
    assert result == text, f"Story mismatch: {result[:50]}"


def test_save_story_returns_id():
    """save_story() returns an integer story_id."""
    sid = db.save_story("Another story")
    assert isinstance(sid, int), f"Expected int, got {type(sid)}"
    assert sid > 0


def test_save_story_updates_existing():
    """Calling save_story() again updates the same row."""
    db.save_story("Version 1")
    id1 = db.save_story("Version 2")
    result = db.load_story()
    assert result == "Version 2", f"Expected 'Version 2', got: {result}"


print("\n== Story CRUD ==")
reset_db()
runner.test("save_and_load_story", test_save_and_load_story)
runner.test("save_story_returns_id", test_save_story_returns_id)
reset_db()
runner.test("save_story_updates_existing", test_save_story_updates_existing)


# ── Character CRUD ───────────────────────────────────────────────────────

SAMPLE_CHARACTERS = {
    "characters": [
        {
            "name": "Inspector Vijay",
            "age": "42",
            "ethnicity": "South Indian",
            "gender": "male",
            "facial_features": ["angular face", "strong jawline"],
            "clothing": "charcoal achkan coat",
            "key_scenes": ["crime scene", "archives"],
            "emotions": ["weary determination", "moral conflict"],
        },
        {
            "name": "Rukmini",
            "age": "mid-20s",
            "ethnicity": "South Asian",
            "gender": "female",
            "facial_features": ["symmetrical face"],
            "clothing": "peacock-blue sari",
            "key_scenes": ["warehouse"],
            "emotions": ["confused sadness"],
        },
    ]
}


def test_save_characters():
    """save_characters() stores all characters and returns id map."""
    db.save_story("test story")
    id_map = db.save_characters(SAMPLE_CHARACTERS)
    assert len(id_map) == 2, f"Expected 2 characters, got {len(id_map)}"
    assert "Inspector Vijay" in id_map
    assert "Rukmini" in id_map
    assert all(isinstance(v, int) for v in id_map.values())


def test_load_character_data_format():
    """load_character_data() returns dict with 'characters' key matching old JSON format."""
    db.save_story("test story")
    db.save_characters(SAMPLE_CHARACTERS)
    data = db.load_character_data()
    assert data is not None
    assert "characters" in data
    assert len(data["characters"]) == 2
    vijay = data["characters"][0]
    assert vijay["name"] == "Inspector Vijay"
    assert vijay["age"] == "42"
    assert vijay["ethnicity"] == "South Indian"
    assert vijay["gender"] == "male"
    assert vijay["facial_features"] == ["angular face", "strong jawline"]
    assert vijay["clothing"] == "charcoal achkan coat"
    assert vijay["key_scenes"] == ["crime scene", "archives"]
    assert vijay["emotions"] == ["weary determination", "moral conflict"]


def test_character_names():
    """character_names() returns list of name strings."""
    db.save_story("test story")
    db.save_characters(SAMPLE_CHARACTERS)
    names = db.character_names()
    assert names == ["Inspector Vijay", "Rukmini"], f"Got: {names}"


def test_load_character_data_empty():
    """load_character_data() returns None when no characters exist."""
    data = db.load_character_data()
    assert data is None


def test_character_names_empty():
    """character_names() returns [] when no characters exist."""
    names = db.character_names()
    assert names == []


def test_get_character_id_by_name():
    """get_character_id_by_name() looks up by slug."""
    db.save_story("test")
    id_map = db.save_characters(SAMPLE_CHARACTERS)
    cid = db.get_character_id_by_name("Inspector Vijay")
    assert cid == id_map["Inspector Vijay"]


def test_get_character_id_not_found():
    """get_character_id_by_name() returns None for unknown name."""
    result = db.get_character_id_by_name("Nonexistent Character")
    assert result is None


print("\n== Character CRUD ==")
reset_db()
runner.test("save_characters", test_save_characters)
reset_db()
runner.test("load_character_data_format", test_load_character_data_format)
reset_db()
runner.test("character_names", test_character_names)
reset_db()
runner.test("load_character_data_empty", test_load_character_data_empty)
reset_db()
runner.test("character_names_empty", test_character_names_empty)
reset_db()
runner.test("get_character_id_by_name", test_get_character_id_by_name)
reset_db()
runner.test("get_character_id_not_found", test_get_character_id_not_found)


# ── Search Queries ───────────────────────────────────────────────────────

SAMPLE_QUERIES = [
    {
        "character": "Inspector Vijay",
        "type": "base_portrait",
        "query": "South Indian male 42 portrait",
        "notes": "Base face",
    },
    {
        "character": "Inspector Vijay",
        "type": "emotion_weary determination",
        "query": "South Indian male weary expression",
        "notes": "weary determination",
    },
    {
        "character": "Rukmini",
        "type": "base_portrait",
        "query": "South Asian female portrait",
        "notes": "Base face for Rukmini",
    },
]


def test_save_search_queries():
    """save_search_queries() stores queries linked to characters."""
    db.save_story("test")
    id_map = db.save_characters(SAMPLE_CHARACTERS)
    db.save_search_queries(SAMPLE_QUERIES, id_map)
    from db.repositories.search_query import SearchQueryRepo
    vijay_queries = SearchQueryRepo.get_by_character(id_map["Inspector Vijay"])
    assert len(vijay_queries) == 2, f"Expected 2 queries for Vijay, got {len(vijay_queries)}"
    ruk_queries = SearchQueryRepo.get_by_character(id_map["Rukmini"])
    assert len(ruk_queries) == 1


def test_save_search_queries_by_slug_lookup():
    """save_search_queries() works without explicit id_map (looks up by slug)."""
    db.save_story("test")
    db.save_characters(SAMPLE_CHARACTERS)
    db.save_search_queries(SAMPLE_QUERIES)  # no id_map
    from db.repositories.search_query import SearchQueryRepo
    all_q = SearchQueryRepo.get_all()
    assert len(all_q) == 3, f"Expected 3, got {len(all_q)}"


print("\n== Search Queries ==")
reset_db()
runner.test("save_search_queries", test_save_search_queries)
reset_db()
runner.test("save_search_queries_by_slug_lookup", test_save_search_queries_by_slug_lookup)


# ── Prompts (Scenes + ImagePrompts) ─────────────────────────────────────

SAMPLE_PROMPTS = {
    "inspector_vijay_rain_scene": {
        "character": "Inspector Vijay",
        "scene": "rain_scene",
        "scene_description": "Standing under chrome awning in heavy rain",
        "prompt": "A 42-year-old South Indian male detective stands under rain...",
    },
    "rukmini_warehouse_moonlight": {
        "character": "Rukmini",
        "scene": "warehouse_moonlight",
        "scene_description": "Sitting among silk bolts in abandoned warehouse",
        "prompt": "A young South Asian woman in peacock-blue sari...",
    },
}


def test_save_and_load_prompts():
    """save_prompts() then load_prompts() round-trips correctly."""
    db.save_story("test")
    id_map = db.save_characters(SAMPLE_CHARACTERS)
    db.save_prompts(SAMPLE_PROMPTS, id_map)
    result = db.load_prompts()
    assert len(result) == 2, f"Expected 2 prompts, got {len(result)}"
    assert "inspector_vijay_rain_scene" in result
    assert "rukmini_warehouse_moonlight" in result
    rain = result["inspector_vijay_rain_scene"]
    assert rain["character"] == "Inspector Vijay"
    assert rain["scene"] == "rain_scene"
    assert rain["scene_description"] == "Standing under chrome awning in heavy rain"
    assert "detective stands under rain" in rain["prompt"]


def test_load_prompts_empty():
    """load_prompts() returns {} when no prompts exist."""
    result = db.load_prompts()
    assert result == {}


print("\n== Prompts (Scenes + ImagePrompts) ==")
reset_db()
runner.test("save_and_load_prompts", test_save_and_load_prompts)
reset_db()
runner.test("load_prompts_empty", test_load_prompts_empty)


# ── Image Registration ───────────────────────────────────────────────────

def test_register_image():
    """register_image() stores metadata and returns id."""
    img_id = db.register_image(
        file_path="/app/characters/vijay_base_1.jpg",
        image_type="portrait",
        source="pexels",
        photographer="John Doe",
        source_url="https://pexels.com/photo/123",
    )
    assert isinstance(img_id, int) and img_id > 0
    from db.repositories.image import ImageRepo
    row = ImageRepo.get_by_path("/app/characters/vijay_base_1.jpg")
    assert row is not None
    assert row["image_type"] == "portrait"
    assert row["source"] == "pexels"
    assert row["file_name"] == "vijay_base_1.jpg"


def test_register_image_with_character():
    """register_image() links to character_id."""
    db.save_story("test")
    id_map = db.save_characters(SAMPLE_CHARACTERS)
    vijay_id = id_map["Inspector Vijay"]
    img_id = db.register_image(
        file_path="/app/characters/vijay_portrait.jpg",
        image_type="portrait",
        character_id=vijay_id,
    )
    from db.repositories.image import ImageRepo
    imgs = ImageRepo.get_by_character(vijay_id)
    assert len(imgs) == 1
    assert imgs[0]["file_path"] == "/app/characters/vijay_portrait.jpg"


def test_register_image_unique_path():
    """Duplicate file_path is silently ignored (INSERT OR IGNORE)."""
    db.register_image(file_path="/app/outputs/test.png", image_type="generated")
    db.register_image(file_path="/app/outputs/test.png", image_type="generated")
    from db.repositories.image import ImageRepo
    all_imgs = ImageRepo.get_all()
    paths = [r["file_path"] for r in all_imgs]
    assert paths.count("/app/outputs/test.png") == 1


print("\n== Image Registration ==")
reset_db()
runner.test("register_image", test_register_image)
reset_db()
runner.test("register_image_with_character", test_register_image_with_character)
reset_db()
runner.test("register_image_unique_path", test_register_image_unique_path)


# ── Face Swap ────────────────────────────────────────────────────────────

def test_create_and_complete_face_swap():
    """Full face swap lifecycle: create -> complete."""
    src_id = db.register_image("/app/characters/src.jpg", image_type="portrait")
    tgt_id = db.register_image("/app/scenes/target.jpg", image_type="scene_reference")
    swap_id = db.create_face_swap(src_id, tgt_id)
    assert isinstance(swap_id, int) and swap_id > 0

    from db.repositories.face_swap import FaceSwapRepo
    swap = FaceSwapRepo.get_by_id(swap_id)
    assert swap["status"] == "pending"

    result_img_id = db.complete_face_swap(swap_id, "/app/outputs/faceswap/result.png")
    swap = FaceSwapRepo.get_by_id(swap_id)
    assert swap["status"] == "completed"
    assert swap["result_image_id"] == result_img_id


print("\n== Face Swap ==")
reset_db()
runner.test("create_and_complete_face_swap", test_create_and_complete_face_swap)


# ── Project API ──────────────────────────────────────────────────────────

def test_get_active_project():
    """get_active_project() returns the default project dict."""
    proj = db.get_active_project()
    assert proj is not None
    assert proj["name"] == "Neo-Mumbai Noir"
    assert proj["is_active"] == 1


print("\n== Project API ==")
reset_db()
runner.test("get_active_project", test_get_active_project)


# ── JSON Migration ───────────────────────────────────────────────────────

def test_json_migration():
    """migrate_json_to_db() imports existing JSON files."""
    from db.migrations.migrate import migrate_json_to_db

    # Only run if JSON files exist
    char_path = Path("characters/character_data.json")
    if not char_path.exists():
        print("  SKIP  json_migration (no JSON files present)")
        return

    result = migrate_json_to_db()
    assert "characters" in result
    assert result["characters"] > 0

    # Verify data was imported
    data = db.load_character_data()
    assert data is not None
    assert len(data["characters"]) > 0

    prompts = db.load_prompts()
    # Prompts may or may not exist depending on JSON files
    story = db.load_story()
    assert len(story) > 0


print("\n== JSON Migration ==")
reset_db()
runner.test("json_migration", test_json_migration)


# ── Backward Compatibility ───────────────────────────────────────────────

def test_backward_compat_types():
    """All backward-compatible functions return the documented types."""
    # Empty state
    assert db.load_story() == "" or isinstance(db.load_story(), str)
    assert db.load_character_data() is None or isinstance(db.load_character_data(), dict)
    assert isinstance(db.load_prompts(), dict)
    assert isinstance(db.character_names(), list)

    # With data
    db.save_story("test story text")
    db.save_characters(SAMPLE_CHARACTERS)
    db.save_prompts(SAMPLE_PROMPTS)

    assert isinstance(db.load_story(), str)
    data = db.load_character_data()
    assert isinstance(data, dict)
    assert "characters" in data
    assert isinstance(data["characters"], list)
    assert isinstance(data["characters"][0], dict)
    assert isinstance(db.load_prompts(), dict)
    assert isinstance(db.character_names(), list)
    assert all(isinstance(n, str) for n in db.character_names())


print("\n== Backward Compatibility ==")
reset_db()
runner.test("backward_compat_types", test_backward_compat_types)


# ── Utilities ────────────────────────────────────────────────────────────

def test_slugify():
    from db.utils import slugify
    assert slugify("Inspector Vijay Krishnan") == "inspector_vijay_krishnan"
    assert slugify("Rukmini (RK-7)") == "rukmini_rk_7"
    assert slugify("simple") == "simple"
    assert slugify("  spaces  ") == "spaces"


def test_json_helpers():
    from db.utils import to_json, from_json
    assert to_json(["a", "b"]) == '["a", "b"]'
    assert from_json('["a", "b"]') == ["a", "b"]
    assert from_json(None) == []
    assert from_json("invalid") == []
    assert to_json(None) == "[]"


print("\n== Utilities ==")
runner.test("slugify", test_slugify)
runner.test("json_helpers", test_json_helpers)


# ── Final Summary ────────────────────────────────────────────────────────

success = runner.summary()
sys.exit(0 if success else 1)
