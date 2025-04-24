import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import shutil
from pathlib import Path

class WeeklyRotatingHandler(RotatingFileHandler):
    """Обработчик с недельной ротацией"""
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None):
        super().__init__(filename, mode, maxBytes, backupCount, encoding=encoding)
        # Сохраняем номер текущей недели и год
        current_date = datetime.now()
        self.current_week = current_date.isocalendar()[1]
        self.current_year = current_date.year
        
    def shouldRollover(self, record):
        """Проверяет, нужно ли создавать новый файл"""
        # Проверяем размер файла
        if super().shouldRollover(record):
            return True
            
        # Проверяем, изменилась ли неделя
        current_date = datetime.now()
        week_number = current_date.isocalendar()[1]
        year = current_date.year
        
        # Ротация нужна если:
        # - Изменился год
        # - Изменился номер недели
        return (year != self.current_year) or (week_number != self.current_week)

    def doRollover(self):
        """Создает новый файл при ротации"""
        if self.stream:
            self.stream.close()
            self.stream = None

        # Формируем имя для бэкапа с номером недели и датой
        backup_dir = Path(self.baseFilename).parent / 'backup'
        current_time = datetime.now()
        week_number = current_time.isocalendar()[1]
        
        # Формат: log_backup_week{номер_недели}_{дата}.txt
        backup_filename = (
            f"log_backup_week{week_number:02d}_"
            f"{current_time.strftime('%d_%m_%Y')}.txt"
        )
        backup_path = backup_dir / backup_filename

        if os.path.exists(self.baseFilename):
            # Копируем текущий лог в бэкап
            shutil.copy2(self.baseFilename, backup_path)
            # Очищаем основной лог
            with open(self.baseFilename, 'w', encoding=self.encoding) as f:
                f.write('')

        # Обновляем текущую неделю и год
        self.current_week = current_time.isocalendar()[1]
        self.current_year = current_time.year

def get_latest_backup_file(backup_dir: Path) -> Path:
    """Получает путь к последнему файлу бэкапа или создает новый"""
    backup_files = list(backup_dir.glob('log_backup_week*.txt'))
    if backup_files:
        return max(backup_files, key=lambda x: x.stat().st_mtime)
    
    # Если файлов нет, создаем новый с текущей датой и номером недели
    current_time = datetime.now()
    week_number = current_time.isocalendar()[1]
    return backup_dir / f"log_backup_week{week_number:02d}_{current_time.strftime('%d_%m_%Y')}.txt"

def append_to_backup(content: str, backup_file: Path):
    """Добавляет контент в конец файла бэкапа"""
    with open(backup_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{content}")

def cleanup_monthly_backups(backup_dir: Path):
    """Очищает старые бэкапы в конце месяца, оставляя логи последней недели"""
    current_time = datetime.now()
    
    # Проверяем, последний ли день месяца
    tomorrow = current_time + timedelta(days=1)
    if current_time.month != tomorrow.month:
        # Находим файлы последней недели
        week_ago = current_time - timedelta(days=7)
        
        for backup_file in backup_dir.glob('log_backup_week*.txt'):
            try:
                # Получаем дату из имени файла (DD_MM_YYYY)
                file_date_str = backup_file.stem.split('_')[-3:]  # Получаем [DD, MM, YYYY]
                file_date = datetime.strptime('_'.join(file_date_str), '%d_%m_%Y')
                
                # Удаляем файлы старше недели
                if file_date.date() < week_ago.date():
                    backup_file.unlink()
            except (IndexError, ValueError):
                continue

def setup_logger():
    # Создаём основную директорию logs и backup
    logs_dir = Path('logs')
    backup_dir = logs_dir / 'backup'
    logs_dir.mkdir(exist_ok=True)
    backup_dir.mkdir(exist_ok=True)

    # Основной лог файл
    log_file_path = logs_dir / 'bot_log.txt'
    
    # Если существует старый лог, переносим его содержимое в бэкап
    if log_file_path.exists():
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        old_content = log_file_path.read_text(encoding='utf-8')
        if old_content.strip():  # Проверяем, что файл не пустой
            latest_backup = get_latest_backup_file(backup_dir)
            separator = "=" * 80
            backup_content = f"\n{separator}\nPrevious session logs (before {current_time}):\n{separator}\n{old_content}"
            append_to_backup(backup_content, latest_backup)
        
        # Очищаем основной лог файл
        log_file_path.write_text('', encoding='utf-8')

    # Настраиваем обработчик логов с недельной ротацией
    rotating_handler = WeeklyRotatingHandler(
        log_file_path, 
        maxBytes=2 * 1024 * 1024,  # 2 MB
        backupCount=5,  # Максимум 5 файлов с логами
        encoding='utf-8'
    )

    # Формат для логов в файл (подробный)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    rotating_handler.setFormatter(file_formatter)

    # Обработчик для вывода логов в консоль (минимальный)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Фильтр для консоли (только сообщения с тегом "CONSOLE")
    class ConsoleFilter(logging.Filter):
        def filter(self, record):
            return hasattr(record, 'console')
    console_handler.addFilter(ConsoleFilter())

    # Настраиваем корневой логгер
    logging.basicConfig(
        level=logging.INFO,
        handlers=[rotating_handler, console_handler],
    )

    # Отключаем избыточное логгирование aiogram
    for logger_name in ['aiogram.event', 'aiogram.middlewares']:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Проверяем необходимость очистки старых бэкапов
    cleanup_monthly_backups(backup_dir)

    # Добавляем разделитель при запуске (только в файл)
    separator = "=" * 80
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"\n{separator}\n"
                f"Bot started at {current_time}\n"
                f"{separator}")
    
    # Сообщение о запуске (в консоль)
    logging.info("Bot is running...", extra={'console': True})

    return logging
