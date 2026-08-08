import asyncio
import json
from pathlib import Path
from typing import Any

from domain.entities.achievement import Achievement
from domain.entities.vocabulary_word import VocabularyWord


class JsonContentLoader:
    _vocabulary_cache = None
    _reading_passages_cache = None
    _achievements_cache = None
    _listening_passages_cache = None

    def __init__(self, base_path: Path | str = "data") -> None:
        self._base_path = Path(base_path)

    async def load_json(self, relative_path: Path | str) -> Any:
        return await asyncio.to_thread(self.load_json_sync, relative_path)

    def load_json_sync(self, relative_path: Path | str) -> Any:
        file_path = self._resolve_path(relative_path)

        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    async def load_vocabulary(
        self,
        relative_path: Path | str = "vocabulary.json",
    ) -> list[VocabularyWord]:
        if JsonContentLoader._vocabulary_cache is not None:
            return JsonContentLoader._vocabulary_cache

        data = await self.load_json(relative_path)
        if not isinstance(data, list):
            raise ValueError("Vocabulary content must be a JSON array")

        res = [VocabularyWord.from_mapping(item) for item in data]
        JsonContentLoader._vocabulary_cache = res
        return res

    async def load_reading_passages(
        self,
        relative_path: Path | str = "reading_passages.json",
    ) -> list:
        if JsonContentLoader._reading_passages_cache is not None:
            return JsonContentLoader._reading_passages_cache

        from domain.entities.question import ReadingQuestion
        from domain.entities.reading_passage import ReadingPassage

        data = await self.load_json(relative_path)
        if not isinstance(data, list):
            raise ValueError("Reading passages content must be a JSON array")

        passages = []
        for item in data:
            questions = [
                ReadingQuestion(
                    id=str(q["id"]),
                    question=str(q["question"]),
                    options=tuple(str(opt) for opt in q["options"]),
                    correct_index=int(q["correct_index"]),
                    explanation=str(q["explanation"]),
                )
                for q in item["questions"]
            ]
            passage = ReadingPassage(
                id=str(item["id"]),
                title=str(item["title"]),
                text=str(item["text"]),
                questions=tuple(questions),
            )
            passages.append(passage)

        JsonContentLoader._reading_passages_cache = passages
        return passages

    async def load_achievements(
        self,
        relative_path: Path | str = "achievements.json",
    ) -> list[Achievement]:
        if JsonContentLoader._achievements_cache is not None:
            return JsonContentLoader._achievements_cache

        data = await self.load_json(relative_path)
        if not isinstance(data, list):
            raise ValueError("Achievements content must be a JSON array")

        res = [Achievement.from_dict(item) for item in data]
        JsonContentLoader._achievements_cache = res
        return res

    async def load_listening_passages(
        self,
        relative_path: Path | str = "listening_passages.json",
    ) -> list:
        if JsonContentLoader._listening_passages_cache is not None:
            return JsonContentLoader._listening_passages_cache

        from domain.entities.listening_question import ListeningQuestion
        from domain.entities.listening_passage import ListeningPassage

        data = await self.load_json(relative_path)
        if not isinstance(data, list):
            raise ValueError("Listening passages content must be a JSON array")

        passages = []
        for item in data:
            questions = [
                ListeningQuestion(
                    id=str(q["id"]),
                    question=str(q["question"]),
                    options=tuple(str(opt) for opt in q["options"]),
                    correct_index=int(q["correct_index"]),
                    explanation=str(q["explanation"]),
                )
                for q in item["questions"]
            ]
            passage = ListeningPassage(
                id=str(item["id"]),
                title=str(item["title"]),
                type=str(item["type"]),
                audio_file=str(item["audio_file"]),
                transcript=str(item["transcript"]),
                questions=tuple(questions),
            )
            passages.append(passage)

        JsonContentLoader._listening_passages_cache = passages
        return passages

    def _resolve_path(self, relative_path: Path | str) -> Path:
        file_path = (self._base_path / relative_path).resolve()
        base_path = self._base_path.resolve()

        if not file_path.is_relative_to(base_path):
            raise ValueError("Content path must stay inside the data directory")

        if not file_path.exists():
            raise FileNotFoundError(f"Content file not found: {file_path}")

        return file_path
