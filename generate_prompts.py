#!/usr/bin/env python3
"""
Generate detailed prompts for image search or AI image generation
"""
import json
import os
import requests
import sys

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "host.docker.internal:11434")

def query_ollama(prompt, model="llama3.2"):
    """Query Ollama instance via HTTP API"""
    url = f"http://{OLLAMA_HOST}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to Ollama at {OLLAMA_HOST}")
        print("Make sure Ollama is running on the host.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("Error: Ollama request timed out (120s)")
        sys.exit(1)

def generate_image_prompts(character_name, character_data, scene_description):
    """Generate detailed image generation prompts"""
    
    # Safely extract character details with None handling
    age = character_data.get('age') or 'adult'
    ethnicity = character_data.get('ethnicity') or 'person'
    gender = character_data.get('gender') or 'person'
    clothing = character_data.get('clothing') or 'formal attire'
    
    facial_features = character_data.get('facial_features') or []
    if isinstance(facial_features, list) and facial_features:
        features_str = ', '.join([f for f in facial_features if f])
    else:
        features_str = 'distinctive features'
    
    prompt = f"""You are an expert at writing prompts for AI image generation tools like Midjourney or DALL-E.

Create a detailed, high-quality image generation prompt for this character in this scene:

CHARACTER: {character_name}
AGE: {age}
ETHNICITY: {ethnicity}
GENDER: {gender}
CLOTHING: {clothing}
FACIAL FEATURES: {features_str}
SCENE: {scene_description}

VISUAL STYLE: 1940s film noir meets futuristic Mumbai, art deco architecture, neon lights, monsoon rain, peacock blues and coppers, cinematic lighting, dramatic shadows

Create a prompt that includes:
- Physical description (age, ethnicity, distinctive features)
- Clothing and style details
- Pose and expression
- Setting and atmosphere
- Lighting and mood (film noir aesthetic)
- Camera angle and composition

Format: Single paragraph, 100-150 words, optimized for AI image generation.
Output ONLY the prompt, no preamble or explanation.
"""
    
    return query_ollama(prompt)

def load_character_data():
    """Load character data with error handling"""
    try:
        with open("characters/character_data.json", "r") as f:
            data = json.load(f)
        
        if 'characters' not in data:
            print("❌ Error: 'characters' key not found in JSON")
            sys.exit(1)
        
        return data
    except FileNotFoundError:
        print("❌ Error: characters/character_data.json not found")
        print("Run extract_characters.py first!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in character_data.json: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Load character data
    data = load_character_data()
    
    # Define key scenes for each character
    scenes = {
        "vijay": [
            {
                "key": "rain_scene",
                "description": "Standing under chrome awning in heavy rain, dark eyes scanning crime scene below, weary but determined expression, cigarette smoke curling upward, neon lights reflecting in puddles"
            },
            {
                "key": "interrogation",
                "description": "Sitting in dimly lit office, cigarette in hand, smoke curling around face, internal conflict visible in expression, case files scattered on desk, art deco lamp casting dramatic shadows"
            },
            {
                "key": "dawn_decision",
                "description": "At eastern gate at dawn, rain-soaked coat, handing data chip to someone off-camera, face heavy with moral weight of decision, monsoon clouds breaking behind"
            },
            {
                "key": "archive_research",
                "description": "Hunched over desk in cramped office surrounded by holographic files, cigarette smoke filling the air, intense concentration, art deco desk lamp, noir shadows"
            }
        ],
        "rukmini": [
            {
                "key": "warehouse_moonlight",
                "description": "Sitting among colorful silk bolts in abandoned warehouse, moonlight streaming through broken roof, rain drumming overhead, peacock-blue sari, android-perfect features with unexpectedly human expression of sadness"
            },
            {
                "key": "first_encounter",
                "description": "In elegant peacock-blue sari, dancer's posture, impossibly graceful movements, synthetic skin like moonstone, eyes showing unexpected depth and emotion, neon-lit interior"
            },
            {
                "key": "desperate_plea",
                "description": "Close-up of face showing confused sadness, android perfection with glitching emotion, hands pressed together in namaste gesture, sari draped elegantly"
            },
            {
                "key": "final_gratitude",
                "description": "At eastern gate at dawn, palms together in perfect namaste, gratitude and hope in android features, peacock-blue sari, mist surrounding, about to disappear into freedom"
            }
        ],
        "chen": [
            {
                "key": "victim_scene",
                "description": "Wealthy British-Indian trade magnate in luxurious private booth, traditional meets modern aesthetic, batik curtains, art deco surroundings, late 50s, distinguished features"
            }
        ],
        "ashworth": [
            {
                "key": "villain",
                "description": "British corporate executive in Indo-British formal wear, calculating expression, expensive suit with subtle Indian design elements, art deco office, sinister undertones"
            }
        ]
    }
    
    prompts = {}
    all_prompts_output = []
    
    print("\n" + "="*70)
    print("GENERATING IMAGE PROMPTS FOR CHARACTERS")
    print("="*70)
    
    for char in data['characters']:
        char_name = char.get('name', 'Unknown')
        char_name_lower = char_name.lower()
        
        # Find matching scenes for this character
        character_scenes = None
        for scene_key, scene_list in scenes.items():
            if scene_key in char_name_lower:
                character_scenes = scene_list
                break
        
        if not character_scenes:
            print(f"\n⚠️  No scenes defined for {char_name}, skipping...")
            continue
        
        print(f"\n{'─'*70}")
        print(f"CHARACTER: {char_name}")
        print(f"{'─'*70}")
        
        for scene in character_scenes:
            scene_key = scene['key']
            scene_desc = scene['description']
            
            print(f"\n🎬 Scene: {scene_key}")
            print(f"   {scene_desc[:80]}...")
            print(f"\n   ⏳ Generating prompt (this may take 30s)...")
            
            try:
                prompt = generate_image_prompts(char_name, char, scene_desc)
                
                prompt_key = f"{char_name.lower().replace(' ', '_')}_{scene_key}"
                prompts[prompt_key] = {
                    "character": char_name,
                    "scene": scene_key,
                    "scene_description": scene_desc,
                    "prompt": prompt
                }
                
                print(f"\n   ✅ Generated:")
                print(f"   {prompt}\n")
                
                # For easy copying
                all_prompts_output.append({
                    "id": prompt_key,
                    "character": char_name,
                    "scene": scene_key,
                    "prompt": prompt
                })
                
            except Exception as e:
                print(f"   ❌ Error generating prompt: {e}")
                continue
    
    # Save prompts
    with open("characters/image_generation_prompts.json", "w") as f:
        json.dump(prompts, f, indent=2)

    # Save to DB
    try:
        import db as db_module
        db_module.save_prompts(prompts)
        print("  Saved prompts to database")
    except Exception as e:
        print(f"  Warning: Could not save to DB: {e}")

    # Also save a simple list for easy copying
    with open("characters/prompts_list.txt", "w") as f:
        for item in all_prompts_output:
            f.write(f"{'='*70}\n")
            f.write(f"ID: {item['id']}\n")
            f.write(f"Character: {item['character']} - {item['scene']}\n")
            f.write(f"{'='*70}\n")
            f.write(f"{item['prompt']}\n\n")
    
    print("\n" + "="*70)
    print("FILES CREATED")
    print("="*70)
    print("✓ characters/image_generation_prompts.json (structured data)")
    print("✓ characters/prompts_list.txt (easy to copy)")
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("1. Review prompts_list.txt")
    print("2. Use prompts with:")
    print("   - Midjourney: Copy prompt to Discord")
    print("   - DALL-E: Copy prompt to ChatGPT")
    print("   - Stable Diffusion: Use with local generation")
    print("3. Save generated images with naming convention:")
    print("   characters/vijay_base_face.jpg")
    print("   scenes/vijay_rain_scene.jpg")
    print("   scenes/rukmini_warehouse.jpg")
    print("4. Or use image search queries from search_queries.json")
    print("   for stock photos from Pexels/Unsplash")
    print("="*70)
    
    if all_prompts_output:
        print(f"\n✅ Successfully generated {len(all_prompts_output)} prompts!")
    else:
        print("\n⚠️  No prompts generated. Check character data.")