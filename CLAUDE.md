# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TOEFL Telegram Bot — a Telegram bot for TOEFL exam preparation built with **Clean Architecture** principles.

**Tech Stack:**
- Python 3.12+
- aiogram 3.x (Telegram Bot framework)
- SQLAlchemy 2.0 (async ORM)
- SQLite with aiosqlite
- pytest (testing)

## Running the Bot

### Setup
```bash
# Install dependencies
pip install -e .

# Set up environment (copy and edit .env.example)
cp .env.example .env
# Edit .env with your BOT_TOKEN and ADMIN_IDS

# Run the bot
python -m app.main
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/unit/test_statistics_service.py -v

# Run integration tests
python -m pytest tests/integration/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Development Scripts
```bash
# Generate vocabulary data (creates 300 TOEFL words)
python scripts/generate_vocab.py

# Validate JSON content structure
python scripts/validate_content.py

# Reset database (destructive - deletes database.db)
python scripts/reset_database.py

# Seed database with test data
python scripts/seed_database.py
```

**Note:** `generate_vocab.py` preserves the first 20 existing words exactly and generates 280 new academic vocabulary words across multiple categories (Science, Environment, Technology, History, Psychology, Economics). The script validates the output using `JsonContentLoader` after generation.

## Architecture

### Clean Architecture Layers

The project follows strict Clean Architecture with dependency inversion:

```
┌─────────────────────────────────────────────┐
│  bot/                (Framework Layer)      │
│  ├─ handlers/   Telegram command handlers   │
│  ├─ keyboards/  UI inline/reply keyboards   │
│  ├─ callbacks/  Callback data classes       │
│  └─ states/     FSM state machines          │
└─────────────────────────────────────────────┘
                    ↓ depends on
┌─────────────────────────────────────────────┐
│  application/         (Use Cases)           │
│  ├─ use_cases/  Business orchestration      │
│  ├─ dto/        Data transfer objects       │
│  └─ interfaces/ Repository abstractions     │
└─────────────────────────────────────────────┘
                    ↓ depends on
┌─────────────────────────────────────────────┐
│  domain/            (Business Logic)        │
│  ├─ entities/   Core domain models          │
│  ├─ services/   Domain business logic       │
│  └─ enums.py    Domain enumerations         │
└─────────────────────────────────────────────┘
                    ↑ implemented by
┌─────────────────────────────────────────────┐
│  infrastructure/    (External Adapters)     │
│  ├─ database/   SQLAlchemy models & repos   │
│  ├─ content/    JSON content loaders        │
│  └─ telegram/   Message formatters          │
└─────────────────────────────────────────────┘
```

**Key Principle:** Domain layer has ZERO external dependencies. Infrastructure implements domain interfaces.

### New Features (Recently Added)

The following features have been added and follow the established patterns:

#### Achievements System
- **Location:** `bot/handlers/achievements.py`, `domain/services/achievement_service.py`
- **Use Case:** `application/use_cases/check_achievements.py`
- **Pattern:** Achievements are checked after test completion using `AchievementService.check_unlockable_achievements()`
- **Integration:** Call `CheckAchievementsUseCase.execute()` after any test or significant user action, passing current `UserStatistics`
- **Data:** Achievement definitions in `data/achievements.json` with requirement types: `completed_tasks`, `words_learned`, `streak_days`, `correct_answers`, `accuracy_percentage`, `perfect_test`, `vocabulary_tests_completed`, `reading_tests_completed`

#### Streak Tracking System
- **Location:** `domain/services/streak_service.py`
- **Use Case:** `application/use_cases/update_streak.py`
- **Pattern:** `StreakService.calculate_new_streak()` compares `last_activity_date` with today's date to determine if streak continues, breaks, or stays the same
- **Database:** `User.last_activity_date` (DATE), `User.streak_days` (current streak), `User.best_streak` (all-time best)
- **Important:** Always update `last_activity_date` when user completes any practice activity

#### User Statistics System
- **Entity:** `domain/entities/user_statistics.py` - immutable dataclass for statistics calculations
- **Use Case:** `application/use_cases/get_user_statistics.py`
- **Pattern:** `UserStatistics.from_user_data()` calculates derived fields (accuracy_percentage) from raw DB values
- **Usage:** Use this entity when checking achievements or displaying statistics, not raw User model fields

### Critical Patterns

#### 1. Session Management (Manual Pattern)
No middleware — sessions are managed manually in handlers:

```python
@router.message(Command("start"))
async def handler(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],  # injected by dispatcher
) -> None:
    async with session_factory() as session:
        repo = UserRepository(session)
        use_case = RegisterUserUseCase(repo)
        await use_case.execute(...)
        await session.commit()  # explicit commit
```

`session_factory` is stored in `dispatcher["session_factory"]` at startup (see `app/main.py:37`).

#### 2. FSM State Serialization
Domain entities must support FSM serialization for callback navigation:

```python
# All quiz/test entities need:
def to_state_dict(self) -> dict[str, Any]:
    # Convert to JSON-serializable dict for FSM storage
    
@classmethod
def from_state_dict(cls, data: dict[str, Any]) -> Self:
    # Restore from FSM storage
```

See `VocabularyQuizQuestion` and `ReadingPassage` for examples. This is required because aiogram's FSM storage cannot serialize domain objects directly.

#### 3. Repository Pattern
Each aggregate root has a repository in `infrastructure/database/repositories.py`:

- `UserRepository` — user CRUD, stat increments (correct_answers, completed_tasks, words_learned)
- `AttemptRepository` — attempt history tracking
- `VocabularyProgressRepository` — spaced repetition tracking (repetitions, mastered, next_review_date)
- `AchievementRepository` — achievement unlocking and queries

Repositories operate on **ORM models** (`infrastructure/database/models.py`), not domain entities. This is a known deviation from pure Clean Architecture for pragmatic reasons.

#### 4. Content Loading
JSON content (`data/*.json`) is loaded via `JsonContentLoader`:

```python
from infrastructure.content.json_content_loader import JsonContentLoader

loader = JsonContentLoader()
words = await loader.load_vocabulary()           # list[VocabularyWord]
passages = await loader.load_reading_passages()  # list[ReadingPassage]
```

**Performance Note:** Content is reloaded on every request. For production, cache at startup or use a content service.

#### 5. Router Registration
New feature modules require router registration in `bot/dispatcher.py`:

```python
from bot.handlers import achievements, common, reading, statistics, vocabulary

def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(common.router)
    dispatcher.include_router(vocabulary.router)
    dispatcher.include_router(reading.router)
    dispatcher.include_router(statistics.router)
    dispatcher.include_router(achievements.router)  # ← add new routers here
    return dispatcher
```

**Important:** Router order matters. The first matching handler wins. Keep `common.router` first as it contains the `/start` command and main menu handler.

## Adding New Features

### Pattern: Following Vocabulary/Reading Examples

When adding a new practice mode (e.g., Listening, Speaking):

1. **Create domain entities** in `domain/entities/`
   - Must have `to_state_dict()` / `from_state_dict()` if used in FSM
   - Use `@dataclass(frozen=True, slots=True)` for immutability

2. **Add content loader method** in `infrastructure/content/json_content_loader.py`
   ```python
   async def load_listening_exercises(self) -> list[ListeningExercise]:
       data = await self.load_json("listening_exercises.json")
       return [ListeningExercise.from_mapping(item) for item in data]
   ```

3. **Create use cases** in `application/use_cases/`
   - `Start<Feature>UseCase` — select content, prepare quiz
   - `Submit<Feature>AnswerUseCase` — handle responses, update DB

4. **Implement bot layer**:
   - `bot/callbacks/<feature>.py` — callback data class (inherit from `CallbackData`)
   - `bot/states/<feature>.py` — FSM states (inherit from `StatesGroup`)
   - `bot/keyboards/<feature>.py` — keyboard builders (return `InlineKeyboardMarkup`)
   - `bot/handlers/<feature>.py` — handlers (~200-300 lines typical)

5. **Register router** in `bot/dispatcher.py`

6. **Add button** to `bot/keyboards/main_menu.py`

7. **Update attempts tracking**: Use existing `attempts` table with new `content_type` (e.g., "listening_exercise")

8. **Integrate achievements and streak tracking**:
   - After test completion, call `UpdateStreakUseCase` to update streak
   - Call `GetUserStatisticsUseCase` to get current statistics
   - Call `CheckAchievementsUseCase` to unlock any new achievements
   - Display newly unlocked achievements to the user

### Attempt Tracking Pattern

All practice activities record attempts in a generic table:

```python
await attempt_repo.create(
    user_id=user_id,
    content_type="vocabulary_mini_test",  # or "reading_passage", etc.
    content_id="vocab_001",               # specific item ID
    is_correct=True,
)
```

Statistics aggregate across all `content_type` values automatically.

### Achievement Integration Pattern

After completing any test or significant milestone:

```python
from datetime import date
from application.use_cases.update_streak import UpdateStreakUseCase
from application.use_cases.get_user_statistics import GetUserStatisticsUseCase
from application.use_cases.check_achievements import CheckAchievementsUseCase

# 1. Update streak
streak_use_case = UpdateStreakUseCase(user_repo)
await streak_use_case.execute(user_id=user.id, activity_date=date.today())

# 2. Get current statistics
stats_use_case = GetUserStatisticsUseCase(user_repo, attempt_repo)
statistics = await stats_use_case.execute(telegram_id=telegram_user.id)

# 3. Check for newly unlocked achievements
achievement_service = AchievementService(await JsonContentLoader().load_achievements())
check_achievements_use_case = CheckAchievementsUseCase(
    achievement_service, achievement_repo
)
newly_unlocked = await check_achievements_use_case.execute(
    user_id=user.id,
    statistics=statistics,
    test_completed=True,
    test_score=correct_count,
    test_total=total_questions,
    test_type="vocabulary_mini_test",  # or "reading_passage"
)

# 4. Display achievements
if newly_unlocked:
    achievement_text = "\n\n🏆 <b>New Achievements Unlocked!</b>\n"
    for ach in newly_unlocked:
        achievement_text += f"{ach.emoji} <b>{ach.title}</b>\n"
    # Append to result message
```

## Database

### Schema
- `users` — user profiles and aggregate stats (words_learned, streak_days, best_streak, correct_answers, completed_tasks, last_activity_date, etc.)
- `vocabulary_progress` — spaced repetition tracking (repetitions, mastered, next_review_date, last_review_date)
- `attempts` — universal attempt history (content_type, content_id, is_correct, created_at)
- `achievements` — unlocked achievements (user_id, achievement_type, unlocked_at)

**Important Fields:**
- `User.last_activity_date` (DATE) — tracks the calendar date of last activity for streak calculation
- `User.last_activity` (DATETIME) — auto-updated timestamp for general activity tracking
- `User.streak_days` — current consecutive days streak
- `User.best_streak` — longest streak ever achieved

### Initialization
Database is auto-created via `init_database()` in `app/main.py:28` on startup using `Base.metadata.create_all`. No migrations configured (alembic.ini is empty placeholder).

**Important:** Schema changes require manual `database.db` deletion and recreation. There is no migration system.

### Direct Access
```bash
sqlite3 database.db
.schema users
SELECT * FROM attempts WHERE user_id = 1 ORDER BY created_at DESC LIMIT 10;
```

## Testing Strategy

- **Unit tests** (`tests/unit/`) — test services and domain logic in isolation, no DB
- **Integration tests** (`tests/integration/`) — test repositories and use cases with real SQLite DB

**Configuration:** `pyproject.toml` sets `asyncio_mode = "auto"` for automatic async test handling.

**Fixtures:** 
- `tests/conftest.py` — pytest configuration with async fixtures:
  - `db_engine` — session-wide in-memory SQLite engine
  - `session_factory` — creates async session maker
  - `db_session` — transactional session that rolls back after each test
- `tests/fixtures/` — reusable test data (users, attempts, sample content)

**Fixture Usage Pattern:**
```python
@pytest_asyncio.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
        await session.rollback()  # Automatic rollback after test
```

### Running Individual Tests
```bash
# Single test file
python -m pytest tests/unit/test_statistics_service.py -v

# Single test function
python -m pytest tests/unit/test_statistics_service.py::test_calculate_accuracy -v

# With markers (if defined)
python -m pytest -m "not slow" -v
```

## Configuration

Environment variables (`.env`):
- `BOT_TOKEN` — Telegram bot token from @BotFather (required)
- `ADMIN_IDS` — Comma-separated admin user IDs for admin features
- `DATABASE_URL` — SQLAlchemy connection string (default: `sqlite+aiosqlite:///./database.db`)
- `DEBUG` — Enable debug logging (default: `false`)

Loaded via `pydantic-settings` in `app/config.py`. Access with `get_settings()` (cached singleton).

## Known Architecture Deviations

These are intentional shortcuts for MVP development:

1. **No Unit of Work** — `infrastructure/database/unit_of_work.py` exists but is empty; transactions managed manually with `session.commit()`

2. **No DI Container** — `app/container.py` is empty; dependencies created inline in handlers

3. **Empty Middleware Files** — `bot/middlewares/` files exist but are empty; session injection via dispatcher dict

4. **ORM Models as Entities** — `domain/entities/user.py` is empty; ORM model in `infrastructure/database/models.py:User` is used directly (violates Clean Architecture)

5. **No Content Caching** — JSON files reloaded on every request (acceptable for current scale <1000 users)

6. **No Migrations** — Alembic configured but not used; schema changes require database deletion

When scaling or refactoring, address these in order: UoW → DI Container → Middleware → Entity/Model separation → Caching → Migrations.

## Content Data Format

All content in `data/*.json`:

- `vocabulary.json` — vocabulary words with translations, examples, level (B1/B2/C1)
- `reading_passages.json` — reading comprehension texts with 5 questions each (includes explanations)
- `achievements.json` — achievement definitions with conditions
- `daily_challenges.json` — (placeholder, not yet implemented)

**Content Structure:** Each item must have:
- Unique `id` field (string)
- All required fields per entity (see domain entities for validation)

Add new content by editing JSON directly. Run `scripts/validate_content.py` after changes to catch schema errors.

## Handler Structure Pattern

Typical handler flow (see `bot/handlers/vocabulary.py` and `bot/handlers/reading.py`):

1. **Entry handler** — Command or button click, loads content, sets FSM state
2. **Question handler** — Displays question with inline keyboard
3. **Answer handler** — Validates answer, updates DB, shows feedback, advances or finishes
4. **Finished handler** — Shows results, offers navigation (retry, new content, back to menu)

All handlers receive `session_factory` from dispatcher and manage their own session lifecycle.

## Common Pitfalls

1. **Forgetting `await session.commit()`** — Changes won't persist without explicit commit
2. **Missing FSM state cleanup** — Call `await state.clear()` when leaving a flow to prevent stale data
3. **Not registering routers** — New handlers won't work until router is added to dispatcher
4. **Content loader errors** — If JSON is malformed, bot will crash on startup or first use
5. **Callback data size limits** — Telegram limits callback_data to 64 bytes; use FSM state for large data
6. **Forgetting streak updates** — Always call `UpdateStreakUseCase` after any practice activity to maintain accurate streak tracking
7. **Missing achievement checks** — After test completion, check for new achievements using `CheckAchievementsUseCase`
8. **Using User model fields directly for statistics** — Use `UserStatistics` entity via `GetUserStatisticsUseCase` for calculated fields like accuracy_percentage
