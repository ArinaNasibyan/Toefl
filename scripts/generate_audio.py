import asyncio
import os
import json
import re
from pathlib import Path
from pydub import AudioSegment
import edge_tts

# Register static ffmpeg paths so pydub can find the binaries automatically
import static_ffmpeg
static_ffmpeg.add_paths()


async def generate_lecture_audio(text: str, output_path: Path) -> None:
    # Use standard male professor neural voice for the biology lecture
    voice = "en-US-GuyNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


async def generate_conversation_audio(text: str, output_path: Path) -> None:
    # Aria (Female Student) and Guy (Male Professor) voices
    voices = {
        "student": "en-US-AriaNeural",
        "professor": "en-US-GuyNeural"
    }

    # Split the transcript into lines and parse turns
    lines = text.split("\n")
    turns = []
    
    # We will generate individual MP3s for each dialogue turn
    temp_files = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Parse "Student: text..." or "Professor: text..."
        match = re.match(r"^(Student|Professor):\s*(.*)$", line, re.IGNORECASE)
        if match:
            role = match.group(1).lower()
            speech_text = match.group(2)
            voice = voices.get(role, "en-US-GuyNeural")
            
            temp_file = Path(f"temp_turn_{i}.mp3")
            communicate = edge_tts.Communicate(speech_text, voice)
            await communicate.save(str(temp_file))
            
            turns.append(temp_file)
            temp_files.append(temp_file)
        else:
            # Fallback if line format is not strictly "Speaker: Text"
            temp_file = Path(f"temp_turn_{i}.mp3")
            communicate = edge_tts.Communicate(line, "en-US-GuyNeural")
            await communicate.save(str(temp_file))
            turns.append(temp_file)
            temp_files.append(temp_file)

    if not turns:
        raise ValueError("No conversation turns parsed successfully")

    # Glue the turns together using pydub, adding a small silence pause of 600ms between dialogue exchanges
    combined_audio = AudioSegment.from_mp3(str(turns[0]))
    silence = AudioSegment.silent(duration=600)  # 600ms pause

    for turn_file in turns[1:]:
        segment = AudioSegment.from_mp3(str(turn_file))
        combined_audio = combined_audio + silence + segment

    # Export the merged dialogue
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined_audio.export(str(output_path), format="mp3")

    # Clean up temporary individual turn MP3s
    for f in temp_files:
        try:
            if f.exists():
                os.remove(f)
        except Exception as e:
            print(f"Error removing temp file {f}: {e}")


async def main() -> None:
    print("Starting TOEFL Listening audio generation script...")
    data_dir = Path("data")
    json_path = data_dir / "listening_passages.json"
    audio_dir = data_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    if not json_path.exists():
        print(f"JSON data file not found at: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        passages = json.load(f)

    for passage in passages:
        passage_id = passage["id"]
        passage_type = passage["type"]
        transcript = passage["transcript"]
        output_file = audio_dir / f"{passage_id}.mp3"

        print(f"Generating audio for: {passage['title']} ({passage_type}) -> {output_file.name}...")

        if passage_type == "lecture":
            await generate_lecture_audio(transcript, output_file)
        elif passage_type == "conversation":
            await generate_conversation_audio(transcript, output_file)
        else:
            print(f"Unknown passage type: {passage_type}")

    print("Listening audio generation complete! All files generated successfully in data/audio/.")


if __name__ == "__main__":
    asyncio.run(main())
