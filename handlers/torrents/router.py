from aiogram import Router
from .basic import register_torrent_handlers

torrent_router = Router(name="torrents")

def setup_torrent_router() -> Router:
    register_torrent_handlers(torrent_router)
    return torrent_router