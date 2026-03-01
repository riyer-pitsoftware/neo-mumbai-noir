#!/usr/bin/env python3
"""
Interactive image downloader - review and select images to download
"""
import json
import os
from pathlib import Path
from image_search import ImageSearcher

def download_images():
    """Download selected images based on results"""
    
    # Load search results
    try:
        with open("characters/image_search_results.json", "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        print("❌ Run image_search.py first!")
        return
    
    searcher = ImageSearcher()
    
    print("\n" + "="*70)
    print("IMAGE DOWNLOAD SELECTOR")
    print("="*70)
    print("\nFor each character, we'll download the top 2 images for each query type.")
    print("You can manually edit the JSON file to customize selections.\n")
    
    downloads_config = {}
    
    for character, char_results in results.items():
        print(f"\n{'─'*70}")
        print(f"CHARACTER: {character}")
        print(f"{'─'*70}")
        
        char_slug = character.lower().replace(' ', '_')
        
        # Group by query type
        by_type = {}
        for result in char_results:
            qtype = result['query_type']
            if qtype not in by_type:
                by_type[qtype] = []
            by_type[qtype].append(result)
        
        char_downloads = []
        
        for qtype, images in by_type.items():
            # Take top 2 for each type
            top_images = images[:2]
            
            for i, img in enumerate(top_images, 1):
                # Determine save location
                if 'base_portrait' in qtype:
                    save_dir = "characters"
                    filename = f"{char_slug}_base_{i}.jpg"
                else:
                    save_dir = "scenes"
                    filename = f"{char_slug}_{qtype}_{i}.jpg"
                
                save_path = Path(save_dir) / filename
                
                char_downloads.append({
                    'url': img['url'],
                    'save_path': str(save_path),
                    'query_type': qtype,
                    'source': img['source'],
                    'photographer': img['photographer']
                })
                
                print(f"  Will download: {filename}")
        
        downloads_config[character] = char_downloads
    
    # Save download config
    with open("characters/downloads_config.json", "w") as f:
        json.dump(downloads_config, f, indent=2)
    
    print("\n" + "="*70)
    print("Ready to download!")
    print("="*70)
    
    response = input("\nProceed with downloads? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Cancelled. Edit downloads_config.json and run this script again.")
        return
    
    print("\n" + "="*70)
    print("DOWNLOADING IMAGES")
    print("="*70 + "\n")
    
    total = sum(len(downloads) for downloads in downloads_config.values())
    current = 0
    
    for character, downloads in downloads_config.items():
        print(f"\n📥 {character}")
        
        for download in downloads:
            current += 1
            print(f"  [{current}/{total}] {Path(download['save_path']).name}...", end=' ')
            
            success = searcher.download_image(
                download['url'],
                download['save_path']
            )
            
            if success:
                print("✅")
                # Save attribution
                attribution_file = Path(download['save_path']).with_suffix('.txt')
                with open(attribution_file, 'w') as f:
                    f.write(f"Photographer: {download['photographer']}\n")
                    f.write(f"Source: {download['source']}\n")
                    f.write(f"URL: {download['url']}\n")
            else:
                print("❌")
    
    print("\n" + "="*70)
    print("DOWNLOAD COMPLETE")
    print("="*70)
    print("\nFiles saved to:")
    print("  - characters/ (base portraits)")
    print("  - scenes/ (emotion/pose references)")
    print("\nNext: Review images and run face_fusion_pipeline.py")


if __name__ == "__main__":
    download_images()