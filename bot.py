# SWILL CASINO v3.0 (FIXED)
import telebot
import random
import requests
import json
 
TOKEN = "8661353701:AAGw3QxlyzxdykjsQY4JJBQvPLHmJWzit2U"
ADMIN_ID = "7984990535"
CRYPTO_TOKEN = "576779:AA2tutCVoEvyW1yMJcu5F1qxmVfSKgilfRJ"
CRYPTO_API = "https://pay.crypt.bot/api"
 
USERS = {}
PENDING = {}
 
bot = telebot.TeleBot(TOKEN)
 
def create_invoice(amount_rub, uid):
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    data = {
        "asset": "USDT",
        "amount": round(amount_rub / 90, 2),
        "description": "SWILL CASINO",
        "hidden_message": str(uid),
        "expires_in": 1800
    }
    r = requests.post(f"{CRYPTO_API}/createInvoice", json=data, headers=headers)
    if r.status_code == 200:
        inv = r.json()["result"]
        PENDING[inv["invoice_id"]] = uid
        return inv
    return None
 
def check_payment(inv_id):
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    r = requests.post(f"{CRYPTO_API}/getInvoices", json={"invoice_ids": [inv_id]}, headers=headers)
    if r.status_code == 200:
        return r.json()["result"]["items"][0]["status"]
    return "error"
 
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if uid not in USERS:
        USERS[uid] = {"balance": 0, "name": message.from_user.username or "Player", "games": 0, "dep": 0}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎰 Слоты", "🎲 Рулетка")
    markup.row("💵 Баланс", "📥 Пополнить")
    markup.row("💸 Вывод", "🎁 Бонус")
    bot.send_message(message.chat.id, f"🔥 SWILL CASINO\nБаланс: {USERS[uid]['balance']} RUB", reply_markup=markup)
 
@bot.message_handler(func=lambda m: m.text == "📥 Пополнить")
def dep_menu(message):
    markup = telebot.types.InlineKeyboardMarkup()
    for amt in [500, 1000, 5000, 10000]:
        markup.add(telebot.types.InlineKeyboardButton(f"💎 {amt} RUB", callback_data=f"dep_{amt}"))
    bot.send_message(message.chat.id, "Выбери сумму (USDT TRC20):", reply_markup=markup)
 
@bot.callback_query_handler(func=lambda c: c.data.startswith("dep_"))
def dep_create(call):
    uid = call.from_user.id
    amt = int(call.data.split("_")[1])
    inv = create_invoice(amt, uid)
    if inv:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💵 Оплатить", url=inv["pay_url"]))
        markup.add(telebot.types.InlineKeyboardButton("🔄 Проверить", callback_data=f"chk_{inv['invoice_id']}_{amt}"))
        bot.send_message(call.message.chat.id, f"Счёт: {amt} RUB\nДействует 30 мин", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "❌ Ошибка")
    bot.answer_callback_query(call.id)
 
@bot.callback_query_handler(func=lambda c: c.data.startswith("chk_"))
def dep_check(call):
    _, inv_id, amt = call.data.split("_")
    inv_id = int(inv_id)
    amt = int(amt)
    status = check_payment(inv_id)
    if status == "paid":
        uid = PENDING.get(inv_id)
        if uid in USERS:
            USERS[uid]["balance"] += amt
            USERS[uid]["dep"] += amt
            bot.send_message(call.message.chat.id, f"✅ +{amt} RUB!")
            del PENDING[inv_id]
    elif status == "expired":
        bot.send_message(call.message.chat.id, "⏰ Истёк")
        del PENDING[inv_id]
    else:
        bot.send_message(call.message.chat.id, "⏳ Ждём оплату...")
    bot.answer_callback_query(call.id)
 
@bot.message_handler(func=lambda m: m.text == "💸 Вывод")
def withdraw_menu(message):
    uid = message.from_user.id
    bal = USERS[uid]["balance"]
    if bal < 500:
        bot.send_message(message.chat.id, "Мин. вывод 500 RUB")
        return
    bot.send_message(message.chat.id, f"Доступно: {bal} RUB\nВведи USDT адрес (TRC20):")
 
@bot.message_handler(func=lambda m: len(m.text) == 34 and m.text.startswith("T"))
def withdraw_do(message):
    uid = message.from_user.id
    bal = USERS[uid]["balance"]
    fee = bal * 0.03
    to_send = bal - fee
    bot.send_message(message.chat.id, f"📤 Вывод создан!\nСумма: {bal} RUB\nКомиссия 3%: {fee:.1f} RUB\nК получению: {to_send:.1f} RUB\nАдрес: {message.text}\n⏳ До 24ч")
    USERS[uid]["balance"] = 0
 
@bot.message_handler(func=lambda m: m.text == "🎰 Слоты")
def slots(message):
    uid = message.from_user.id
    if USERS[uid]["balance"] < 10:
        bot.send_message(message.chat.id, "❌ Мин. 10 RUB")
        return
    s = random.choices(["🍒","🍋","🍊","7️⃣","⭐","💎"], k=3)
    if random.random() < 0.25:
        s = [s[0]]*3
        w = random.randint(30, 200)
        USERS[uid]["balance"] += w
        r = f"🎉 {s} +{w} RUB"
    else:
        USERS[uid]["balance"] -= 10
        r = f"💩 {s} -10 RUB"
    USERS[uid]["games"] += 1
    bot.send_message(message.chat.id, r)
 
@bot.message_handler(func=lambda m: m.text == "🎲 Рулетка")
def roulette_menu(message):
    uid = message.from_user.id
    if USERS[uid]["balance"] < 50:
        bot.send_message(message.chat.id, "❌ Мин. 50 RUB")
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("🔴 Красное x2", callback_data="r_red"),
               telebot.types.InlineKeyboardButton("⚫ Чёрное x2", callback_data="r_black"))
    markup.row(telebot.types.InlineKeyboardButton("0️⃣ Зеро x14", callback_data="r_zero"))
    bot.send_message(message.chat.id, "Ставка 50 RUB:", reply_markup=markup)
 
@bot.callback_query_handler(func=lambda c: c.data.startswith("r_"))
def roulette_spin(call):
    uid = call.from_user.id
    USERS[uid]["balance"] -= 50
    spin = random.randint(1, 15)
    ch = call.data.split("_")[1]
    if (ch == "red" and 1 <= spin <= 7) or (ch == "black" and 8 <= spin <= 14):
        w = 100
    elif ch == "zero" and spin == 15:
        w = 700
    else:
        w = 0
    USERS[uid]["balance"] += w
    USERS[uid]["games"] += 1
    emoji = "🔴" if spin <= 7 else "⚫" if spin <= 14 else "0️⃣"
    bot.edit_message_text(text=f"🎲 {emoji} {spin} {'+'+str(w) if w else '-50'} RUB",
                          chat_id=call.message.chat.id, message_id=call.message.message_id)
 
@bot.message_handler(func=lambda m: m.text == "💵 Баланс")
def bal(message):
    u = USERS[message.from_user.id]
    bot.send_message(message.chat.id, f"💰 {u['balance']} RUB | 🎮 Игр: {u['games']}")
 
@bot.message_handler(func=lambda m: m.text == "🎁 Бонус")
def bonus(message):
    uid = message.from_user.id
    b = random.randint(50, 200)
    USERS[uid]["balance"] += b
    bot.send_message(message.chat.id, f"🎁 +{b} RUB!")
 
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, f"👥 Игроков: {len(USERS)}")
 
print("SWILL CASINO v3.0 STARTED")
bot.polling(none_stop=True)
