import asyncio
import json
import sys
from pathlib import Path
from infrastructure.content.json_content_loader import JsonContentLoader

async def main():
    loader = JsonContentLoader()
    print("Validating TOEFL Telegram Bot Content...")
    
    # 1. Validate Vocabulary
    try:
        words = await loader.load_vocabulary()
        print(f"[OK] Vocabulary: Loaded {len(words)} words successfully.")
        
        # Check size
        if len(words) != 350:
            print(f"[ERROR] Vocabulary Error: Expected 350 words, but got {len(words)}.")
            sys.exit(1)
            
        # Check standard fields
        for i, word in enumerate(words):
            if not word.id or not word.word or not word.translation or not word.transcription or not word.example or not word.level:
                print(f"[ERROR] Vocabulary Error: Word at index {i} ('{word.word}') is missing fields.")
                sys.exit(1)
                
            # Check IPA format (must start and end with /)
            if not word.transcription.startswith('/') or not word.transcription.endswith('/'):
                print(f"[ERROR] Vocabulary Error: Word '{word.word}' has invalid transcription format: '{word.transcription}'.")
                sys.exit(1)
                
    except Exception as e:
        print(f"[ERROR] Vocabulary Validation Failed: {e}")
        sys.exit(1)
        
    # 2. Validate Reading Passages
    try:
        passages = await loader.load_reading_passages()
        print(f"[OK] Reading Passages: Loaded {len(passages)} passages successfully.")
        
        # Check each passage
        for p in passages:
            if not p.id or not p.title or not p.text or not p.questions:
                print(f"[ERROR] Reading Error: Passage '{p.title}' is missing fields.")
                sys.exit(1)
                
            if len(p.questions) != 5:
                print(f"[ERROR] Reading Error: Passage '{p.title}' has {len(p.questions)} questions instead of 5.")
                sys.exit(1)
                
            for q in p.questions:
                if not q.id or not q.question or not q.options or q.correct_index is None or not q.explanation:
                    print(f"[ERROR] Reading Error: Question '{q.id}' in passage '{p.title}' is missing fields.")
                    sys.exit(1)
                    
                if len(q.options) != 4:
                    print(f"[ERROR] Reading Error: Question '{q.id}' in passage '{p.title}' has {len(q.options)} options instead of 4.")
                    sys.exit(1)
                    
                if q.correct_index < 0 or q.correct_index >= 4:
                    print(f"[ERROR] Reading Error: Question '{q.id}' in passage '{p.title}' has invalid correct_index: {q.correct_index}.")
                    sys.exit(1)
                    
    except Exception as e:
        print(f"[ERROR] Reading Passages Validation Failed: {e}")
        sys.exit(1)
        
    # 3. Validate Achievements
    try:
        achievements = await loader.load_achievements()
        print(f"[OK] Achievements: Loaded {len(achievements)} achievements successfully.")
    except Exception as e:
        print(f"[ERROR] Achievements Validation Failed: {e}")
        sys.exit(1)
        
    print("[SUCCESS] All content validation checks passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
