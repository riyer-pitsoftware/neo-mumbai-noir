#!/usr/bin/env python3
"""
Automated image search using Pexels and Unsplash APIs
"""
import os
import json
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ImageSearcher:
    def __init__(self):
        self.pexels_key = os.getenv('PEXELS_API_KEY')
        self.unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
        
        if not self.pexels_key:
            print("⚠️  PEXELS_API_KEY not found in .env")
        if not self.unsplash_key:
            print("⚠️  UNSPLASH_ACCESS_KEY not found in .env")
    
    def search_pexels(self, query, per_page=5, orientation='portrait'):
        """Search Pexels for images"""
        if not self.pexels_key:
            return []
        
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": self.pexels_key}
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for photo in data.get('photos', []):
                results.append({
                    'source': 'pexels',
                    'id': photo['id'],
                    'url': photo['src']['large2x'],
                    'photographer': photo['photographer'],
                    'description': photo.get('alt', query)
                })
            
            return results
        except Exception as e:
            print(f"Pexels error: {e}")
            return []
    
    def search_unsplash(self, query, per_page=5, orientation='portrait'):
        """Search Unsplash for images"""
        if not self.unsplash_key:
            return []
        
        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for photo in data.get('results', []):
                results.append({
                    'source': 'unsplash',
                    'id': photo['id'],
                    'url': photo['urls']['regular'],
                    'photographer': photo['user']['name'],
                    'description': photo.get('description') or photo.get('alt_description') or query
                })
            
            return results
        except Exception as e:
            print(f"Unsplash error: {e}")
            return []
    
    def search_all(self, query, per_page=5):
        """Search both sources"""
        results = []
        
        print(f"   🔍 Searching Pexels...")
        results.extend(self.search_pexels(query, per_page))
        
        time.sleep(1)  # Rate limiting
        
        print(f"   🔍 Searching Unsplash...")
        results.extend(self.search_unsplash(query, per_page))
        
        return results
    
    def download_image(self, url, save_path):
        """Download image from URL"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"Download error: {e}")
            return False


def auto_search_and_download():
    """Main function to search and download images"""
    
    # Load search queries
    try:
        with open("characters/search_queries.json", "r") as f:
            queries_data = json.load(f)
    except FileNotFoundError:
        print("❌ search_queries.json not found. Run extract_characters.py first!")
        return
    
    searcher = ImageSearcher()
    
    if not searcher.pexels_key and not searcher.unsplash_key:
        print("❌ No API keys found! Please add them to .env file")
        return
    
    print("\n" + "="*70)
    print("AUTOMATED IMAGE SEARCH")
    print("="*70 + "\n")
    
    # Group queries by character
    by_character = {}
    for query_item in queries_data:
        char = query_item.get('character', 'Unknown')
        if char not in by_character:
            by_character[char] = []
        by_character[char].append(query_item)
    
    all_results = {}
    
    for character, queries in by_character.items():
        print(f"\n{'─'*70}")
        print(f"CHARACTER: {character}")
        print(f"{'─'*70}")
        
        char_results = []
        
        for query_item in queries:
            query = query_item.get('query', '')
            query_type = query_item.get('type', 'unknown')
            
            print(f"\n📸 {query_type}")
            print(f"   Query: {query}")
            
            results = searcher.search_all(query, per_page=3)
            
            print(f"   ✅ Found {len(results)} images")
            
            for i, result in enumerate(results, 1):
                char_results.append({
                    'query_type': query_type,
                    'query': query,
                    'result_number': i,
                    'source': result['source'],
                    'url': result['url'],
                    'photographer': result['photographer'],
                    'description': result['description']
                })
            
            time.sleep(1)  # Rate limiting
        
        all_results[character] = char_results
    
    # Save results
    with open("characters/image_search_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "="*70)
    print("SEARCH COMPLETE")
    print("="*70)
    print(f"✓ Results saved to: characters/image_search_results.json")
    print(f"\nNext: Review results and run download_selected_images.py")


if __name__ == "__main__":
    auto_search_and_download()