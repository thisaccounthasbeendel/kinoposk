import sys
from watchfiles import watch
import subprocess
import time
import os
import shutil
import signal

# ANSI цвета
YELLOW = '\033[93m'
RESET = '\033[0m'

def clean_pycache():
    """Рекурсивно удаляет все __pycache__ директории в проекте"""
    for root, dirs, files in os.walk('.'):
        if 'venv' in root:  # Пропускаем папку venv и все её подпапки
            continue
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            shutil.rmtree(pycache_path)
            print(f"Removed {pycache_path}")

def run_bot():
    process = subprocess.Popen([sys.executable, "-B", "main.py"])
    return process

def handle_exit(signum, frame):
    print("\nЗавершение работы...")
    if 'process' in globals():
        process.kill()
    sys.exit(0)

if __name__ == "__main__":
    # Регистрируем обработчик для SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, handle_exit)
    
    print(f"\n{YELLOW}Нажмите Ctrl+C для выхода из режима разработки{RESET}\n")
    
    clean_pycache()
    process = run_bot()
    
    for changes in watch(".", watch_filter=lambda x, y: y.endswith('.py'), raise_interrupt=False):
        print("\nDetected changes, restarting bot...")
        process.kill()
        # Даем процессу время на корректное завершение
        time.sleep(1)
        clean_pycache()
        process = run_bot()
