from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UsersAPITestCase(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.token_url = reverse("token_obtain_pair")
        self.token_refresh_url = reverse("token_refresh")

        self.user_data = {
            "email": "testuser@example.com",
            "password": "strong_password_123",
            "password2": "strong_password_123",  # если в регистрационном API требуется подтверждение
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())

    def test_token_obtain(self):
        # Создаём пользователя напрямую
        User.objects.create_user(
            email=self.user_data["email"], password=self.user_data["password"]
        )

        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"],
        }
        response = self.client.post(self.token_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что мы получили access и refresh токены
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_refresh(self):
        # Предварительно получаем токен
        User.objects.create_user(
            email=self.user_data["email"], password=self.user_data["password"]
        )
        login_response = self.client.post(
            self.token_url,
            {
                "email": self.user_data["email"],
                "password": self.user_data["password"],
            },
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        # Запрос на обновление токена
        response = self.client.post(
            self.token_refresh_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


class UserManagerTests(TestCase):
    def test_create_user_success(self):
        user = User.objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, "user@example.com")
        self.assertTrue(user.check_password("testpass123"))

    def test_create_user_no_email(self):
        with self.assertRaisesMessage(ValueError, "Email must be set"):
            User.objects.create_user(email=None, password="testpass123")

    def test_create_superuser_success(self):
        admin_user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass"
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_active)

    def test_create_superuser_missing_is_staff(self):
        with self.assertRaisesMessage(ValueError, "Superuser must have is_staff=True."):
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpass",
                is_staff=False,
            )

    def test_create_superuser_missing_is_superuser(self):
        with self.assertRaisesMessage(
            ValueError, "Superuser must have is_superuser=True."
        ):
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpass",
                is_superuser=False,
            )


class UserModelTests(TestCase):
    def test_str_returns_email(self):
        user = User(email="testuser@example.com")
        self.assertEqual(str(user), "testuser@example.com")

    def test_user_fields_defaults(self):
        user = User.objects.create_user(email="user2@example.com", password="password")
        # Поскольку avatar — ImageFieldFile, он не None, а пустой файл, проверяем имя
        self.assertFalse(user.avatar.name)
        self.assertEqual(user.city, "")
        self.assertFalse(user.phone)
