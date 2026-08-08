# Achievements System - Implementation Guide

## Overview

The achievements system is **fully implemented** in the TOEFL Telegram Bot. Users earn achievements by completing tests, maintaining streaks, and reaching milestones.

## Features Implemented

### 1. Achievement Types

The system includes **15 achievements** across 5 categories:

#### 📊 Milestones
- **🎯 First Steps** - Complete your first test (1 task)
- **💪 Century Club** - Answer 100 questions correctly
- **👑 Elite Learner** - Answer 500 questions correctly

#### 📚 Vocabulary
- **📚 Vocabulary Rookie** - Complete 5 vocabulary mini tests
- **📖 Vocabulary Expert** - Complete 20 vocabulary mini tests
- **✍️ Word Collector** - Learn 50 words
- **🎓 Word Master** - Learn 100 words

#### 📖 Reading
- **📰 Reading Rookie** - Complete 5 reading tests
- **📕 Reading Expert** - Complete 20 reading tests

#### 🎯 Skills
- **💯 Perfectionist** - Score 100% on any test
- **⭐ Flawless Master** - Score 100% on 5 tests
- **🎯 Sharp Shooter** - Achieve 80% accuracy overall
- **🎖️ Sniper** - Achieve 90% accuracy overall

#### 🔥 Streaks
- **🔥 Weekly Warrior** - Maintain a 7-day streak
- **🏆 Monthly Champion** - Maintain a 30-day streak

### 2. Achievement Unlocking

Achievements are automatically checked and unlocked after:
- ✅ Completing vocabulary mini tests
- ✅ Completing reading comprehension tests
- ✅ Any practice activity that updates user statistics

### 3. User Interface

#### Main Menu
- **🏆 Achievements** button in the main menu
- Shows all unlocked achievements grouped by category
- Displays progress: "Unlocked: X/15"

#### Test Results
After completing a test, users see:
- Test score and percentage
- Streak notification (increased or current)
- **🎉 New Achievements Unlocked!** section (if any)
  - Achievement emoji and title
  - Achievement description

### 4. Achievement Display Format

```
🏆 Your Achievements

Unlocked: 5/15

📊 Milestones
🎯 First Steps
   Complete your first test

📚 Vocabulary
📚 Vocabulary Rookie
   Complete 5 vocabulary mini tests

🔥 Streaks
🔥 Weekly Warrior
   Maintain a 7-day streak
```

### 5. Integration Points

#### Vocabulary Mini Test (`bot/handlers/vocabulary.py`)
- After completing the test, calls:
  1. `UpdateStreakUseCase` - updates user's streak
  2. `GetUserStatisticsUseCase` - gets current statistics
  3. `CheckAchievementsUseCase` - checks for new achievements
- Displays newly unlocked achievements in results

#### Reading Test (`bot/handlers/reading.py`)
- Same integration as vocabulary mini test
- Uses `test_type="reading_passage"`

#### Achievements Handler (`bot/handlers/achievements.py`)
- `/achievements` command or 🏆 Achievements button
- Loads all achievements from `data/achievements.json`
- Fetches user's unlocked achievements from database
- Displays formatted list grouped by category

## Technical Architecture

### Domain Layer
- **`domain/entities/achievement.py`** - Achievement entity
- **`domain/services/achievement_service.py`** - Business logic for checking requirements

### Application Layer
- **`application/use_cases/check_achievements.py`** - Use case for checking and unlocking achievements

### Infrastructure Layer
- **`infrastructure/database/repositories.py`** - `AchievementRepository` for database operations
- **`infrastructure/content/json_content_loader.py`** - Loads achievements from JSON

### Bot Layer
- **`bot/handlers/achievements.py`** - Achievement display handler
- **`bot/keyboards/achievements.py`** - Achievement keyboard builder
- **`bot/callbacks/achievements.py`** - Achievement callback data

### Data
- **`data/achievements.json`** - Achievement definitions with requirements

## Database Schema

### `achievements` table
```sql
CREATE TABLE achievements (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    achievement_type TEXT NOT NULL,  -- achievement ID from JSON
    unlocked_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Requirement Types

The system supports the following requirement types:

1. **completed_tasks** - Total number of tests completed
2. **words_learned** - Total unique words learned
3. **streak_days** - Current consecutive day streak
4. **correct_answers** - Total correct answers
5. **accuracy_percentage** - Overall accuracy percentage
6. **perfect_test** - Number of tests with 100% score
7. **vocabulary_tests_completed** - Number of vocabulary tests
8. **reading_tests_completed** - Number of reading tests

## Testing

All tests pass successfully:

```bash
# Run achievement tests
python -m pytest tests/ -v -k achievement

# Results: 7 passed
✅ test_achievement_unlock_integration
✅ test_check_completed_tasks_achievement
✅ test_check_vocabulary_tests_achievement
✅ test_check_perfect_test_achievement
✅ test_perfect_test_not_achieved_when_not_perfect
✅ test_already_unlocked_achievements_not_returned
✅ test_no_achievements_when_requirements_not_met
```

## How to Add New Achievements

1. **Add to `data/achievements.json`**:
```json
{
  "id": "new_achievement_id",
  "title": "Achievement Title",
  "description": "What the user accomplished",
  "emoji": "🏅",
  "category": "milestone",
  "requirement": {
    "type": "completed_tasks",
    "value": 10
  }
}
```

2. **That's it!** The system will automatically:
   - Load the new achievement
   - Check requirements after tests
   - Display it when unlocked
   - Show it in the achievements list

## User Flow Example

1. User completes a vocabulary mini test
2. System checks all achievement requirements
3. User unlocks "First Steps" achievement (completed 1 task)
4. Bot displays:
   ```
   📝 Mini Test Complete
   
   Your score: 5/5 (100%)
   
   🔥 Streak increased! 1 days in a row!
   
   🎉 New Achievements Unlocked!
   
   🎯 First Steps
      Complete your first test
   
   💯 Perfectionist
      Score 100% on any test
   ```

## Current Status

✅ **Fully Implemented and Working**
- Achievement system is integrated with both vocabulary and reading tests
- All 15 achievements are defined and functional
- User interface displays achievements correctly
- Tests verify correct behavior
- Streak tracking works alongside achievements

## Next Steps (Optional Enhancements)

These features are **not required** but could be added in the future:

1. **Achievement notifications** - Push notifications when unlocking
2. **Progress tracking** - Show progress toward locked achievements
3. **Achievement rewards** - Unlock special features or content
4. **Leaderboards** - Compare achievements with other users
5. **Rare achievements** - Time-limited or special event achievements
6. **Achievement statistics** - Track when and how achievements were unlocked

---

**Note**: The system is production-ready and requires no additional work to function.
