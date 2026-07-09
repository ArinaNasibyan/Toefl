import asyncio
import json
from pathlib import Path
from typing import Any

from domain.entities.vocabulary_word import VocabularyWord


class JsonContentLoader:
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
        data = await self.load_json(relative_path)
        if not isinstance(data, list):
            raise ValueError("Vocabulary content must be a JSON array")

        return [VocabularyWord.from_mapping(item) for item in data]

    def _resolve_path(self, relative_path: Path | str) -> Path:
        file_path = (self._base_path / relative_path).resolve()
        base_path = self._base_path.resolve()

        if not file_path.is_relative_to(base_path):
            raise ValueError("Content path must stay inside the data directory")

        if not file_path.exists():
            raise FileNotFoundError(f"Content file not found: {file_path}")

        return file_path
