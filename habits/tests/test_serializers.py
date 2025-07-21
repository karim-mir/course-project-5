from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from habits.models import Habit
from habits.serializers import HabitSerializer

User = get_user_model()


class HabitSerializerTest(TestCase):
    def setUp(self):
        self.valid_data = {
            "action": "Test Habit",
            "is_public": True,
            "periodicity": 1,
            "time_to_complete": timedelta(seconds=120),
            "time": time(8, 0),
            "is_pleasant_habit": False,
            "reward": "smile",
            "place": "Home",
        }

    def test_serialization(self):
        habit = Habit.objects.create(
            user=None,
            action="Read",
            is_public=False,
            periodicity=1,
            time_to_complete=timedelta(seconds=120),
            time=time(20, 0),
        )
        serializer = HabitSerializer(habit)
        data = serializer.data
        self.assertEqual(data["action"], "Read")
        self.assertEqual(data["is_public"], False)
        self.assertIn("user", data)
        self.assertIn("id", data)

    def test_deserialization_and_validation_success(self):
        serializer = HabitSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_deserialization_and_validation_fail_periodicity(self):
        data = self.valid_data.copy()
        data["periodicity"] = 0  # invalid periodicity
        serializer = HabitSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_deserialization_and_validation_fail_time_to_complete(self):
        data = self.valid_data.copy()
        data["time_to_complete"] = -timedelta(minutes=1)  # invalid duration
        serializer = HabitSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
