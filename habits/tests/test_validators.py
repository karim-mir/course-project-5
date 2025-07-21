from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from habits.models import Habit
from habits.validators import (validate_associated_habits,
                               validate_periodicity, validate_time_to_complete)


class ValidatorsTest(TestCase):
    def setUp(self):
        self.habit = Habit.objects.create(
            action="Test habit",
            periodicity=1,
            time_to_complete=timedelta(seconds=60),
            time="08:00:00",
            is_pleasant_habit=False,
        )

    # validate_periodicity

    def test_validate_periodicity_valid(self):
        for valid_val in range(1, 8):
            try:
                validate_periodicity(valid_val)
            except ValidationError:
                self.fail(
                    f"validate_periodicity() raised ValidationError unexpectedly for {valid_val}"
                )

    def test_validate_periodicity_invalid(self):
        invalid_values = [0, 8, -1, 100]
        for val in invalid_values:
            with self.assertRaises(ValidationError) as cm:
                validate_periodicity(val)
            self.assertIn(
                _("Периодичность должна быть от 1 до 7 дней включительно."),
                cm.exception.messages,
            )

    # validate_time_to_complete

    def test_validate_time_to_complete_valid(self):
        # Граничные и корректные значения
        try:
            validate_time_to_complete(timedelta(seconds=1))
            validate_time_to_complete(timedelta(seconds=120))
        except ValidationError:
            self.fail(
                "validate_time_to_complete() raised ValidationError unexpectedly for valid value"
            )

    def test_validate_time_to_complete_zero_or_negative(self):
        with self.assertRaises(ValidationError) as cm:
            validate_time_to_complete(timedelta(seconds=0))
        self.assertIn(
            _("Время выполнения должно быть положительным числом."),
            cm.exception.messages,
        )

        with self.assertRaises(ValidationError) as cm:
            validate_time_to_complete(timedelta(seconds=-1))
        self.assertIn(
            _("Время выполнения должно быть положительным числом."),
            cm.exception.messages,
        )

    def test_validate_time_to_complete_above_max(self):
        with self.assertRaises(ValidationError) as cm:
            validate_time_to_complete(timedelta(seconds=121))
        self.assertIn(
            _("Время выполнения не должно превышать 120 секунд (2 минуты)."),
            cm.exception.messages,
        )

    # validate_associated_habits

    def test_validate_associated_habits_reward_and_associated_conflict(self):
        self.habit.reward = "Reward"
        self.habit.save()
        # Создаём связанную привычку
        related_habit = Habit.objects.create(
            action="Related habit",
            periodicity=1,
            time_to_complete=timedelta(seconds=30),
            time="09:00:00",
            is_pleasant_habit=True,
        )
        self.habit.associated_habits.add(related_habit)

        with self.assertRaises(ValidationError) as cm:
            validate_associated_habits(self.habit)
        self.assertIn(
            _("Нельзя указывать одновременно вознаграждение и связанные привычки."),
            cm.exception.messages,
        )

    def test_validate_associated_habits_non_pleasant_related(self):
        related_habit = Habit.objects.create(
            action="Non pleasant",
            periodicity=1,
            time_to_complete=timedelta(seconds=30),
            time="09:00:00",
            is_pleasant_habit=False,
        )
        self.habit.associated_habits.add(related_habit)
        with self.assertRaises(ValidationError) as cm:
            validate_associated_habits(self.habit)
        self.assertIn(
            _("Связанные привычки должны быть приятными."), cm.exception.messages
        )

    def test_validate_associated_habits_pleasant_habit_no_reward_or_associated(self):
        pleasant_habit = Habit.objects.create(
            action="Pleasant",
            periodicity=1,
            time_to_complete=timedelta(seconds=60),
            time="10:00:00",
            is_pleasant_habit=True,
            reward="",
        )

        # Проверяем, что без награды и связанных привычек - ошибки нет
        try:
            pleasant_habit.full_clean()
        except ValidationError:
            self.fail(
                "Вызов full_clean() выбросил ошибку для приятной привычки без связанных привычек и награды"
            )

        # Создаем связанную привычку
        other_habit = Habit.objects.create(
            action="Pleasant related",
            periodicity=1,
            time_to_complete=timedelta(seconds=30),
            time="11:00:00",
            is_pleasant_habit=True,
        )

        # Добавляем связанную привычку и ожидаем ошибку при сохранении / валидации
        pleasant_habit.associated_habits.set([other_habit])
        with self.assertRaises(ValidationError) as cm:
            pleasant_habit.full_clean()  # <- вот здесь ошибка будет
        self.assertIn(
            "У приятной привычки не может быть связанных привычек.", str(cm.exception)
        )

        # Убираем связанные привычки и добавляем награду, тоже должно быть ошибкой
        pleasant_habit.associated_habits.clear()
        pleasant_habit.reward = "Some reward"
        with self.assertRaises(ValidationError) as cm:
            pleasant_habit.full_clean()
        self.assertIn(
            "У приятной привычки не может быть вознаграждения.", str(cm.exception)
        )
