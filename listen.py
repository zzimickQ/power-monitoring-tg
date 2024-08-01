import nest_asyncio

nest_asyncio.apply()
import asyncio
import os
import psutil
import time

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


def add_user(new_user_id):
    users = get_users()
    print("prev users", users)
    users.add(str(new_user_id))
    print("updated users", users)
    with open("users.txt", "w") as file:
        file.writelines(users)


def get_users():
    # create file if it doesn't exist

    if not os.path.exists("users.txt"):
        with open("users.txt", "w") as file:
            file.write("")

    with open("users.txt", "r") as file:
        return set(file.readlines())


def set_last_state(state):
    with open("state.txt", "w") as file:
        file.write(state and "plugged" or "unplugged")


def get_last_state():
    # create file if it doesn't exist
    if not os.path.exists("state.txt"):
        with open("state.txt", "w") as file:
            file.write("unplugged")

    with open("state.txt", "r") as file:
        return file.read() == "plugged"


def is_plugged():
    return psutil.sensors_battery().power_plugged


async def start_power_state_loop(initial_state, callback):
    prev_is_plugged_state = initial_state
    while True:
        now_state = is_plugged()
        if prev_is_plugged_state != now_state:
            # state changed
            print(now_state and "Plugged in" or "Unplugged")
            await callback(now_state)

        prev_is_plugged_state = is_plugged()
        # time.sleep(1)
        await asyncio.sleep(1)


async def main():
    bot_token = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(bot_token).build()

    async def bot_job():
        async def register_user(
            update: Update, context: ContextTypes.DEFAULT_TYPE
        ) -> None:
            add_user(update.effective_user.id)
            await update.message.reply_text(
                f"Hello {update.effective_user.first_name}\n I will notify you when the power state changes."
            )

        app.add_handler(CommandHandler("start", register_user))

        print("Bot started")
        await app.run_polling()

    async def power_listener_job():
        async def on_state_change(is_plugged):
            set_last_state(is_plugged)
            print("State changed to", is_plugged and "plugged in" or "unplugged")
            users = get_users()
            async with app.bot as bot:
                for user_id in users:
                    print("sending message to", user_id)
                    await bot.sendMessage(
                        chat_id=user_id,
                        text=f"Power is {is_plugged and 'plugged in' or 'unplugged'} {is_plugged and '✅' or '❌'}",
                    )

        print("Starting power state loop")
        await start_power_state_loop(get_last_state(), on_state_change)

    # power_listener_tread = threading.Thread(target=power_listener_job, daemon=True)
    # power_listener_tread.start()

    # bot_job()
    # power_listener_tread.join()

    await asyncio.gather(bot_job(), power_listener_job())


if __name__ == "__main__":
    asyncio.run(main())
