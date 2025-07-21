from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_periodicity(value):
    if not (1 <= value <= 7):
        raise ValidationError(
            _("Периодичность должна быть от 1 до 7 дней включительно.")
        )


def validate_time_to_complete(value):
    max_seconds = 120
    if value.total_seconds() > max_seconds:
        raise ValidationError(
            _("Время выполнения не должно превышать 120 секунд (2 минуты).")
        )


def validate_associated_habits(habit_instance):
    reward_filled = bool(habit_instance.reward)
    associated = habit_instance.associated_habits.all() if habit_instance.pk else []

    if reward_filled and associated:
        raise ValidationError(
            _("Нельзя указывать одновременно вознаграждение и связанные привычки.")
        )

    if associated:
        for h in associated:
            if not h.is_pleasant_habit:
                raise ValidationError(_("Связанные привычки должны быть приятными."))

    if habit_instance.is_pleasant_habit:
        if reward_filled:
            raise ValidationError(
                _("У приятной привычки не может быть вознаграждения.")
            )
        if associated:
            raise ValidationError(
                _("У приятной привычки не может быть связанных привычек.")
            )
