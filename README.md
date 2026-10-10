# Бот «Тест эмоционального интеллекта (ЭмИн)»

## Запуск на Mac
1. В Telegram откройте @BotFather → /newbot → получите токен.
2. В терминале:
```
cd emin_bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN="ваш_токен"
python bot.py
```
3. Напишите боту /start.

Пока бот запущен на Mac, он работает. Для работы 24/7 его нужно перенести на VPS.

## Файлы
- emin.py — утверждения, ключ, нормы, подсчёт (не менять).
- texts.py — приветствие, описания шкал, финальный текст (редактируйте).
- results.db — анонимная база результатов (создаётся сама).
