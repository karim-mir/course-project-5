from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from habits.models import Habit
from habits.permissions import IsOwnerOrReadOnlyForPublic
from datetime import time, timedelta

User = get_user_model()

class IsOwnerOrReadOnlyForPublicTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsOwnerOrReadOnlyForPublic()

        self.owner = User.objects.create_user(email='owner@example.com', password='12345')
        self.other_user = User.objects.create_user(email='other@example.com', password='12345')

        self.public_habit = Habit.objects.create(
            user=self.owner,
            action="Public Habit",
            is_public=True,
            periodicity=1,
            time_to_complete=timedelta(seconds=60),
            time=time(10, 0),
        )
        self.private_habit = Habit.objects.create(
            user=self.owner,
            action="Private Habit",
            is_public=False,
            periodicity=1,
            time_to_complete=timedelta(seconds=60),
            time=time(11, 0),
        )

    def get_request(self, method, user):
        wsgi_request = self.factory.generic(method, '/fake-url/')
        request = Request(wsgi_request)
        request.user = user
        return request

    def test_safe_methods_allowed_for_public(self):
        for method in SAFE_METHODS:
            request = self.get_request(method, user=self.other_user)
            self.assertTrue(self.permission.has_object_permission(request, None, self.public_habit))

    def test_safe_methods_allowed_for_owner_private(self):
        for method in SAFE_METHODS:
            request = self.get_request(method, user=self.owner)
            self.assertTrue(self.permission.has_object_permission(request, None, self.private_habit))

    def test_safe_methods_denied_for_not_owner_private(self):
        for method in SAFE_METHODS:
            request = self.get_request(method, user=self.other_user)
            self.assertFalse(self.permission.has_object_permission(request, None, self.private_habit))

    def test_write_methods_allowed_only_for_owner(self):
        for method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            request = self.get_request(method, user=self.owner)
            self.assertTrue(self.permission.has_object_permission(request, None, self.public_habit))
            self.assertTrue(self.permission.has_object_permission(request, None, self.private_habit))

    def test_write_methods_denied_for_not_owner(self):
        for method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            request = self.get_request(method, user=self.other_user)
            self.assertFalse(self.permission.has_object_permission(request, None, self.public_habit))
            self.assertFalse(self.permission.has_object_permission(request, None, self.private_habit))
