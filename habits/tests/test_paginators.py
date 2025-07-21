from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from habits.models import Habit

User = get_user_model()


class HabitPaginationTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="1234")
        for i in range(30):
            Habit.objects.create(
                user=self.user,
                action=f"Action {i}",
                periodicity=1,
                time_to_complete=timedelta(seconds=60),
                time=time(8, 0),
            )
        self.client.force_authenticate(user=self.user)

    def test_default_page_size(self):
        # Использование 'habits:my-habit-list'
        url = reverse("habits:my-habit-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 5)  # по умолчанию 5

    def test_custom_page_size_within_limit(self):
        # Использование 'habits:my-habit-list'
        url = reverse("habits:my-habit-list") + "?page_size=10"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 10)

    def test_page_size_above_max(self):
        # Использование 'habits:my-habit-list'
        url = reverse("habits:my-habit-list") + "?page_size=50"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 20)  # max_page_size=20

    def test_pagination_page_two(self):
        # Использование 'habits:my-habit-list'
        url = reverse("habits:my-habit-list") + "?page=2"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Проверяем, что возвращается следующая порция результатов (оставшиеся элементы)
        self.assertGreaterEqual(len(response.data["results"]), 1)
