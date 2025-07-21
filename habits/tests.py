from datetime import time
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from habits.models import Habit

User = get_user_model()


class HabitAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="1234")
        self.other_user = User.objects.create_user(email="other@example.com", password="1234")

        self.public_habit = Habit.objects.create(
            user=self.other_user,
            action="Walk",
            is_public=True,
            periodicity=1,
            time_to_complete="0:01:30",
            time=time(8, 0),
        )

        self.private_habit = Habit.objects.create(
            user=self.user,
            action="Read",
            is_public=False,
            periodicity=1,
            time_to_complete="0:01:00",
            time=time(20, 0),
        )

    def test_list_public_habit(self):
        url = reverse('public-habits-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Только публичные привычки
        for habit in response.data.get('results', []):
            self.assertTrue(habit['is_public'])

    def test_list_own_habits_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('my-habit-list')  # изменилось на my-habit-list
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Только привычки текущего пользователя
        for habit in response.data.get('results', []):
            self.assertEqual(habit['user'], self.user.id)

    def test_create_habit(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('my-habit-list')  # создание через my-habits
        data = {
            "action": "Exercise",
            "is_public": False,
            "periodicity": 1,
            "time_to_complete": "0:02:00",
            "time": "08:00:00"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Habit.objects.filter(user=self.user, action="Exercise").exists())

    def test_update_and_delete_permissions(self):
        self.client.force_authenticate(user=self.other_user)
        # Привычка пользователя self.user, доступ на изменение которой должен быть запрещён
        url = reverse('habit-detail', args=[self.private_habit.pk])  # полный CRUD через habits

        # Попытка обновления чужой привычки - ожидаем 403 Forbidden
        response = self.client.patch(url, {"action": "Hack"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Попытка удаления чужой привычки - ожидаем 403 Forbidden
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
