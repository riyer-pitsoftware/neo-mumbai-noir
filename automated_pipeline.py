#!/usr/bin/env python3
"""
Unified pipeline - search OR generate images automatically
"""
import sys

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║     NEO-MUMBAI NOIR - AUTOMATED IMAGE PIPELINE            ║
╚════════════════════════════════════════════════════════════╝

Choose image source:
  1. Search stock photos (Pexels + Unsplash)
  2. Generate locally (ComfyUI)
  3. Generate locally (Automatic1111)
  4. Both (search first, then generate missing)
  
  q. Quit
""")
    
    choice = input("Select option (1-4, q): ").strip()
    
    if choice == '1':
        print("\n🔍 Starting image search...")
        import image_search
        image_search.auto_search_and_download()
        
        print("\nNow run: python download_selected_images.py")
    
    elif choice == '2':
        print("\n🎨 Starting ComfyUI generation...")
        print("Make sure ComfyUI is running: cd ~/projects/ComfyUI && python main.py")
        input("Press Enter when ready...")
        
        import local_generation_comfy
        local_generation_comfy.generate_all_characters()
    
    elif choice == '3':
        print("\n🎨 Starting Automatic1111 generation...")
        print("Make sure A1111 is running: cd ~/projects/stable-diffusion-webui && ./webui.sh --api")
        input("Press Enter when ready...")
        
        import local_generation_a1111
        local_generation_a1111.generate_all_characters()
    
    elif choice == '4':
        print("\n🔄 Hybrid approach - searching then generating...")
        
        import image_search
        image_search.auto_search_and_download()
        
        print("\nNow select which to download and which to generate.")
    
    elif choice.lower() == 'q':
        print("Goodbye!")
        sys.exit(0)
    
    else:
        print("Invalid choice!")
        return main()


if __name__ == "__main__":
    main()