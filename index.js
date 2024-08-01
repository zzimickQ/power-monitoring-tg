const isCharging = require("is-charging");
const rx = require("rxjs");
const TelegramBot = require("node-telegram-bot-api");
const fs = require("fs");

const token = process.env.BOT_TOKEN;
const bot = new TelegramBot(token, { polling: true });

async function batteryMonitoringLoop() {
  const behaviorSubject = new rx.Subject();
  (async () => {
    while (true) {
      const charging = await isCharging();
      behaviorSubject.next(charging);
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  })();
  return behaviorSubject;
}

const users = {
  users: new Set(),
  getUsers() {
    if (this.users.size === 0) {
      try {
        const data = fs.readFileSync("users.txt", "utf8");
        this.users = new Set(data.split("\n"));
      } catch (e) {
        console.log(e);
      }
    }
    return this.users;
  },
  userExists(userId) {
    return this.users.has(userId);
  },
  addUser(userId) {
    this.users.add(userId);
    fs.writeFileSync("users.txt", Array.from(this.users).join("\n"));
  },
  sendToAll(message) {
    for (let user of this.getUsers()) {
      bot.sendMessage(user, message).catch((e) => console.log(e));
    }
  },
};

async function main() {
  const batteryMonitoring = await batteryMonitoringLoop(false);

  bot.on("message", (update) => {
    if (update.text === "/start") {
      users.addUser(update.chat.id);
      bot.sendMessage(
        update.chat.id,
        `Hello ${update.chat.first_name}\nI will notify you when the power state changes.`
      );
    }
  });

  batteryMonitoring
    .pipe(rx.skip(2), rx.distinctUntilChanged())
    .subscribe((charging) => {
      users.sendToAll(
        `Power is ${charging ? "connected" : "disconnected"} ${
          charging ? "✅" : "❌"
        }`
      );
    });

  users.sendToAll(
    `Power back online monitoring started. You will be notified when the power state changes.`
  );

  console.log("Power monitoring started");
}

main();
