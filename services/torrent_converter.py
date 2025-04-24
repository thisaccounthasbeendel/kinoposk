import libtorrent as lt
import time
import logging
from pathlib import Path
import tempfile
import os
import asyncio
from typing import Optional, Tuple
import re

class TorrentConverter:
    def __init__(self):
        self.temp_dir = Path("temp/torrents")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def _sanitize_filename(self, filename: str) -> str:
        """Очищает имя файла от недопустимых символов"""
        # Заменяем недопустимые символы на underscore
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Ограничиваем длину имени файла
        return filename[:200] if len(filename) > 200 else filename

    async def convert_magnet(self, magnet_uri: str) -> Optional[Tuple[str, Path]]:
        """
        Конвертирует магнет-ссылку в торрент файл
        
        Args:
            magnet_uri: Магнет-ссылка
            
        Returns:
            Tuple[str, Path]: (название торрента, путь к файлу) или None при ошибке
        """
        temp_download_dir = None
        
        try:
            # Создаем временную директорию для загрузки метаданных
            temp_download_dir = tempfile.mkdtemp()
            
            # Создаем сессию
            sess = lt.session()
            
            # Настраиваем параметры
            params = lt.parse_magnet_uri(magnet_uri)
            params.save_path = temp_download_dir
            
            # Добавляем торрент
            handle = sess.add_torrent(params)
            
            logging.info("[TORRENT CONVERTER] Fetching metadata...")
            
            # Ждем получения метаданных
            timeout = 30  # таймаут в секундах
            start_time = time.time()
            
            while (not handle.status().has_metadata):
                await asyncio.sleep(0.1)
                if time.time() - start_time > timeout:
                    raise Exception("[TORRENT CONVERTER] Timeout waiting for metadata")
            
            logging.info("[TORRENT CONVERTER] Got metadata, saving torrent file...")
            
            # Получаем информацию о торренте
            torrent_info = handle.status().torrent_file
            
            # Получаем название торрента из метаданных
            torrent_name = torrent_info.name()
            safe_name = self._sanitize_filename(torrent_name)
            
            # Создаем уникальное имя файла
            timestamp = int(time.time())
            output_path = self.temp_dir / f"{safe_name}_{timestamp}.torrent"
            
            # Создаем torrent файл
            torrent_file = lt.create_torrent(torrent_info)
            
            # Сохраняем файл
            with open(output_path, 'wb') as f:
                f.write(lt.bencode(torrent_file.generate()))
            
            # Очищаем сессию
            sess.remove_torrent(handle)
            
            logging.info(f"[TORRENT CONVERTER] Torrent saved to: {output_path}")
            return torrent_name, output_path
            
        except Exception as e:
            logging.error(f"Error converting magnet to torrent: {e}")
            return None
            
        finally:
            # Очищаем временную директорию для загрузки
            if temp_download_dir:
                try:
                    for root, dirs, files in os.walk(temp_download_dir, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(temp_download_dir)
                except Exception as e:
                    logging.warning(f"[TORRENT CONVERTER] [TORRENT CONVERTER] Failed to cleanup temp directory: {e}")

    def cleanup_file(self, file_path: Path) -> None:
        """Удаляет торрент файл после отправки"""
        try:
            if file_path.exists():
                file_path.unlink()
                logging.info(f"[TORRENT CONVERTER] Deleted torrent file: {file_path}")
        except Exception as e:
            logging.error(f"Error deleting torrent file: {e}")

# Создаем глобальный экземпляр конвертера
torrent_converter = TorrentConverter()