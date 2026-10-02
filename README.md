# TOEFL Preparation Telegram Bot

A professional, feature-rich TOEFL preparation bot built with **aiogram 3.x**, **SQLAlchemy (Async)**, and **Clean Architecture**.

## ✨ Features

- 📚 **Vocabulary**: 350+ TOEFL academic words with definitions, examples, and spaced repetition (Leitner SRS).
- 📖 **Reading Practice**: Academic passages across science, biology, history, environment, and technology with multiple-choice questions and instant explanations.
- 🎧 **Listening Practice**: Academic audio lectures with MP3 audio playback and comprehension questions.
- 🎯 **Daily Challenges**: Daily interactive TOEFL tasks with streak tracking.
- 🔥 **Streaks & Retention**: Tracks consecutive practice days and best streaks.
- 🏆 **Achievements**: 10 automatic achievement badges based on learning milestones.
- 📊 **User Statistics**: Accuracy rates, completed tasks, and learning progress.

---

## 🏗️ Architecture

```
app/              # Application entrypoint, configuration, and logging
bot/              # Telegram handlers, keyboards, states (FSM), and callbacks
domain/           # Core business entities, models, and domain services
application/      # Use cases, interfaces, and DTOs
infrastructure/   # Database engine, SQLAlchemy models, repositories, content loader
data/             # JSON datasets (vocabulary, reading, listening, achievements) and audio
```

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Install Dependencies

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your Bot Token:

```bash
cp .env.example .env
```

Edit `.env`:
```env
BOT_TOKEN=your_telegram_bot_token_from_botfather
ADMIN_IDS=123456789
DATABASE_URL=sqlite+aiosqlite:///./database.db
DEBUG=false
```

### 3. Run Tests

```bash
pytest
```

### 4. Start the Bot

```bash
python -m app.main
```

---

## 🐳 Docker & Cloud Deployment (Railway)

The repository is production-ready for containerized deployment:

- **Dockerfile**: Built on `python:3.12-slim` with `ffmpeg` installed.
- **Persistent Volume**: Mount a persistent volume at `/data` with `DATABASE_URL=sqlite+aiosqlite:////data/database.db`.
- **railway.toml**: Pre-configured with `restartPolicyType = "ON_FAILURE"`.
