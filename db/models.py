"""
Dataclasses for all database entities.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    id: Optional[int] = None
    username: str = "default"
    display_name: str = "Default User"
    created_at: Optional[str] = None


@dataclass
class Project:
    id: Optional[int] = None
    user_id: int = 1
    name: str = "Neo-Mumbai Noir"
    description: str = ""
    is_active: bool = True
    created_at: Optional[str] = None


@dataclass
class Story:
    id: Optional[int] = None
    project_id: int = 1
    title: str = ""
    content: str = ""
    ollama_model: str = "llama3.2"
    created_at: Optional[str] = None


@dataclass
class Character:
    id: Optional[int] = None
    story_id: Optional[int] = None
    name: str = ""
    slug: str = ""
    age: str = ""
    ethnicity: str = ""
    gender: str = ""
    facial_features: list = field(default_factory=list)
    clothing: str = ""
    key_scenes: list = field(default_factory=list)
    emotions: list = field(default_factory=list)


@dataclass
class Scene:
    id: Optional[int] = None
    character_id: Optional[int] = None
    scene_key: str = ""
    scene_name: str = ""
    description: str = ""


@dataclass
class SearchQuery:
    id: Optional[int] = None
    character_id: Optional[int] = None
    query_type: str = ""
    query_text: str = ""
    notes: str = ""
    executed: bool = False
    results_count: int = 0


@dataclass
class ImagePrompt:
    id: Optional[int] = None
    scene_id: Optional[int] = None
    character_id: Optional[int] = None
    prompt_text: str = ""
    negative_prompt: str = ""
    ollama_model: str = "llama3.2"


@dataclass
class ImageRecord:
    id: Optional[int] = None
    character_id: Optional[int] = None
    scene_id: Optional[int] = None
    image_prompt_id: Optional[int] = None
    image_type: str = ""  # portrait, scene_reference, generated, faceswap
    file_path: str = ""
    file_name: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    source: str = ""  # pexels, unsplash, comfyui, facefusion
    photographer: str = ""
    source_url: str = ""


@dataclass
class FaceSwap:
    id: Optional[int] = None
    source_image_id: Optional[int] = None
    target_image_id: Optional[int] = None
    result_image_id: Optional[int] = None
    status: str = "pending"  # pending, processing, completed, failed
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
