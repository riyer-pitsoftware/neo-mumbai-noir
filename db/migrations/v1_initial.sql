-- Neo-Mumbai Noir: v1 initial schema
-- Applied automatically on first import of db package

CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_version (version) VALUES (1);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL DEFAULT '',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO users (id, username, display_name) VALUES (1, 'default', 'Default User');

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL DEFAULT 1 REFERENCES users(id),
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO projects (id, user_id, name, description, is_active)
VALUES (1, 1, 'Neo-Mumbai Noir', 'Default project', 1);

-- Stories
CREATE TABLE IF NOT EXISTS stories (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER NOT NULL DEFAULT 1 REFERENCES projects(id),
    title        TEXT NOT NULL DEFAULT '',
    content      TEXT NOT NULL DEFAULT '',
    ollama_model TEXT NOT NULL DEFAULT 'llama3.2',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Characters
CREATE TABLE IF NOT EXISTS characters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id        INTEGER REFERENCES stories(id),
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL,
    age             TEXT NOT NULL DEFAULT '',
    ethnicity       TEXT NOT NULL DEFAULT '',
    gender          TEXT NOT NULL DEFAULT '',
    facial_features TEXT NOT NULL DEFAULT '[]',   -- JSON array
    clothing        TEXT NOT NULL DEFAULT '',
    key_scenes      TEXT NOT NULL DEFAULT '[]',   -- JSON array
    emotions        TEXT NOT NULL DEFAULT '[]',   -- JSON array
    UNIQUE(story_id, slug)
);

-- Scenes
CREATE TABLE IF NOT EXISTS scenes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL REFERENCES characters(id),
    scene_key    TEXT NOT NULL,
    scene_name   TEXT NOT NULL DEFAULT '',
    description  TEXT NOT NULL DEFAULT '',
    UNIQUE(character_id, scene_key)
);

-- Search queries
CREATE TABLE IF NOT EXISTS search_queries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id  INTEGER NOT NULL REFERENCES characters(id),
    query_type    TEXT NOT NULL DEFAULT '',
    query_text    TEXT NOT NULL DEFAULT '',
    notes         TEXT NOT NULL DEFAULT '',
    executed      INTEGER NOT NULL DEFAULT 0,
    results_count INTEGER NOT NULL DEFAULT 0
);

-- Image prompts
CREATE TABLE IF NOT EXISTS image_prompts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id        INTEGER REFERENCES scenes(id),
    character_id    INTEGER REFERENCES characters(id),
    prompt_text     TEXT NOT NULL DEFAULT '',
    negative_prompt TEXT NOT NULL DEFAULT '',
    ollama_model    TEXT NOT NULL DEFAULT 'llama3.2'
);

-- Images (metadata only; files stay on disk)
CREATE TABLE IF NOT EXISTS images (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id    INTEGER REFERENCES characters(id),
    scene_id        INTEGER REFERENCES scenes(id),
    image_prompt_id INTEGER REFERENCES image_prompts(id),
    image_type      TEXT NOT NULL DEFAULT '',   -- portrait, scene_reference, generated, faceswap
    file_path       TEXT NOT NULL UNIQUE,
    file_name       TEXT NOT NULL DEFAULT '',
    width           INTEGER,
    height          INTEGER,
    source          TEXT NOT NULL DEFAULT '',   -- pexels, unsplash, comfyui, facefusion
    photographer    TEXT NOT NULL DEFAULT '',
    source_url      TEXT NOT NULL DEFAULT '',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Face swaps
CREATE TABLE IF NOT EXISTS face_swaps (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    source_image_id  INTEGER REFERENCES images(id),
    target_image_id  INTEGER REFERENCES images(id),
    result_image_id  INTEGER REFERENCES images(id),
    status           TEXT NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at     TIMESTAMP
);

-- Views
CREATE VIEW IF NOT EXISTS v_characters_with_images AS
SELECT
    c.id AS character_id,
    c.name,
    c.slug,
    c.age,
    c.ethnicity,
    c.gender,
    COUNT(i.id) AS image_count
FROM characters c
LEFT JOIN images i ON i.character_id = c.id
GROUP BY c.id;

CREATE VIEW IF NOT EXISTS v_storyboard AS
SELECT
    c.name AS character_name,
    c.slug,
    s.scene_key,
    s.description AS scene_description,
    ip.prompt_text,
    i.file_path,
    i.image_type
FROM characters c
LEFT JOIN scenes s ON s.character_id = c.id
LEFT JOIN image_prompts ip ON ip.scene_id = s.id
LEFT JOIN images i ON (i.scene_id = s.id OR i.character_id = c.id)
ORDER BY c.name, s.scene_key;

CREATE VIEW IF NOT EXISTS v_image_gallery AS
SELECT
    i.id,
    i.file_path,
    i.file_name,
    i.image_type,
    i.source,
    c.name AS character_name,
    s.scene_key
FROM images i
LEFT JOIN characters c ON c.id = i.character_id
LEFT JOIN scenes s ON s.id = i.scene_id
ORDER BY i.created_at DESC;
