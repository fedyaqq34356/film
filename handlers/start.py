from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.inline import get_main_menu
from utils.formatters import format_help_message
from config import MESSAGES

router = Router()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Обработчик команды /start."""
    await state.clear()  # Очищаем состояние
    
    await message.answer(
        MESSAGES['start'],
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    
    await callback.message.edit_text(
        MESSAGES['start'],
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Показать справку."""
    await callback.message.edit_text(
        format_help_message(),
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("help"))
async def help_command(message: Message):
    """Команда помощи."""
    await message.answer(
        format_help_message(),
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )