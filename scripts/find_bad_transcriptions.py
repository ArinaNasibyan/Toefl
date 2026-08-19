import json
from pathlib import Path

def main():
    vocab_path = Path("data/vocabulary.json")
    if not vocab_path.exists():
        print("Database not found.")
        return
        
    with open(vocab_path, "r", encoding="utf-8") as f:
        words = json.load(f)
        
    print(f"Scanning {len(words)} words for suspicious transcriptions...\n")
    
    suspicious_count = 0
    for item in words:
        word = item["word"]
        trans = item["transcription"]
        
        reasons = []
        # Check if transcription has capital letters (e.g. /KAY-puh-buhl/)
        if any(c.isupper() for c in trans):
            reasons.append("Contains capital letters (informal respelling)")
            
        # Check if it has hyphens (informal respelling style like /uh-BUHN-duhnt/)
        if "-" in trans:
            # But exclude cases where the word itself is hyphenated (e.g. semi-arid)
            # unless the transcription has hyphens that aren't matching word hyphens
            if "-" not in word or trans.count("-") > word.count("-"):
                reasons.append("Contains hyphens (suspicious respelling)")
                
        # Check if it's too short (less than 3 chars)
        if len(trans) < 3:
            reasons.append("Too short")
            
        # Check if it contains phonetic spelling indicators like 'uh', 'AY', 'YOO'
        for term in ["uh", "AY", "YOO", "AW", "EE", "OH", "OO", "ow", "oy"]:
            if term in trans and term not in word:
                if term.upper() in trans or term in trans:
                    reasons.append(f"Contains respelling indicator '{term}'")
                    break
                    
        # Check if it lacks stress marks but contains weird symbols
        if len(word) > 5 and "ˈ" not in trans and "/" in trans:
            reasons.append("Missing primary stress mark on multi-syllable word")
            
        if reasons:
            suspicious_count += 1
            log_lines = [
                f"Word: '{word}'",
                f"  Transcription: {trans}",
                f"  Reasons: {', '.join(reasons)}",
                "-" * 40
            ]
            for line in log_lines:
                print(line.encode('ascii', errors='backslashreplace').decode('ascii'))
            
    print(f"Scan complete. Found {suspicious_count} suspicious transcriptions.")

if __name__ == "__main__":
    main()
