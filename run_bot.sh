#!/bin/bash

# Запуск Telegram бота
echo "Запуск Telegram бота..."
python main.py --mode bot &
BOT_PID=$!

# Запуск админки
echo "Запуск админки..."
python main.py --mode admin &

echo "Бот и админка запущены"
echo "PID бота: $BOT_PID"

# Ожидание завершения
wait