import os
from app import create_app

# Создаем приложение с помощью фабрики
app = create_app()

if __name__ == '__main__':
    # Запускаем приложение
    app.run(debug=True)