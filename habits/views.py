from rest_framework import viewsets, generics, permissions
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Habit
from .serializers import HabitSerializer
from .paginators import HabitPagination
from .permissions import IsOwnerOrReadOnlyForPublic

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
    filterset_fields = ['is_public']  # опционально, если нужно фильтровать

    def get_queryset(self):
        user = self.request.user
        return Habit.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
