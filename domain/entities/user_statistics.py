from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserStatistics:
    completed_tasks: int
    correct_answers: int
    accuracy_percentage: int
    current_streak: int
    best_streak: int
    words_learned: int
    vocabulary_tests_completed: int = 0
    reading_tests_completed: int = 0
    listening_tests_completed: int = 0

    @classmethod
    def from_user_data(
        cls,
        *,
        completed_tasks: int,
        correct_answers: int,
        total_attempts: int,
        current_streak: int,
        best_streak: int,
        words_learned: int,
        vocabulary_tests_completed: int = 0,
        reading_tests_completed: int = 0,
        listening_tests_completed: int = 0,
    ) -> "UserStatistics":
        accuracy_percentage = 0
        if total_attempts > 0:
            accuracy_percentage = round((correct_answers / total_attempts) * 100)

        return cls(
            completed_tasks=completed_tasks,
            correct_answers=correct_answers,
            accuracy_percentage=accuracy_percentage,
            current_streak=current_streak,
            best_streak=best_streak,
            words_learned=words_learned,
            vocabulary_tests_completed=vocabulary_tests_completed,
            reading_tests_completed=reading_tests_completed,
            listening_tests_completed=listening_tests_completed,
        )
