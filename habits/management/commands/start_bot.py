import os
from django.core.management.base import BaseCommand
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

User = get_user_model()

class Command(BaseCommand):
    help = 'Запуск Telegram бота'

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
                await update.message.reply_text("Пожалуйста, укажи email после команды /register")
                return

            email = args[0]

            try:
                user = await get_user_by_email(email)
                user.telegram_chat_id = chat_id
                await save_user(user)
                await update.message.reply_text(f"Аккаунт {email} успешно привязан к этому чату!")
            except User.DoesNotExist:
                await update.message.reply_text(f"Пользователь с email {email} не найден.")
            except Exception as e:
                self.stderr.write(f"Ошибка при привязке telegram_chat_id: {e}")
                await update.message.reply_text("Произошла ошибка, попробуйте позже.")

        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "Привет! Чтобы получать напоминания, зарегистрируй аккаунт командой:\n"
                "/register your_email@example.com"
            )

        application = ApplicationBuilder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("register", register))
        application.run_polling()
