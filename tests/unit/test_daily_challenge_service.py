from datetime import date
import pytest
from domain.entities.vocabulary_word import VocabularyWord
from domain.entities.reading_passage import ReadingPassage
from domain.services.daily_challenge_service import DailyChallengeService

def test_daily_challenge_service_alternates_by_date() -> None:
    # Set up sample vocab words and reading passages
    words = [
        VocabularyWord(id="v1", word="abundant", translation="plentiful", transcription="/əˈbʌndənt/", example="ex", level="B2"),
        VocabularyWord(id="v2", word="acquire", translation="obtain", transcription="/əˈkwaɪər/", example="ex", level="B1")
    ]
    passages = [
        ReadingPassage(id="p1", title="Title 1", text="Text 1", questions=()),
        ReadingPassage(id="p2", title="Title 2", text="Text 2", questions=())
    ]
    
    service = DailyChallengeService(vocabulary_words=words, reading_passages=passages)
    
    # 2024-01-01 is epoch base in service, which has days_since_epoch = 0 (even) -> vocabulary
    challenge_type, content_id = service.get_challenge_for_date(date(2024, 1, 1))
    assert challenge_type == "vocabulary_quiz"
    assert content_id == "v1"
    
    # 2024-01-02 has days_since_epoch = 1 (odd) -> reading
    challenge_type, content_id = service.get_challenge_for_date(date(2024, 1, 2))
    assert challenge_type == "reading_passage"
    assert content_id == "p2" # 1 % 2 = 1 -> passages[1]

def test_daily_challenge_service_metadata() -> None:
    service = DailyChallengeService(vocabulary_words=[], reading_passages=[])
    
    # Vocab challenge info
    assert service.get_challenge_title("vocabulary_quiz") == "📚 Vocabulary Challenge"
    assert "vocab" in service.get_challenge_description("vocabulary_quiz").lower()
    assert service.get_reward_points("vocabulary_quiz") == 10
    
    # Reading challenge info
    assert service.get_challenge_title("reading_passage") == "📖 Reading Challenge"
    assert "read" in service.get_challenge_description("reading_passage").lower()
    assert service.get_reward_points("reading_passage") == 15
