@echo off
echo Запуск Telegram бота...
python main.py --mode bot

echo Запуск админки...
python main.py --mode admin

echo Бот и админка запущены
pause