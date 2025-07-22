from django.contrib.auth import get_user_model
from django.test import TestCase

from users.serializers import RegisterSerializer

User = get_user_model()


class RegisterSerializerTest(TestCase):

    def test_create_user(self):
        data = {"email": "newuser@example.com", "password": "strongPassword123"}
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, data["email"])
        self.assertTrue(user.check_password(data["password"]))

    def test_password_write_only(self):
        data = {"email": "newuser2@example.com", "password": "strongPassword123"}
        serializer = RegisterSerializer(data=data)
        serializer.is_valid()

        self.assertNotIn("password", serializer.data)
