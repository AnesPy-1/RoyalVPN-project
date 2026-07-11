import os
import tempfile
from html import escape

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .client import BotAPIError, RoyalVPNBotClient
from .config import BOT_ADMIN_TELEGRAM_IDS
from botapi.models import BotSession
from botapi.security import validate_session_token


router = Router()
client = RoyalVPNBotClient()
user_sessions: dict[int, str] = {}
user_profiles: dict[int, dict] = {}
pending_requests: dict[int, int] = {}


class LoginFlow(StatesGroup):
    waiting_username = State()
    waiting_password = State()


class TopUpFlow(StatesGroup):
    waiting_amount = State()
    waiting_receipt = State()


class AdminRejectFlow(StatesGroup):
    waiting_reason = State()


def _main_keyboard(is_logged_in: bool, is_admin: bool) -> InlineKeyboardMarkup:
    rows = []
    if is_logged_in:
        rows.append([InlineKeyboardButton(text="حساب من", callback_data="menu:profile")])
        rows.append([InlineKeyboardButton(text="شارژ کیف پول", callback_data="menu:topup")])
        rows.append([InlineKeyboardButton(text="خروج از حساب", callback_data="menu:logout")])
    else:
        rows.append([InlineKeyboardButton(text="ورود به حساب", callback_data="menu:login")])
    if is_admin:
        rows.append([InlineKeyboardButton(text="پنل مدیریت", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _back_keyboard(callback_data: str = "menu:home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت", callback_data=callback_data)]]
    )


def _payment_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ارسال رسید", callback_data=f"payment:receipt:{payment_id}")],
            [InlineKeyboardButton(text="بازگشت به منو", callback_data="menu:home")],
        ]
    )


def _admin_payment_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تأیید", callback_data=f"admin:approve:{payment_id}"),
                InlineKeyboardButton(text="❌ رد", callback_data=f"admin:reject:{payment_id}"),
            ]
        ]
    )


def _is_admin(telegram_user_id: int) -> bool:
    return str(telegram_user_id) in BOT_ADMIN_TELEGRAM_IDS


def _error_message(code: str | None) -> str:
    mapping = {
        "invalid_credentials": "نام کاربری یا رمز عبور اشتباه است.",
        "validation_error": "لطفا اطلاعات را به شکل درست وارد کنید.",
        "site_settings_missing": "فعلا امکان انجام این عملیات وجود ندارد. لطفا بعدا دوباره تلاش کنید.",
        "session_invalid": "جلسه شما منقضی شده است. لطفا دوباره وارد شوید.",
        "already_approved": "این رسید قبلا تایید شده است.",
        "already_rejected": "این رسید قبلا رد شده است.",
        "not_found": "اطلاعات مورد نظر پیدا نشد.",
        "bot_api_not_configured": "اتصال ربات هنوز تنظیم نشده است.",
    }
    if code in mapping:
        return mapping[code]
    return "عملیات با خطا مواجه شد. لطفا دوباره تلاش کنید."


async def _track_message(state: FSMContext, message_id: int):
    data = await state.get_data()
    bot_message_ids = list(data.get("bot_message_ids", []))
    bot_message_ids.append(message_id)
    await state.update_data(bot_message_ids=bot_message_ids)


async def _clear_tracked_messages(bot, chat_id: int, state: FSMContext, keep_ids: set[int] | None = None):
    data = await state.get_data()
    bot_message_ids = list(data.get("bot_message_ids", []))
    keep_ids = keep_ids or set()
    remaining = []
    for message_id in reversed(bot_message_ids):
        if message_id in keep_ids:
            remaining.append(message_id)
            continue
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception:
            remaining.append(message_id)
    await state.update_data(bot_message_ids=list(reversed(remaining)))


async def _send_tracked(message: Message, state: FSMContext, text: str, **kwargs):
    sent = await message.answer(text, **kwargs)
    await _track_message(state, sent.message_id)
    return sent


async def _send_tracked_callback(callback: CallbackQuery, state: FSMContext, text: str, **kwargs):
    sent = await callback.message.answer(text, **kwargs)
    await _track_message(state, sent.message_id)
    return sent


async def _safe_delete_user_message(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


def _profile_cache_for(telegram_user_id: int) -> dict:
    return user_profiles.get(telegram_user_id, {})


def _format_toman(amount: int | str | None) -> str:
    try:
        value = int(amount or 0)
    except (TypeError, ValueError):
        return str(amount or "0")
    return f"{value:,}"


def _get_active_session_token(telegram_user_id: int) -> str | None:
    session_token = user_sessions.get(telegram_user_id)
    if not session_token:
        return None
    ok, _, session = validate_session_token(session_token)
    if not ok:
        user_sessions.pop(telegram_user_id, None)
        user_profiles.pop(telegram_user_id, None)
        return None
    return session_token


async def _update_profile_cache(telegram_user_id: int, session_token: str):
    try:
        response = client.profile(session_token)
    except BotAPIError:
        return {}
    user_profiles[telegram_user_id] = response["user"]
    return response["user"]


async def _notify_admins_about_receipt(bot, *, payment: dict, profile: dict, receipt_text: str, receipt_image_path: str | None):
    caption = (
        "💳 درخواست پرداخت جدید\n\n"
        f"کاربر: {escape(profile.get('username', '---'))}\n"
        f"شناسه پرداخت: {escape(payment['reference_id'])}\n"
        f"شناسه داخلی: {payment['id']}\n"
        f"مبلغ درخواستی: {payment.get('requested_amount', 0)} تومان\n"
        f"هدیه شارژ: {payment.get('bonus_amount', 0)} تومان\n"
        f"مبلغ قابل پرداخت: {payment.get('payable_amount', 0)} تومان\n"
        f"زمان: {escape(payment.get('created_at', ''))}\n\n"
        f"رسید: {escape(receipt_text or '---')}"
    )
    keyboard = _admin_payment_keyboard(payment["id"])
    for admin_id in BOT_ADMIN_TELEGRAM_IDS:
        try:
            if receipt_image_path:
                await bot.send_photo(
                    chat_id=int(admin_id),
                    photo=FSInputFile(receipt_image_path),
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
            else:
                await bot.send_message(
                    chat_id=int(admin_id),
                    text=caption,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
        except Exception:
            continue


async def _finalize_user_flow(bot, state: FSMContext, chat_id: int, message_text: str, reply_markup=None):
    await _clear_tracked_messages(bot, chat_id, state)
    await state.clear()
    final_message = await bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)
    return final_message


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    telegram_user_id = message.from_user.id
    session_token = _get_active_session_token(telegram_user_id)
    if session_token:
        await _update_profile_cache(telegram_user_id, session_token)
    await message.answer(
        "به ربات RoyalVPN خوش آمدید.",
        reply_markup=_main_keyboard(bool(session_token), _is_admin(telegram_user_id)),
    )


@router.callback_query(F.data == "menu:home")
async def home_callback(callback: CallbackQuery, state: FSMContext):
    await _clear_tracked_messages(callback.bot, callback.message.chat.id, state)
    await state.clear()
    telegram_user_id = callback.from_user.id
    session_token = _get_active_session_token(telegram_user_id)
    try:
        await callback.message.edit_text(
            "به ربات RoyalVPN خوش آمدید.",
            reply_markup=_main_keyboard(bool(session_token), _is_admin(telegram_user_id)),
        )
    except Exception:
        await callback.message.answer(
            "به ربات RoyalVPN خوش آمدید.",
            reply_markup=_main_keyboard(telegram_user_id in user_sessions, _is_admin(telegram_user_id)),
        )
    await callback.answer()


@router.callback_query(F.data == "menu:login")
async def login_callback(callback: CallbackQuery, state: FSMContext):
    await _clear_tracked_messages(callback.bot, callback.message.chat.id, state)
    await state.clear()
    await state.set_state(LoginFlow.waiting_username)
    await state.update_data(bot_message_ids=[])
    sent = await callback.message.answer("لطفا نام کاربری خود را وارد کنید:")
    await _track_message(state, sent.message_id)
    await callback.answer()


@router.message(StateFilter(LoginFlow.waiting_username))
async def login_username(message: Message, state: FSMContext):
    username = (message.text or "").strip()
    if not username:
        await _safe_delete_user_message(message)
        await _send_tracked(message, state, "نام کاربری معتبر وارد کنید.")
        return
    await state.update_data(username=username)
    await _safe_delete_user_message(message)
    await _send_tracked(message, state, "لطفا رمز عبور خود را وارد کنید:")
    await state.set_state(LoginFlow.waiting_password)


@router.message(StateFilter(LoginFlow.waiting_password))
async def login_password(message: Message, state: FSMContext):
    data = await state.get_data()
    username = data.get("username", "")
    password = (message.text or "").strip()
    await _safe_delete_user_message(message)

    try:
        response = client.login(username, password, str(message.from_user.id))
    except BotAPIError as exc:
        await _finalize_user_flow(
            message.bot,
            state,
            message.chat.id,
            _error_message(exc.code),
            reply_markup=_back_keyboard("menu:login"),
        )
        return

    user_sessions[message.from_user.id] = response["session_token"]
    user_profiles[message.from_user.id] = response["user"]
    await _finalize_user_flow(
        message.bot,
        state,
        message.chat.id,
        f"✅ ورود موفقیت‌آمیز بود.\n\nبه حساب کاربری خود وارد شدید.\nموجودی: {response['user']['wallet_balance']} تومان",
        reply_markup=_main_keyboard(True, _is_admin(message.from_user.id)),
    )


@router.callback_query(F.data == "menu:logout")
async def logout_callback(callback: CallbackQuery, state: FSMContext):
    session_token = user_sessions.pop(callback.from_user.id, None)
    if session_token:
        BotSession.objects.filter(token_hash=BotSession.hash_token(session_token)).update(is_active=False)
    pending_requests.pop(callback.from_user.id, None)
    user_profiles.pop(callback.from_user.id, None)
    await _clear_tracked_messages(callback.bot, callback.message.chat.id, state)
    await state.clear()
    await callback.message.answer(
        "از حساب خارج شدید.",
        reply_markup=_main_keyboard(False, _is_admin(callback.from_user.id)),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def profile_callback(callback: CallbackQuery):
    session_token = _get_active_session_token(callback.from_user.id)
    if not session_token:
        await callback.answer("ابتدا وارد شوید.", show_alert=True)
        return
    try:
        response = client.profile(session_token)
    except BotAPIError:
        await callback.answer("فعلا امکان دریافت اطلاعات حساب وجود ندارد.", show_alert=True)
        return
    user_profiles[callback.from_user.id] = response["user"]
    user = response["user"]
    text = (
        f"👤 اطلاعات حساب\n\n"
        f"Username: {user['username']}\n"
        f"تاریخ عضویت: {user['date_joined'][:10]}\n\n"
        f"💰 موجودی: {user['wallet_balance']} تومان\n"
        f"💳 مجموع پرداخت‌ها: {user['total_top_up']} تومان\n"
        f"📦 تعداد تراکنش: {user['total_transactions']}"
    )
    await callback.message.answer(text, reply_markup=_main_keyboard(True, _is_admin(callback.from_user.id)))
    await callback.answer()


@router.callback_query(F.data == "menu:topup")
async def topup_callback(callback: CallbackQuery, state: FSMContext):
    session_token = _get_active_session_token(callback.from_user.id)
    if not session_token:
        await callback.answer("ابتدا وارد شوید.", show_alert=True)
        return
    await _clear_tracked_messages(callback.bot, callback.message.chat.id, state)
    await state.clear()
    await state.set_state(TopUpFlow.waiting_amount)
    await state.update_data(bot_message_ids=[])
    sent = await callback.message.answer("مبلغ مورد نظر را به تومان وارد کنید:")
    await _track_message(state, sent.message_id)
    await callback.answer()


@router.message(StateFilter(TopUpFlow.waiting_amount))
async def topup_amount(message: Message, state: FSMContext):
    session_token = _get_active_session_token(message.from_user.id)
    if not session_token:
        await _safe_delete_user_message(message)
        await _finalize_user_flow(
            message.bot,
            state,
            message.chat.id,
            "ابتدا وارد حساب خود شوید.",
            reply_markup=_back_keyboard("menu:home"),
        )
        return
    try:
        amount = int((message.text or "").strip())
    except ValueError:
        await _safe_delete_user_message(message)
        await message.answer("مبلغ را فقط به صورت عدد وارد کنید.")
        return
    if amount < 1:
        await _safe_delete_user_message(message)
        await message.answer("مبلغ باید بیشتر از صفر باشد.")
        return

    await _safe_delete_user_message(message)
    try:
        response = client.create_payment_request(session_token, amount)
    except BotAPIError as exc:
        await _finalize_user_flow(
            message.bot,
            state,
            message.chat.id,
            _error_message(exc.code),
            reply_markup=_back_keyboard("menu:topup"),
        )
        return

    payment = response["request"]
    pending_requests[message.from_user.id] = payment["id"]
    await state.set_state(TopUpFlow.waiting_receipt)
    await state.update_data(bot_message_ids=[])

    sent = await message.answer(
        "پرداخت ایجاد شد.\n\n"
        f"مبلغ قابل پرداخت: {payment['payable_amount']} تومان\n"
        f"شماره کارت: <code>{payment['payment_card_number']}</code>\n\n"
        "بعد از پرداخت، روی دکمه ارسال رسید بزنید و رسید را ارسال کنید.",
        parse_mode=ParseMode.HTML,
        reply_markup=_payment_keyboard(payment["id"]),
    )
    await _track_message(state, sent.message_id)


@router.callback_query(F.data.startswith("payment:receipt:"))
async def receipt_begin(callback: CallbackQuery, state: FSMContext):
    session_token = _get_active_session_token(callback.from_user.id)
    if not session_token:
        await callback.answer("ابتدا وارد شوید.", show_alert=True)
        return
    request_id = int(callback.data.split(":")[-1])
    pending_requests[callback.from_user.id] = request_id
    await state.set_state(TopUpFlow.waiting_receipt)
    await state.update_data(bot_message_ids=[])
    sent = await callback.message.answer(
        "رسید پرداخت را به صورت عکس یا متن ارسال کنید.\n"
        "اگر لینک یا شناسه تراکنش هم دارید، در همان پیام بنویسید.",
        reply_markup=_back_keyboard("menu:home"),
    )
    await _track_message(state, sent.message_id)
    await callback.answer()


@router.message(StateFilter(TopUpFlow.waiting_receipt))
async def receipt_submit(message: Message, state: FSMContext):
    session_token = _get_active_session_token(message.from_user.id)
    request_id = pending_requests.get(message.from_user.id)
    if not session_token or not request_id:
        await _safe_delete_user_message(message)
        await _finalize_user_flow(
            message.bot,
            state,
            message.chat.id,
            "درخواست پرداخت پیدا نشد. لطفا دوباره از بخش شارژ کیف پول شروع کنید.",
            reply_markup=_back_keyboard("menu:topup"),
        )
        return

    receipt_text = message.caption or message.text or ""
    transaction_id = ""
    receipt_link = ""
    receipt_image_path = None
    if message.photo:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_file.close()
        await message.bot.download(message.photo[-1], destination=temp_file.name)
        receipt_image_path = temp_file.name

    try:
        response = client.submit_receipt(
            session_token,
            request_id,
            receipt_text=receipt_text,
            receipt_link=receipt_link,
            transaction_id=transaction_id,
            receipt_image_path=receipt_image_path,
        )
    except BotAPIError as exc:
        if receipt_image_path:
            try:
                os.remove(receipt_image_path)
            except OSError:
                pass
        await _safe_delete_user_message(message)
        await _finalize_user_flow(
            message.bot,
            state,
            message.chat.id,
            _error_message(exc.code),
            reply_markup=_back_keyboard("menu:home"),
        )
        return

    profile = _profile_cache_for(message.from_user.id)
    if not profile:
        profile = await _update_profile_cache(message.from_user.id, session_token)
    await _notify_admins_about_receipt(
        message.bot,
        payment=response["request"],
        profile=profile or {"username": message.from_user.username or message.from_user.full_name or str(message.from_user.id)},
        receipt_text=receipt_text,
        receipt_image_path=receipt_image_path,
    )

    if receipt_image_path:
        try:
            os.remove(receipt_image_path)
        except OSError:
            pass

    await _safe_delete_user_message(message)
    pending_requests.pop(message.from_user.id, None)
    await _finalize_user_flow(
        message.bot,
        state,
        message.chat.id,
        "✅ رسید شما ثبت شد. پس از بررسی، موجودی شما به‌صورت خودکار بروزرسانی می‌شود.",
        reply_markup=_back_keyboard("menu:home"),
    )


@router.callback_query(F.data == "menu:admin")
async def admin_menu(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    await callback.message.answer(
        "پنل مدیریت",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="آمار سایت", callback_data="admin:stats")],
                [InlineKeyboardButton(text="پرداخت‌های در انتظار", callback_data="admin:pending")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    try:
        response = client.admin_statistics()
    except BotAPIError:
        await callback.answer("فعلا امکان دریافت آمار وجود ندارد.", show_alert=True)
        return
    users = response["users"]
    payments = response["payments"]
    await callback.message.answer(
        "آمار سایت\n\n"
        f"کل کاربران: {users['total']}\n"
        f"کاربران دارای خرید: {users['with_purchases']}\n\n"
        f"کل درخواست‌ها: {payments['total_requests']}\n"
        f"در انتظار: {payments['pending']}\n"
        f"تایید شده: {payments['approved']}\n"
        f"رد شده: {payments['rejected']}\n"
        f"جمع مبلغ: {payments['total_amount']} تومان"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:pending")
async def admin_pending(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    try:
        response = client.admin_pending_payments()
    except BotAPIError:
        await callback.answer("فعلا امکان دریافت لیست وجود ندارد.", show_alert=True)
        return
    requests = response["requests"]
    if not requests:
        await callback.message.answer("درخواست در انتظاری وجود ندارد.")
        await callback.answer()
        return
    for item in requests[:10]:
        await callback.message.answer(
            "درخواست پرداخت جدید\n\n"
            f"کاربر: {item['username']}\n"
            f"مبلغ: {item['payable_amount']} تومان\n"
            f"شناسه پرداخت: {item['reference_id']}\n"
            f"زمان: {item['created_at']}\n\n"
            f"رسید: {item['receipt_text'] or '---'}\n"
            f"لینک: {item['receipt_link'] or '---'}\n"
            f"شناسه تراکنش: {item['transaction_id'] or '---'}",
            reply_markup=_admin_payment_keyboard(item["id"]),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:approve:"))
async def admin_approve(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    payment_id = int(callback.data.split(":")[-1])
    try:
        response = client.approve_payment(payment_id)
    except BotAPIError as exc:
        await callback.answer(_error_message(exc.code), show_alert=True)
        return

    payment = response["payment"]
    target_user_id = payment["user_id"]
    if target_user_id in user_profiles:
        user_profiles[target_user_id]["wallet_balance"] = payment["new_balance"]
    try:
        await callback.bot.send_message(
            chat_id=target_user_id,
            text=(
                "✅ رسید شما تایید شد.\n\n"
                f"شماره پرداخت: {payment['reference_id']}\n"
                f"مبلغ {_format_toman(payment['amount'])} تومان به موجودی شما اضافه شد.\n"
                f"موجودی جدید: {_format_toman(payment['new_balance'])} تومان"
            ),
            reply_markup=_back_keyboard("menu:home"),
        )
    except Exception:
        pass
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=(
                    "✅ رسید تایید شد.\n"
                    f"کاربر: {payment['username']}\n"
                    f"مبلغ: {_format_toman(payment['amount'])} تومان"
                ),
                reply_markup=None,
            )
        else:
            await callback.message.edit_text(
                text=(
                    "✅ رسید تایید شد.\n"
                    f"کاربر: {payment['username']}\n"
                    f"مبلغ: {_format_toman(payment['amount'])} تومان"
                ),
                reply_markup=None,
            )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("admin:reject:"))
async def admin_reject(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    payment_id = int(callback.data.split(":")[-1])
    await _clear_tracked_messages(callback.bot, callback.message.chat.id, state)
    await state.clear()
    await state.set_state(AdminRejectFlow.waiting_reason)
    await state.update_data(
        payment_id=payment_id,
        source_message_id=callback.message.message_id,
        source_is_photo=bool(callback.message.photo),
        bot_message_ids=[],
    )
    sent = await callback.message.answer(
        "دلیل رد را ارسال کنید. اگر دلیل خاصی ندارید، فقط یک خط تیره `-` بفرستید.",
        parse_mode=ParseMode.HTML,
    )
    await _track_message(state, sent.message_id)
    await callback.answer()


@router.message(StateFilter(AdminRejectFlow.waiting_reason))
async def admin_reject_reason(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await state.clear()
        return
    data = await state.get_data()
    payment_id = data.get("payment_id")
    reason = (message.text or "").strip()
    await _safe_delete_user_message(message)
    if not payment_id:
        await _finalize_user_flow(
            message.bot,
            state,
            message.chat.id,
            "پرداخت مورد نظر پیدا نشد.",
            reply_markup=_back_keyboard("menu:home"),
        )
        return
    note = "" if reason in {"", "-"} else reason
    try:
        response = client.reject_payment(payment_id, note=note or "رد شد توسط ادمین تلگرام")
    except BotAPIError as exc:
        await _finalize_user_flow(
            message.bot,
            state,
            message.chat.id,
            _error_message(exc.code),
            reply_markup=_back_keyboard("menu:home"),
        )
        return
    payment = response["payment"]
    try:
        await message.bot.send_message(
            chat_id=payment["user_id"],
            text=(
                "❌ رسید شما رد شد.\n\n"
                f"شماره پرداخت: {payment['reference_id']}\n"
                "در صورت نیاز با پشتیبانی تماس بگیرید."
            ),
            reply_markup=_back_keyboard("menu:home"),
        )
    except Exception:
        pass
    source_message_id = data.get("source_message_id")
    source_is_photo = bool(data.get("source_is_photo"))
    if message.chat and message.chat.id:
        await _clear_tracked_messages(message.bot, message.chat.id, state)
    await state.clear()
    try:
        if source_message_id and source_is_photo:
            await message.bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=source_message_id,
                caption=(
                    "❌ رسید رد شد.\n"
                    f"کاربر: {payment['username']}\n"
                    f"شناسه پرداخت: {payment['reference_id']}"
                ),
                reply_markup=None,
            )
        elif source_message_id:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=source_message_id,
                text=(
                    "❌ رسید رد شد.\n"
                    f"کاربر: {payment['username']}\n"
                    f"شناسه پرداخت: {payment['reference_id']}"
                ),
                reply_markup=None,
            )
    except Exception:
        pass
    await message.answer("پرداخت با موفقیت رد شد.")
