from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HabitViewSet, MyHabitViewSet, PublicHabitListAPIView

router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habit")
router.register(r"my-habits", MyHabitViewSet, basename="my-habit")

urlpatterns = [
    path("public-habits/", PublicHabitListAPIView.as_view(), name="public-habits-list"),
    path("", include(router.urls)),
]
