import asyncio
from datetime import date, timedelta
from infrastructure.content.json_content_loader import JsonContentLoader
from domain.services.daily_challenge_service import DailyChallengeService

async def main():
    loader = JsonContentLoader()
    words = await loader.load_vocabulary()
    passages = await loader.load_reading_passages()
    service = DailyChallengeService(words, passages)
    
    start_date = date.today()
    print(f"Simulating daily challenges starting from today ({start_date}):\n")
    
    for i in range(8):
        current_date = start_date + timedelta(days=i)
        challenge_type, content_id = service.get_challenge_for_date(current_date)
        title = service.get_challenge_title(challenge_type)
        desc = service.get_challenge_description(challenge_type)
        
        # Clean title of emojis to avoid encoding crash
        safe_title = title.replace("📚", "[VOCAB]").replace("📖", "[READING]")
        
        # Look up title/word name
        content_name = ""
        if challenge_type == "vocabulary_quiz":
            word_obj = next((w for w in words if w.id == content_id), None)
            content_name = f"Quiz starting with '{word_obj.word}' ({word_obj.transcription})" if word_obj else content_id
        elif challenge_type == "reading_passage":
            passage_obj = next((p for p in passages if p.id == content_id), None)
            content_name = f"Passage: '{passage_obj.title}'" if passage_obj else content_id
            
        lines = [
            f"Day {i} ({current_date}):",
            f"  Type: {safe_title} ({challenge_type})",
            f"  Content: {content_name}",
            f"  Description: {desc}",
            f"  Points: {service.get_reward_points(challenge_type)}",
            "-" * 50
        ]
        for line in lines:
            print(line.encode('ascii', 'ignore').decode('ascii'))

if __name__ == "__main__":
    asyncio.run(main())
