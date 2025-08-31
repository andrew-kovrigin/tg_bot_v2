import hashlib
import sys

def generate_password_hash(password):
    """Создает SHA512 хэш от пароля"""
    return hashlib.sha512(password.encode('utf-8')).hexdigest()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python generate_password_hash.py <ваш_пароль>")
        sys.exit(1)
    
    password = sys.argv[1]
    hash_value = generate_password_hash(password)
    print(f"Хэш SHA512 для пароля '{password}':")
    print(hash_value)