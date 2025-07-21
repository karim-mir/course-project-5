from datetime import time, timedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model

from habits.models import Habit

User = get_user_model()

class HabitModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="1234")
        self.pleasant_habit = Habit.objects.create(
            user=self.user,
            action="Meditate",
            is_pleasant_habit=True,
            periodicity=3,
            time_to_complete=timedelta(seconds=60),
            time=time(7, 0),
        )
        self.normal_habit = Habit.objects.create(
            user=self.user,
            action="Read",
            is_pleasant_habit=False,
            periodicity=1,
            time_to_complete=timedelta(seconds=120),
            time=time(20, 0),
        )

    def test_str_method_with_place(self):
        habit = Habit(
            user=self.user,
            action="Walk",
            time=time(6, 30),
            place="Park"
        )
        self.assertEqual(str(habit), "Я буду Walk в 06:30:00 в Park")

    def test_str_method_without_place(self):
        habit = Habit(
            user=self.user,
            action="Run",
            time=time(6, 30),
            place=None
        )
        self.assertEqual(str(habit), "Я буду Run в 06:30:00 в ...")

    def test_validate_periodicity_valid(self):
        habit = Habit(
            user=self.user,
            action="Write",
            periodicity=5,
            time_to_complete=timedelta(seconds=60),
            time=time(8, 0),
        )
        # Should not raise
        habit.full_clean()

    def test_validate_periodicity_invalid(self):
        habit = Habit(
            user=self.user,
            action="Write",
            periodicity=0,  # invalid: less than 1
            time_to_complete=timedelta(seconds=60),
            time=time(8, 0),
        )
        with self.assertRaises(ValidationError) as cm:
            habit.full_clean()
        self.assertIn("periodicity", cm.exception.message_dict)

    def test_validate_time_to_complete_valid(self):
        habit = Habit(
            user=self.user,
            action="Write",
            periodicity=1,
            time_to_complete=timedelta(seconds=120),
            time=time(8, 0),
        )
        habit.full_clean()  # should not raise

    def test_validate_time_to_complete_invalid(self):
        habit = Habit(
            user=self.user,
            action="Write",
            periodicity=1,
            time_to_complete=timedelta(seconds=121),  # too large
            time=time(8, 0),
        )
        with self.assertRaises(ValidationError) as cm:
            habit.full_clean()
        self.assertIn("time_to_complete", cm.exception.message_dict)

    def test_validate_associated_habits_reward_and_associated_conflict(self):
        habit = Habit(
            user=self.user,
            action="Conflicting Habit",
            reward="Good job",
            is_pleasant_habit=False,
            periodicity=1,
            time_to_complete=timedelta(seconds=60),
            time=time(9, 0),
        )
        # Создаём связанную привычку (приятную)
        pleasant_habit = Habit.objects.create(
            user=self.user,
            action="Pleasant",
            is_pleasant_habit=True,
            periodicity=1,
            time_to_complete=timedelta(seconds=60),
            time=time(9, 30),
        )
        habit.save()
        habit.associated_habits.add(pleasant_habit)

        with self.assertRaises(ValidationError) as cm:
            habit.clean()
        self.assertIn("Нельзя указывать одновременно вознаграждение и связанные привычки", str(cm.exception))

    def test_validate_associated_habits_non_pleasant_related(self):
        habit = Habit(
            user=self.user,
            action="Test Habit",
            is_pleasant_habit=False,
            periodicity=1,
            time_to_complete=timedelta(seconds=60),
            time=time(9, 0),
        )
        habit.save()

        # Добавляем связанную неприятную привычку
        habit2 = Habit.objects.create(
            user=self.user,
            action="Unpleasant",
            is_pleasant_habit=False,  # не приятная
            periodicity=1,
            time_to_complete=timedelta(seconds=60),
            time=time(9, 0),
        )
        habit.associated_habits.add(habit2)

        with self.assertRaises(ValidationError) as cm:
            habit.clean()
        self.assertIn("Связанные привычки должны быть приятными", str(cm.exception))

    def test_validate_associated_habits_pleasant_habit_no_reward_or_associated(self):
        habit = Habit(
            user=self.user,
            action="PleasantHabit",
            is_pleasant_habit=True,
            reward="",
            periodicity=1,
            time_to_complete=timedelta(seconds=60),
            time=time(9, 0),
        )
        habit.save()

        # Проверяем, что clean не выдает ошибок если нет reward и нет associated
        try:
            habit.clean()
        except ValidationError:
            self.fail("Проверка clean() упала для приятной привычки без награды и связанных")

        # Нельзя, если есть reward
        habit.reward = "Some reward"
        with self.assertRaises(ValidationError) as cm:
            habit.clean()
        self.assertIn("У приятной привычки не может быть вознаграждения", str(cm.exception))

        # Сбросим reward и добавим associated
        habit.reward = ""
        habit.save()

        habit2 = Habit.objects.create(
            user=self.user,
            action="Pleasant 2",
            is_pleasant_habit=True,
            periodicity=1,
            time_to_complete=timedelta(seconds=60),
            time=time(10, 0),
        )
        habit.associated_habits.add(habit2)

        with self.assertRaises(ValidationError) as cm:
            habit.clean()
        self.assertIn("У приятной привычки не может быть связанных привычек", str(cm.exception))
