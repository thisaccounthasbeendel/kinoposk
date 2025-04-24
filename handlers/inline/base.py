from aiogram import Router, F, types

router = Router()

@router.inline_query(F.query.regexp(r'^(?!#).*').as_("query"))  # Ловим все запросы, которые НЕ начинаются с #
async def empty_inline_query(query: types.InlineQuery):
    """Обработчик для обычных инлайн запросов - возвращает пустой результат"""
    await query.answer(
        results=[],
        switch_pm_text="🔍 Поиск доступен только в боте",
        switch_pm_parameter="start"
    )