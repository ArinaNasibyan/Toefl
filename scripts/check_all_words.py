import json
from pathlib import Path

def main():
    vocab_path = Path("data/vocabulary.json")
    if not vocab_path.exists():
        print("Database not found.")
        return
        
    with open(vocab_path, "r", encoding="utf-8") as f:
        words = json.load(f)
        
    output_path = Path("data/vocab_check.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for i, item in enumerate(words):
            f.write(f"{i+1:03d}. {item['word']}: {item['transcription']}\n")
            
    print(f"Successfully wrote {len(words)} words to {output_path}")

if __name__ == "__main__":
    main()
