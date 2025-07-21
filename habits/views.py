from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, permissions, viewsets

from .models import Habit
from .paginators import HabitPagination
from .permissions import IsOwnerOrReadOnlyForPublic
from .serializers import HabitSerializer


# Список публичных привычек (только чтение)
class PublicHabitListAPIView(generics.ListAPIView):
    serializer_class = HabitSerializer
    pagination_class = HabitPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Habit.objects.filter(is_public=True)


# CRUD для привычек текущего пользователя с пагинацией
class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    pagination_class = HabitPagination
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnlyForPublic]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_public"]

    def get_queryset(self):
        # Возвращаем все привычки, чтобы при доступе к detail DRF мог найти объект
        # Проверка прав через IsOwnerOrReadOnlyForPublic контролирует доступ на изменение
        return Habit.objects.all().order_by("id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MyHabitViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = HabitSerializer
    pagination_class = HabitPagination
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # Показываем и создаём привычки только текущего пользователя
        return Habit.objects.filter(user=self.request.user).order_by("id")
