import os
from datetime import datetime

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          CommandHandler, ContextTypes)

from habits.models import Habit

User = get_user_model()


class Command(BaseCommand):
    help = "Запуск Telegram бота"

    def handle(self, *args, **options):
        TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        User = get_user_model()

        # Обернём функцию получения пользователя в sync_to_async
        @sync_to_async
        def get_user_by_email(email):
            return User.objects.get(email=email)

        @sync_to_async
        def save_user(user):
            user.save()

        async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat_id = update.effective_chat.id
            args = context.args  # аргументы после команды /register

            if not args:
                await update.message.reply_text(
                    "Пожалуйста, укажи email после команды /register"
                )
                return

            email = args[0]

            try:
                user = await get_user_by_email(email)
                user.telegram_chat_id = chat_id
                await save_user(user)
                await update.message.reply_text(
                    f"Аккаунт {email} успешно привязан к этому чату!"
                )
            except User.DoesNotExist:
                await update.message.reply_text(
                    f"Пользователь с email {email} не найден."
                )
            except Exception as e:
                self.stderr.write(f"Ошибка при привязке telegram_chat_id: {e}")
                await update.message.reply_text("Произошла ошибка, попробуйте позже.")

        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "Привет! Чтобы получать напоминания, зарегистрируй аккаунт командой:\n"
                "/register your_email@example.com"
            )

        # Функция вывода привычек
        @sync_to_async
        def get_user_habits(user):
            return list(
                user.habit_set.all()
            )  # или habits, смотря как называется реляция

        async def habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                user = await sync_to_async(User.objects.get)(
                    telegram_chat_id=update.effective_chat.id
                )
            except User.DoesNotExist:
                await update.message.reply_text(
                    "Вы не зарегистрированы. Используйте /register"
                )
                return

            habits = await get_user_habits(user)
            if not habits:
                await update.message.reply_text("У вас пока нет привычек.")
                return

            message = "Ваши привычки:\n"
            keyboard = []
            for habit in habits:
                message += f"- {habit.title} в {habit.time.strftime('%H:%M')}\n"
                # Добавим кнопку удаления рядом с каждой привычкой
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"Удалить {habit.title}", callback_data=f"delete_{habit.id}"
                        )
                    ]
                )

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)

        # Обработчик callback от кнопок
        async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()

            data = query.data
            if data.startswith("delete_"):
                habit_id = int(data.split("_")[1])
                chat_id = update.effective_chat.id

                try:
                    user = await sync_to_async(User.objects.get)(
                        telegram_chat_id=chat_id
                    )
                except User.DoesNotExist:
                    await query.edit_message_text(
                        "Вы не зарегистрированы. Используйте /register"
                    )
                    return

                try:
                    habit = await sync_to_async(user.habit_set.get)(id=habit_id)
                except Habit.DoesNotExist:  # Или Habit.DoesNotExist
                    await query.edit_message_text("Ошибка: привычка не найдена.")
                    return

                await sync_to_async(habit.delete)()
                await query.edit_message_text("Привычка удалена.")

        # Команда для добавления привычки
        async def addhabit(update: Update, context: ContextTypes.DEFAULT_TYPE):
            args = context.args
            if len(args) < 2:
                await update.message.reply_text(
                    "Использование: /addhabit <название> <время в формате ЧЧ:ММ>.\n"
                    "Пример: /addhabit Утренняя зарядка 07:00"
                )
                return

            title = " ".join(args[:-1])
            time_str = args[-1]

            try:
                habit_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                await update.message.reply_text(
                    "Время должно быть в формате ЧЧ:ММ, например 07:00"
                )
                return

            try:
                user = await sync_to_async(User.objects.get)(
                    telegram_chat_id=update.effective_chat.id
                )
            except User.DoesNotExist:
                await update.message.reply_text(
                    "Вы не зарегистрированы. Используйте /register"
                )
                return

            habit = Habit(title=title, time=habit_time, user=user)
            await sync_to_async(habit.save)()

            await update.message.reply_text(
                f"Привычка '{title}' на {habit_time.strftime('%H:%M')} добавлена."
            )

        application = ApplicationBuilder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("register", register))
        application.add_handler(CommandHandler("habits", habits))
        application.add_handler(CommandHandler("addhabit", addhabit))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.run_polling()
