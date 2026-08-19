# How to Run the TOEFL Telegram Bot

## Prerequisites

✅ All dependencies are already installed:
- Python 3.14.3
- aiogram 3.29.1
- SQLAlchemy 2.0.51
- aiosqlite 0.22.1

✅ Bot token is configured in `.env` file

## Running the Bot

### Option 1: Simple Run (Foreground)
```bash
python -m app.main
```
The bot will run in the current terminal. Press `Ctrl+C` to stop.

### Option 2: Background Run
```bash
# Windows PowerShell
Start-Process python -ArgumentList "-m", "app.main" -WindowStyle Hidden

# Or using pythonw (no console window)
pythonw -m app.main
```

### Option 3: Using a Process Manager (Recommended for Production)

Install pm2 (Node.js process manager):
```bash
npm install -g pm2
pm2 start "python -m app.main" --name toefl-bot
pm2 status
pm2 logs toefl-bot
pm2 stop toefl-bot
pm2 restart toefl-bot
```

## Troubleshooting

### Error: "Conflict: terminated by other getUpdates request"

This means another bot instance is already running. Only ONE instance can run at a time.

**To fix:**

1. **Check if bot is running on another device:**
   - Phone app
   - Another computer
   - Another terminal window
   - Cloud server

2. **Stop the other instance first**, then start a new one.

3. **Find running Python processes:**
   ```powershell
   # Windows PowerShell
   Get-Process python | Select-Object Id, ProcessName, StartTime
   
   # Kill a specific process by ID
   Stop-Process -Id <process_id>
   ```

   ```bash
   # Linux/Mac
   ps aux | grep "app.main"
   kill <process_id>
   ```

### Bot Not Responding

1. Check if the bot is actually running:
   ```bash
   # The log should show "Run polling for bot @toefl_teach_bot"
   ```

2. Verify bot token in `.env` file is correct

3. Check internet connection

4. Look at the logs for errors

## Testing the Bot

Once running, open Telegram and:

1. Search for `@toefl_teach_bot`
2. Send `/start` command
3. You should see the main menu with buttons:
   - 📚 Vocabulary
   - 📖 Reading
   - 🎯 Daily Challenge
   - 📊 Statistics
   - 🏆 Achievements

## Test Achievements

To test the achievements system:

1. Click **📚 Vocabulary** → **📝 Mini Test**
2. Answer all 5 questions correctly (100% score)
3. After completion, you'll see:
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

4. Click **🏆 Achievements** to see all your unlocked achievements

## Bot Features

- **📚 Vocabulary Practice**: Learn 300 TOEFL words with translations and examples
- **📝 Mini Tests**: 5-question vocabulary quizzes with instant feedback
- **📖 Reading Comprehension**: Full passages with 5 questions each
- **📊 Statistics**: Track your progress, accuracy, and learning stats
- **🏆 Achievements**: Unlock 15 achievements across 5 categories
- **🔥 Streak Tracking**: Maintain daily practice streaks

## Database

The bot uses SQLite database (`database.db`) created automatically on first run.

To reset the database:
```bash
# Delete the database file
rm database.db

# Or use the reset script
python scripts/reset_database.py
```

## Logs

The bot logs all activity to the console. For production, consider redirecting to a file:

```bash
python -m app.main > bot.log 2>&1
```

Or use Python's logging configuration to write to files.

## Support

For issues or questions:
1. Check logs for error messages
2. Verify `.env` configuration
3. Ensure only one bot instance is running
4. Check that all dependencies are installed: `pip list`

## Quick Commands Summary

```bash
# Run bot
python -m app.main

# Run tests
python -m pytest tests/ -v

# Generate new vocabulary
python scripts/generate_vocab.py

# Reset database
python scripts/reset_database.py
```
