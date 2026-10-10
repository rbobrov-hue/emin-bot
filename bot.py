import asyncio, json, os, sqlite3, datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from emin import ITEMS, OPTIONS, NAMES, score, level
from texts import WELCOME, DESCRIPTIONS, FINAL, SOURCE

TOKEN = os.environ.get("BOT_TOKEN") or os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_ID = os.environ.get("ADMIN_ID")
DATA_DIR = os.environ.get("DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)
db = sqlite3.connect(os.path.join(DATA_DIR, "results.db"))
db.execute("CREATE TABLE IF NOT EXISTS results (ts TEXT, user_id INTEGER, answers TEXT, scores TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS progress (user_id INTEGER PRIMARY KEY, answers TEXT)")
db.commit()

def get_prog(uid):
    r = db.execute("SELECT answers FROM progress WHERE user_id=?", (uid,)).fetchone()
    return json.loads(r[0]) if r else None

def set_prog(uid, ans):
    db.execute("REPLACE INTO progress VALUES (?,?)", (uid, json.dumps(ans))); db.commit()

def question(i):
    kb = [[InlineKeyboardButton(text=o, callback_data=f"a:{i}:{v}")] for v, o in enumerate(OPTIONS)]
    if i > 0:
        kb.append([InlineKeyboardButton(text="← Назад", callback_data=f"back:{i}")])
    return f"Вопрос {i+1} из {len(ITEMS)}\n\n{ITEMS[i][0]}", InlineKeyboardMarkup(inline_keyboard=kb)

def report(s):
    lines = [f"<b>{NAMES['ОЭИ']}: {s['ОЭИ']}</b> — {level('ОЭИ', s['ОЭИ'])} уровень\n"]
    for k in ("МЭИ","ВЭИ","ПЭ","УЭ"):
        lines.append(f"{NAMES[k]}: {s[k]} — {level(k, s[k])}")
    lines.append("\n<b>Субшкалы</b>")
    for k in ("МП","МУ","ВП","ВУ","ВЭ"):
        lines.append(f"• {NAMES[k]}: {s[k]} — {level(k, s[k])}\n  <i>{DESCRIPTIONS[k]}</i>")
    lines += ["", FINAL, "", SOURCE]
    return "\n".join(lines)

dp = Dispatcher()

@dp.message(CommandStart())
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Начать", callback_data="go")]])
    await m.answer(WELCOME, reply_markup=kb)

@dp.message(Command("restart"))
async def restart(m: Message):
    set_prog(m.from_user.id, [])
    t, kb = question(0); await m.answer(t, reply_markup=kb)

@dp.callback_query(F.data == "go")
async def go(c: CallbackQuery):
    set_prog(c.from_user.id, [])
    t, kb = question(0); await c.message.edit_text(t, reply_markup=kb); await c.answer()

@dp.callback_query(F.data.startswith("back:"))
async def back(c: CallbackQuery):
    ans = get_prog(c.from_user.id) or []
    ans = ans[:-1]; set_prog(c.from_user.id, ans)
    t, kb = question(len(ans)); await c.message.edit_text(t, reply_markup=kb); await c.answer()

@dp.callback_query(F.data.startswith("a:"))
async def answer(c: CallbackQuery):
    _, i, v = c.data.split(":"); i, v = int(i), int(v)
    ans = get_prog(c.from_user.id)
    if ans is None or i != len(ans):   # устаревшая кнопка
        await c.answer("Эта кнопка уже неактуальна"); return
    ans.append(v); set_prog(c.from_user.id, ans)
    if len(ans) < len(ITEMS):
        t, kb = question(len(ans)); await c.message.edit_text(t, reply_markup=kb)
    else:
        s = score(ans)
        db.execute("INSERT INTO results VALUES (?,?,?,?)",
                   (datetime.datetime.now().isoformat(), c.from_user.id, json.dumps(ans), json.dumps(s, ensure_ascii=False)))
        db.execute("DELETE FROM progress WHERE user_id=?", (c.from_user.id,)); db.commit()
        await c.message.edit_text("Тест завершён. Ваши результаты:")
        await c.message.answer(report(s), parse_mode="HTML")
        await c.message.answer("Пройти заново: /restart")
        if ADMIN_ID:
            u = c.from_user
            who = f"@{u.username}" if u.username else u.full_name
            short = ", ".join(f"{k} {s[k]}" for k in ("ОЭИ","МЭИ","ВЭИ","ПЭ","УЭ","МП","МУ","ВП","ВУ","ВЭ"))
            try:
                await c.bot.send_message(int(ADMIN_ID), f"Новый результат: {who} (id {u.id})\n{short}\nОтветы: {''.join(map(str, ans))}")
            except Exception:
                pass
    await c.answer()

async def main():
    bot = Bot(TOKEN)
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
