from django.conf import settings
from django.db import models

from habits.validators import (validate_associated_habits,
                               validate_periodicity, validate_time_to_complete)


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь",
        help_text="Укажите пользователя",
    )
    place = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Место",
        help_text="Укажите место",
    )
    time = models.TimeField(
        verbose_name="Время",
        help_text="Укажите время выполнения привычки",
    )
    action = models.CharField(
        max_length=255,
        blank=False,
        verbose_name="Действие",
        help_text="Укажите действие",
    )
    is_pleasant_habit = models.BooleanField(
        default=False,
        verbose_name="Признак приятной привычки",
        help_text="Отметьте, если привычка является приятной",
    )
    associated_habits = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        verbose_name="Связанные привычки",
        help_text="Укажите связанные привычки",
    )
    periodicity = models.PositiveIntegerField(
        default=1,
        validators=[validate_periodicity],
        verbose_name="Периодичность (в днях)",
        help_text="Через сколько дней повторять привычку",
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Вознаграждение",
        help_text="Укажите вознаграждение",
    )
    time_to_complete = models.DurationField(
        validators=[validate_time_to_complete],
        verbose_name="Время на выполнение",
        help_text="Укажите предполагаемое время на выполнение привычки",
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Признак публичности",
        help_text="Отметьте, если привычка общедоступна",
    )

    def clean(self):
        if self.reward is not None:
            self.reward = self.reward.strip()
        validate_associated_habits(self)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["id"]
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"

    def __str__(self):
        return f"Я буду {self.action} в {self.time} в {self.place or '...'}"
