from django.test import SimpleTestCase
from django.urls import reverse, resolve

from habits.views import HabitViewSet, MyHabitViewSet, PublicHabitListAPIView


class TestURLS(SimpleTestCase):
    def test_public_habits_url(self):
        url = reverse("habits:public-habits-list")
        assert url == "/habits/public-habits/"
        resolver = resolve(url)
        assert resolver.func.view_class == PublicHabitListAPIView

    def test_habits_list_url(self):
        url = reverse("habits:habit-list")
        assert url == "/habits/"
        resolver = resolve(url)
        assert hasattr(resolver.func, "cls")
        assert resolver.func.cls == HabitViewSet

    def test_habit_detail_url(self):
        url = reverse("habits:habit-detail", kwargs={"pk": 1})
        assert url == "/habits/1/"
        resolver = resolve(url)
        assert hasattr(resolver.func, "cls")
        assert resolver.func.cls == HabitViewSet

    def test_my_habits_list_url(self):
        url = reverse("habits:my-habit-list")
        assert url == "/habits/my-habits/"
        resolver = resolve(url)
        assert hasattr(resolver.func, "cls")
        assert resolver.func.cls == MyHabitViewSet

    # Если в MyHabitViewSet нет RetrieveModelMixin, удалите этот тест
    def test_my_habit_detail_url(self):
        url = reverse("habits:my-habit-detail", kwargs={"pk": 1})
        assert url == "/habits/my-habits/1/"
        resolver = resolve(url)
        assert hasattr(resolver.func, "cls")
        assert resolver.func.cls == MyHabitViewSet
