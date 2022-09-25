import re
from aiogram import Bot, Dispatcher, dispatcher, executor, types
import datetime
import pandas as pd
from aiogram.dispatcher.filters import Text
import asyncio
import numpy as np
import lib  # Библиотека вспомогательных функций
from system.dbc import getSQLSettings  # Настройки SQL
from itertools import groupby

global log_group
log_group = '$$$$$$$'  # группа, куда бот отсылает часть логов
print('WOrked')
u_f = lib.Query.getRecordsByQuery('fli', f'id != 0')  # забирает все увлечения
global u_fl
u_fl = pd.DataFrame(u_f)
c_f = lib.Query.getRecordsByQuery('c', f'id != 0')  # забирает все настройки
global c
c = pd.DataFrame(c_f)

bot = Bot(f"{str(c.at[1, 'chat_id'])}")  # если 2, то тестовый
dp = Dispatcher(bot)

contact_f = lib.Query.getRecordsByQuery('bdci', f'id != 0')  # забирает все цели контактов
global contact_b
contact_b = pd.DataFrame(contact_f)

deal_f = lib.Query.getRecordsByQuery('bdi', f'id != 0')  # забирает все чем занимается человек
global deal_b
deal_b = pd.DataFrame(deal_f)

sector_f = lib.Query.getRecordsByQuery('bsi', f'id != 0')  # забирает все из какого сектора
global sector_b
sector_b = pd.DataFrame(sector_f)


# Генерация клавиатуры группы пользователей
def get_keyboard_u_group(id):
    buttons = [
        types.InlineKeyboardButton(text="Отправить всем", callback_data=f"num_sendEveryone_*{str(id)}"),
        types.InlineKeyboardButton(text="По дружбе", callback_data=f"num_sendFriends_*{str(id)}"),
        types.InlineKeyboardButton(text="По бизнесу", callback_data=f"num_sendBusiness_*{str(id)}")
    ]
    keyboard_u_group = types.InlineKeyboardMarkup()
    keyboard_u_group.add(*buttons)
    return keyboard_u_group


# Генерация клавиатуры выбор пола
def get_keyboard_gender(id):
    buttons = [
        types.InlineKeyboardButton(text="Я - мужчина 👦", callback_data=f"num_gender_{str(id)}_1"),
        types.InlineKeyboardButton(text="Я - женщина 👧", callback_data=f"num_gender_{str(id)}_0")
    ]
    keyboard_ban = types.InlineKeyboardMarkup()
    keyboard_ban.add(*buttons)
    return keyboard_ban


# Генерация клавиатуры выбор города
def get_keyboard_sity(id, step):
    buttons = [
        # перечисление городов
    ]
    keyboard_ban = types.InlineKeyboardMarkup()
    keyboard_ban.add(*buttons)
    return keyboard_ban


# Генерация клавиатуры язык
def get_keyboard_lang(id, step):
    t = lib.Query.getRecordsByQuery('u_lang_id', f'ei = {id}')
    te = lib.Query.getRecordsByQuery('u_lang', f'id != 10')
    keyboard_lang = types.InlineKeyboardMarkup(row_width=2)
    row_btns = []
    for el in te:
        er = 0
        for x in t:
            if x['lang_id'] == el['id']:
                er = 1
        if er == 1:
            row_btns.append(
                types.InlineKeyboardButton(text=f"✅{el['name']}", callback_data=f"num_lang_{id}_{el['id']}_1_{step}"))
        else:
            row_btns.append(
                types.InlineKeyboardButton(text=f"{el['name']}", callback_data=f"num_lang_{id}_{el['id']}_0_{step}"))
    keyboard_lang.add(*row_btns)
    return keyboard_lang


# Генерация клавиатуры для выбора года рождения пользователя
def get_keyboard_year(id, step):
    markup = types.InlineKeyboardMarkup(row_width=5)
    te = [i for i in range(1960, 2010)]
    row_btns = [types.InlineKeyboardButton(text=f'{i}', callback_data=f'num_gen-year_{id}_{i}_{step}') for i in te]
    markup.add(*row_btns)
    return markup


# Генерация клавиатуры для выбора месяца рождения пользователя
def get_keyboard_mounth(id, year, step):
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton(text="Январь", callback_data=f"num_gen-mounth_{id}_{year}_1_{step}")
        , types.InlineKeyboardButton(text="Февраль", callback_data=f"num_gen-mounth_{id}_{year}_2_{step}")
        , types.InlineKeyboardButton(text="Март", callback_data=f"num_gen-mounth_{id}_{year}_3_{step}")
        , types.InlineKeyboardButton(text="Апрель", callback_data=f"num_gen-mounth_{id}_{year}_4_{step}")
        , types.InlineKeyboardButton(text="Май", callback_data=f"num_gen-mounth_{id}_{year}_5_{step}")
        , types.InlineKeyboardButton(text="Июнь", callback_data=f"num_gen-mounth_{id}_{year}_6_{step}")
        , types.InlineKeyboardButton(text="Июль", callback_data=f"num_gen-mounth_{id}_{year}_7_{step}")
        , types.InlineKeyboardButton(text="Август", callback_data=f"num_gen-mounth_{id}_{year}_8_{step}")
        , types.InlineKeyboardButton(text="Сентябрь", callback_data=f"num_gen-mounth_{id}_{year}_9_{step}")
        , types.InlineKeyboardButton(text="Октябрь", callback_data=f"num_gen-mounth_{id}_{year}_10_{step}")
        , types.InlineKeyboardButton(text="Ноябрь", callback_data=f"num_gen-mounth_{id}_{year}_11_{step}")
        , types.InlineKeyboardButton(text="Декабрь", callback_data=f"num_gen-mounth_{id}_{year}_12_{step}")
    ]
    markup.add(*buttons)
    return markup


# Генерация клавиатуры для выбора дня рождения пользователя
def get_keyboard_day(id, year, mounth, step):
    markup = types.InlineKeyboardMarkup(row_width=5)
    te = [i for i in range(1, 32)]
    row_btns = [types.InlineKeyboardButton(text=f'{i}', callback_data=f'num_gen-day_{id}_{year}_{mounth}_{i}_{step}')
                for i in te]
    markup.add(*row_btns)
    return markup


# Генерация клавиатуры выбор цели знакомства
def get_keyboard_choose(id):
    # keyboard_choose = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(text="Найти друзей 🚴‍♂️", callback_data=f"num_choose_{str(id)}_0"),
        types.InlineKeyboardButton(text="Расширить сеть деловых контактов 💶", callback_data=f"num_choose_{str(id)}_1")
    ]
    keyboard_choose = types.InlineKeyboardMarkup(row_width=1)
    keyboard_choose.add(*buttons)
    return keyboard_choose


# Генерация клавиатуры друзья-досуг
def get_keyboard_friends_leisure(id, act, step):
    if act == 'fl':
        t = lib.Query.getRecordsByQuery('flu', f'ei = {id}')
        tempo = 'fli'
    elif act == 'bl':
        t = lib.Query.getRecordsByQuery('blu', f'ei = {id}')
        tempo = 'leisure_id'
    te = lib.Query.getRecordsByQuery('fli', f'id != 0')
    keyboard_friends_leisure = types.InlineKeyboardMarkup(row_width=2)
    row_btns = []
    for el in te:
        er = 0
        for x in t:
            if x[f'{tempo}'] == el['id']:
                er = 1
        if er == 1:
            row_btns.append(
                types.InlineKeyboardButton(text=f"✅{el['name']}", callback_data=f"num_{act}_{id}_{el['id']}_1_{step}"))
        else:
            row_btns.append(
                types.InlineKeyboardButton(text=f"{el['name']}", callback_data=f"num_{act}_{id}_{el['id']}_0_{step}"))
    keyboard_friends_leisure.add(*row_btns)
    return keyboard_friends_leisure


# Генерация клавиатуры друзья-досуг-доп
def get_keyboard_friends_leisure_plus(id, step):
    t = lib.Query.getRecordsByQuery('flu', f'ei = {id}')
    ta = lib.Query.getRecordsByQuery('flu_plus', f'ei = {id}')
    te = lib.Query.getRecordsByQuery('fli', f'id != 0')
    keyboard_friends_leisure = types.InlineKeyboardMarkup(row_width=2)
    row_btns = []
    for el in te:
        er = 0
        tem = 0
        for e in t:
            if tem != 1:
                if e['fli'] != el['id']:
                    for x in ta:
                        if el['id'] == x['fli']:
                            er = 1
                else:
                    tem = 1
                    break
        if tem != 1:
            if er == 1:
                row_btns.append(types.InlineKeyboardButton(text=f"✅{el['name']}",
                                                           callback_data=f"num_flp_{id}_{el['id']}_1_{step}"))
            else:
                row_btns.append(
                    types.InlineKeyboardButton(text=f"{el['name']}", callback_data=f"num_flp_{id}_{el['id']}_0_{step}"))
    keyboard_friends_leisure.add(*row_btns)
    return keyboard_friends_leisure


# Генерация клавиатуры чем сейчас занимаешься
def get_keyboard_business(id, step):
    te = lib.Query.getRecordsByQuery('bdi', f'id != 0')
    keyboard_business = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    for el in te:
        buttons.append(types.InlineKeyboardButton(text=f"{el['name']}", callback_data=f"num_de_{id}_{el['id']}_{step}"))
    keyboard_business.add(*buttons)
    return keyboard_business


# Генерация клавиатуры в какой сфере
def get_keyboard_business_sector(id, act, step):
    if act == 'sect':
        t = lib.Query.getRecordsByQuery('bsu', f'ei = {id}')
        tempo = int(lib.Query.checkCountByQuery('bsu', f'ei = {id}'))
    elif act == 'sect2':
        t = lib.Query.getRecordsByQuery('bs2u', f'ei = {id}')
        tempo = int(lib.Query.checkCountByQuery('bs2u', f'ei = {id}'))
    te = lib.Query.getRecordsByQuery('bsi', f'id != 0')
    keyboard_sector = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for el in te:
        er = 0
        for x in t:
            if x[f'id_sector'] == el['id']:
                er = 1
        if er == 1:
            buttons.append(
                types.InlineKeyboardButton(text=f"✅{el['name']}", callback_data=f"num_{act}_{id}_{el['id']}_1_{step}"))
        else:
            buttons.append(
                types.InlineKeyboardButton(text=f"{el['name']}", callback_data=f"num_{act}_{id}_{el['id']}_0_{step}"))
    if tempo > 0:
        buttons.append(types.InlineKeyboardButton(text=f"Готово", callback_data=f"num_{act}_{id}_0_all_{step}"))
    keyboard_sector.add(*buttons)
    return keyboard_sector


# Генерация клавиатуры какие контакты
def get_keyboard_business_contact(id, step):
    t = lib.Query.getRecordsByQuery('bdcu', f'ei = {id}')
    te = lib.Query.getRecordsByQuery('bdci', f'id != 0')
    keyboard_business_cont = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    for el in te:
        er = 0
        for x in t:
            if x['id_contact'] == el['id']:
                er = 1
        if er == 1:
            buttons.append(
                types.InlineKeyboardButton(text=f"✅{el['name']}", callback_data=f"num_cont_{id}_{el['id']}_1_{step}"))
        else:
            buttons.append(
                types.InlineKeyboardButton(text=f"{el['name']}", callback_data=f"num_cont_{id}_{el['id']}_0_{step}"))
    keyboard_business_cont.add(*buttons)
    return keyboard_business_cont


# Генерация клавиатуры ссылки
def get_keyboard_link(id):
    buttons = [
        # ссылки для поддержки
    ]
    keyboard_link = types.InlineKeyboardMarkup(row_width=1)
    keyboard_link.add(*buttons)
    return keyboard_link


# Генерация клавиатуры ссылки выбора системы пополнения
def get_keyboard_link_choose(m, id):
    buttons = [
        # выбор платёжной системы
    ]
    keyboard_link_choose = types.InlineKeyboardMarkup(row_width=2)
    keyboard_link_choose.add(*buttons)
    return keyboard_link_choose


# Генерация клавиатуры нравится ли анкета
def get_keyboard_fin(id):
    buttons = [
        types.InlineKeyboardButton(text="Мне нравится", callback_data=f"num_fin_{id}_0"),
        types.InlineKeyboardButton(text="Хочу кое-что поправить", callback_data=f"num_fin_{id}_1")
    ]
    keyboard_fin = types.InlineKeyboardMarkup(row_width=1)
    keyboard_fin.add(*buttons)
    return keyboard_fin


# Генерация клавиатуры нравится ли анкета
def get_keyboard_suport(id):
    buttons = [
        types.InlineKeyboardButton(text="У Вас крутая идея! Хочу поддержать", callback_data=f"num_sup_{id}_0"),
        types.InlineKeyboardButton(text="В другой раз", callback_data=f"num_sup_{id}_1")
    ]
    keyboard_sup = types.InlineKeyboardMarkup(row_width=1)
    keyboard_sup.add(*buttons)
    return keyboard_sup


# Генерация клавиатуры была ли встреча в субботу
def get_keyboard_saturday():
    buttons = [
        types.InlineKeyboardButton(text="Да, мы договорились о встрече", callback_data=f"num_saturday_1"),
        types.InlineKeyboardButton(text="Нет, партнёр не отвечает", callback_data=f"num_saturday_0")
    ]
    keyboard_saturday = types.InlineKeyboardMarkup(row_width=1)
    keyboard_saturday.add(*buttons)
    return keyboard_saturday


# Генерация клавиатуры если встреча была
def get_keyboard_feedback():
    keyboard_feedback = types.InlineKeyboardMarkup(row_width=5)
    te = [i for i in range(1, 6)]
    row_btns = [types.InlineKeyboardButton(text=f'{i}', callback_data=f'num_feedback_{i}') for i in te]
    keyboard_feedback.add(*row_btns)
    return keyboard_feedback


# Генерация клавиатуры пропуск обратной связи
def get_keyboard_feedback_pass(id):
    buttons = [
        types.InlineKeyboardButton(text="Пропустить", callback_data=f"num_pass_{id}")
    ]
    keyboard_feedback_pass = types.InlineKeyboardMarkup(row_width=1)
    keyboard_feedback_pass.add(*buttons)
    return keyboard_feedback_pass


# Генерация клавиатуры пропуск обратной связи
def get_keyboard_want(id):
    buttons = [
        types.InlineKeyboardButton(text="Хочу ещё!", callback_data=f"num_want_{id}")
    ]
    keyboard_want = types.InlineKeyboardMarkup(row_width=1)
    keyboard_want.add(*buttons)
    return keyboard_want


# Генерация клавиатуры хочешь больше встреч?
def get_keyboard_wantmore(id):
    buttons = [
        types.InlineKeyboardButton(text="Хочу больше встреч!", callback_data=f"num_wantmore_1_{id}")
        , types.InlineKeyboardButton(text="Буду встречаться один раз в неделю", callback_data=f"num_wantmore_0_{id}")
    ]
    keyboard_wantmore = types.InlineKeyboardMarkup(row_width=1)
    keyboard_wantmore.add(*buttons)
    return keyboard_wantmore


# Генерация клавиатуры ссылки
def get_keyboard_link2(id):
    buttons = [
        types.InlineKeyboardButton(text="Оплатить подписку", callback_data=f"num_link2_{id}")
    ]
    keyboard_link2 = types.InlineKeyboardMarkup(row_width=1)
    keyboard_link2.add(*buttons)
    return keyboard_link2


# Генерация клавиатуры в каком формате встреча
def get_keyboard_wedonline(id):
    buttons = [
        types.InlineKeyboardButton(text="Офлайн", callback_data=f"num_wedo_1_{id}")
        , types.InlineKeyboardButton(text="Онлайн", callback_data=f"num_wedo_0_{id}")
    ]
    keyboard_wedonline = types.InlineKeyboardMarkup(row_width=1)
    keyboard_wedonline.add(*buttons)
    return keyboard_wedonline


# Генерация клавиатуры присоединиться к проекту
def get_keyboard_new_user(id):
    buttons = [
        types.InlineKeyboardButton(text="Присоединиться к проекту", callback_data=f"num_new_{id}")
    ]
    keyboard_new_user = types.InlineKeyboardMarkup(row_width=1)
    keyboard_new_user.add(*buttons)
    return keyboard_new_user


# Генерация клавиатуры присоединиться к проекту
def get_keyboard_cancel_fee(id):
    buttons = [
        types.InlineKeyboardButton(text="Отмена", callback_data=f"num_canf_{id}")
    ]
    keyboard_cancel_fee = types.InlineKeyboardMarkup(row_width=1)
    keyboard_cancel_fee.add(*buttons)
    return keyboard_cancel_fee


async def finall_f(user_id):
    o_user = lib.Query.getRecordByQuery('u', f'ei = {user_id}')
    f_user = lib.Query.getRecordsByQuery('u_leisure', f'ei = {user_id}')
    s = ''
    for el in f_user:
        s += f"\n• {el['leisure_name']}"
    f_user_plus = lib.Query.getRecordsByQuery('u_leisure_plus', f'ei = {user_id}')
    s_plus = ''
    for el in f_user_plus:
        s_plus += f"\n• {el['leisure_name']}"
    cho = f"###"
    await bot.send_message(user_id,
                           f"<b>#######", reply_markup=get_keyboard_fin(user_id),
                           parse_mode=types.ParseMode.HTML)


async def finall(user_id):
    o_user = lib.Query.getRecordByQuery('u_business', f'ei = {user_id}')
    user_bc = lib.Query.getRecordsByQuery('u_business_contact', f'ei = {user_id}')
    user_bl = lib.Query.getRecordsByQuery('u_business_leisure', f'ei = {user_id}')
    user_bs = lib.Query.getRecordsByQuery('u_business_sector', f'ei = {user_id}')
    user_bs2 = lib.Query.getRecordsByQuery('u_business_sector2', f'ei = {user_id}')
    bc = ''
    for el in user_bc:
        bc += f"• {el['name_contact']}\n"
    bl = ''
    for el in user_bl:
        bl += f"• {el['name_leisure']}\n"
    bs = ''
    for el in user_bs:
        bs += f"• {el['name_sector']}\n"
    bs2 = ''
    for el in user_bs2:
        bs2 += f"• {el['name_sector']}\n"

    await bot.send_message(user_id,
                           f"############", reply_markup=get_keyboard_fin(user_id),
                           parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(dispatcher.filters.Text(startswith="num_"))
async def callbacks_num(call: types.CallbackQuery):
    action = call.data.split("_")[1]
    global u_fl
    global contact_b
    global deal_b
    global sector_b
    if action == "ban" or action == "unban":
        try:
            acti = call.data.split("*")[0]
            user_id = call.data.split("*")[1]
        except:
            await call.bot.send_message(log_group,
                                        f'{datetime.datetime.now()} : \nОШИБКА.обработка данных с кнопки Заблокировать/Разблокировать')
        try:
            ttemp = lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'blocked')
        except:
            await call.bot.send_message(log_group,
                                        f'{datetime.datetime.now()} : \nОШИБКА.обработка данных с кнопки.прочтение u_start и нахождение пользователя внутри неё')
        if acti == "num_ban_":
            bl = 1
        else:
            bl = 0
        try:
            idict = {'blocked': bl}
            lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
            if bl == 1:
                await call.message.edit_reply_markup(reply_markup=get_keyboard_unban(user_id))
                await call.message.answer('[info] Пользователь был успешно заблокирован')
                await call.bot.send_message(log_group, f'{datetime.datetime.now()} : \n[info]'
                                                       f'пользователь был успешно заблокирован')
            else:
                await call.message.edit_reply_markup(reply_markup=get_keyboard_ban(user_id))
                await call.message.answer('[info] Пользователь был успешно разблокирован')
                await call.bot.send_message(log_group, f'{datetime.datetime.now()} : \n[info]'
                                                       f'пользователь был успешно разблокирован')
        except:
            await call.message.answer(
                '[error] Возникла ошибка при блокировке пользователя, уже сообщил разработчику, он смотрит')
            await call.bot.send_message(log_group,
                                        f'{datetime.datetime.now()} : \nОШИБКА.обработка данных с кнопки.при блокировке пользователя')
    elif action == "sendEveryone":
        user_id = call.data.split("*")[1]
        idict = {'status': 'sendEveryone', 'ei': user_id}
        lib.Query.addRecordByQuery('u_status', idict)
        await bot.send_message(user_id, 'Напишите текст сообщения:')

    elif action == "sendFriends":
        user_id = call.data.split("*")[1]
        idict = {'status': 'sendFriendsme', 'ei': user_id}
        lib.Query.addRecordByQuery('u_status', idict)
        await bot.send_message(user_id, 'Напишите текст сообщения:')

    elif action == "sendBusiness":
        user_id = call.data.split("*")[1]
        idict = {'status': 'sendBusiness', 'ei': user_id}
        lib.Query.addRecordByQuery('u_status', idict)
        await bot.send_message(user_id, 'Напишите текст сообщения:')

    elif action == "new":
        try:
            user_id = call.data.split("_")[2]
            print(f'id из присоедениться к проекту {user_id}')
            ttemp = lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'blocked')
            if ttemp == 1:
                await call.message.edit_text(
                    f'К сожалению, ты был(а) заблокирован(а). Если это было ошибочно - просьба обратиться в техническую поддержку проекта')
            else:
                idict = {'status': 'name', 'ei': user_id}
                lib.Query.addRecordByQuery('u_status', idict)
                # await call.message.edit_text(
                #     'Сначала несколько общих вопросов. \nКак тебя зовут? \n<b>Напиши имя и фамилию</b>',
                #     parse_mode=types.ParseMode.HTML)
                await call.message.edit_text(
                    f"##################",
                    parse_mode=types.ParseMode.HTML)
                await call.message.answer('Присоединиться к проекту')
                await call.message.answer(
                    'вопрос1',
                    parse_mode=types.ParseMode.HTML)

        except:
            # await call.message.edit_text(
            #     'Мама мия!😰 Что-то пошло не так. Но я уже сообщил разработчику об ошибке, скоро всё уладим.')
            await call.message.answer(
                'Мама мия!😰 Что-то пошло не так. Но я уже сообщил разработчику об ошибке, скоро всё уладим.')
            await bot.send_message(log_group, f'{datetime.datetime.now()} : \nОШИБКА.new_user у пользователя ')
    elif action == "cancel":
        user_id = call.data.split("_")[2]
        lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
        # await call.message.edit_text('Понял, отменил запрос в тех поддержку')
        await call.message.answer('Отменить')
        await call.message.answer('Понял, отменил запрос в тех поддержку')
    elif action == "gender":
        user_id = int(call.data.split("_")[2])
        user_gender = int(call.data.split("_")[3])
        idict = {'gender': user_gender}
        await call.message.edit_text(
            f"Рад знакомству, {lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'first_name')}! Выбери свой пол")
        if user_gender == 0:
            await call.message.answer(f'Я - женщина 👧')
        else:
            await call.message.answer(f'Я - мужчина 👦')
        lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
        # await call.message.edit_text(f'В каком городе ты находишься большую часть времени? \n ',
        #                              reply_markup=get_keyboard_sity(user_id, 'r'))
        await call.message.answer(f'В каком городе ты находишься большую часть времени? \n ',
                                  reply_markup=get_keyboard_sity(user_id, 'r'))
    elif action == "sity":
        user_id = int(call.data.split("_")[2])
        user_sity = call.data.split("_")[3]
        step = call.data.split("_")[4]
        await call.message.edit_text(f'В каком городе ты находишься большую часть времени? \n ')
        await call.message.answer(user_sity)
        if step == 'r':
            if user_sity == '0':
                await call.message.answer('Понял, а из какого ты города?')
                idict = {'status': 'sity', 'ei': user_id}
                lib.Query.addRecordByQuery('u_status', idict)
            else:
                idict = {'sity': user_sity}
                lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
                await call.message.answer(
                    'Супер! У меня есть тут отличные ребята для общения :)\nНа каких языках тебе будет удобно общаться на встречах? Выбери все подходящие варианты',
                    reply_markup=get_keyboard_lang(user_id, 'r'))
        else:
            if user_sity == '0':
                await call.message.answer('Понял, а из какого ты города?')
                idict = {'status': 'sityedit', 'ei': user_id}
                lib.Query.addRecordByQuery('u_status', idict)
            else:
                idict = {'sity': user_sity}
                lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
                if (int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'business')) == 1) and (
                        int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'friends')) == 0):
                    # await call.message.edit_text(f"Посмотри, как будет выглядеть твой профиль для будущих друзей.")
                    await call.message.answer(f"Посмотри, как будет выглядеть твой профиль.")
                    asyncio.sleep(5)
                    await finall(user_id)
                else:
                    # await call.message.edit_text(f"Посмотри, как будет выглядеть твой профиль.")
                    await call.message.answer(f"Посмотри, как будет выглядеть твой профиль.")
                    asyncio.sleep(5)
                    await finall_f(user_id)
    elif action == "lang":
        user_id = int(call.data.split("_")[2])
        user_lang = call.data.split("_")[3]
        act = call.data.split("_")[4]
        step = call.data.split("_")[5]
        if step == 'r':
            if user_lang == '9':
                u_lang = lib.Query.checkCountByQuery('u_lang_id', f'ei = {user_id}')
                if u_lang != 0:
                    await call.message.edit_text(
                        'Супер! У меня есть тут отличные ребята для общения :)\nНа каких языках тебе будет удобно общаться на встречах? Выбери все подходящие варианты')
                    await call.message.answer('Готово')
                    await call.message.answer(
                        'Запомню, идем дальше\n\nСколько тебе лет?\n(Я никому не скажу, это лишь для статистики)😉\n\nВыбери свой год рождения ',
                        reply_markup=get_keyboard_year(user_id, 'r'))
                else:
                    # await call.message.edit_text(
                    #     'Нужно выбрать как минимум один язык на каком тебе будет удобно общаться на встречах. Но можно выбрать и несколько))',
                    #     reply_markup=get_keyboard_lang(user_id, step))
                    await call.message.answer(
                        'Нужно выбрать как минимум один язык на каком тебе будет удобно общаться на встречах. Но можно выбрать и несколько))',
                        reply_markup=get_keyboard_lang(user_id, step))
            else:
                if act == '0':
                    if user_lang == '0':
                        await call.message.answer('Английский')
                    elif user_lang == '1':
                        await call.message.answer('Грузинский')
                    elif user_lang == '2':
                        await call.message.answer('Русский')

                    idict = {'ei': user_id, 'lang_id': user_lang}
                    lib.Query.addRecordByQuery('u_lang_id', idict)
                else:
                    lib.Query.deleteRecordByQuery('u_lang_id',
                                                  f'ei = {user_id} AND lang_id = {user_lang};')
                await call.message.edit_reply_markup(reply_markup=get_keyboard_lang(user_id, step))
        else:
            if user_lang == '9':
                u_lang = lib.Query.checkCountByQuery('u_lang_id', f'ei = {user_id}')
                if u_lang != 0:
                    # await call.message.edit_text(f"Посмотри, как будет выглядеть твой профиль.")
                    await call.message.edit_text(
                        'Супер! У меня есть тут отличные ребята для общения :)\nНа каких языках тебе будет удобно общаться на встречах? Выбери все подходящие варианты')
                    await call.message.answer('Готово')

                    await call.message.answer(f"Посмотри, как будет выглядеть твой профиль.")
                    asyncio.sleep(5)
                    if (int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'business')) == 1) and (
                            int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'friends')) == 0):
                        await finall(user_id)
                    else:
                        await finall_f(user_id)
                else:
                    # await call.message.edit_text(
                    #     'Нужно выбрать как минимум один язык на каком тебе будет удобно общаться на встречах. Но можно выбрать и несколько))',
                    #     reply_markup=get_keyboard_lang(user_id, step))
                    await call.message.answer(
                        'Нужно выбрать как минимум один язык на каком тебе будет удобно общаться на встречах. Но можно выбрать и несколько))',
                        reply_markup=get_keyboard_lang(user_id, step))
            else:
                if act == '0':
                    if user_lang == '0':
                        await call.message.answer('Английский')
                    elif user_lang == '1':
                        await call.message.answer('Грузинский')
                    elif user_lang == '2':
                        await call.message.answer('Русский')
                    idict = {'ei': user_id, 'lang_id': user_lang}
                    lib.Query.addRecordByQuery('u_lang_id', idict)
                else:
                    lib.Query.deleteRecordByQuery('u_lang_id',
                                                  f'ei = {user_id} AND lang_id = {user_lang};')
                await call.message.edit_reply_markup(reply_markup=get_keyboard_lang(user_id, step))
    elif action == "gen-year":
        user_id = int(call.data.split("_")[2])
        year = call.data.split("_")[3]
        step = call.data.split("_")[4]
        await call.message.edit_text(
            'Запомню, идем дальше\n\nСколько тебе лет?\n(Я никому не скажу, это лишь для статистики)😉\n\nВыбери свой год рождения ')
        await call.message.answer(year)
        # await call.message.edit_text \
        #     (f'Теперь месяц', reply_markup=get_keyboard_mounth(user_id, year, step))
        await call.message.answer(f'Теперь месяц', reply_markup=get_keyboard_mounth(user_id, year, step))
    elif action == "gen-mounth":
        user_id = int(call.data.split("_")[2])
        year = call.data.split("_")[3]
        mounth = call.data.split("_")[4]
        step = call.data.split("_")[5]
        await call.message.edit_text(f'Теперь месяц')
    elif action == "gen-day":
        try:
            user_id = int(call.data.split("_")[2])
            year = call.data.split("_")[3]
            mounth = call.data.split("_")[4]
            day = call.data.split("_")[5]
            step = call.data.split("_")[6]
            bday = year + '-' + mounth + '-' + day
            idict = {'bday': bday}
            lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
            await call.message.edit_text(f'И день)')
            await call.message.answer(day)
            if step == 'r':
                # await call.message.edit_text(
                #     f'А теперь – самое интересное. Расскажи подробнее о своих приоритетах, и я подберу тебе вдохновляющего собеседника. \nНа чем сконцентрируемся в первую очередь?',
                #     reply_markup=get_keyboard_choose(user_id))
                await call.message.answer(
                    f'А теперь – самое интересное. Расскажи подробнее о своих приоритетах, и я подберу тебе вдохновляющего собеседника. \nНа чем сконцентрируемся в первую очередь?',
                    reply_markup=get_keyboard_choose(user_id))
            else:
                if (int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'business')) == 1) and (
                        int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'friends')) == 0):
                    # await call.message.edit_text(f"Посмотри, как будет выглядеть твой профиль.")
                    await call.message.answer(f"Посмотри, как будет выглядеть твой профиль.")
                    asyncio.sleep(5)
                    await finall(user_id)
                else:
                    # await call.message.edit_text(f"Посмотри, как будет выглядеть твой профиль.")
                    await call.message.answer(f"Посмотри, как будет выглядеть твой профиль.")
                    asyncio.sleep(5)
                    await finall_f(user_id)
        except:
            await call.bot.send_message(log_group,
                                        f"{datetime.datetime.now()} : \nОШИБКА.при добавлении дня рождения пользователя у "
                                        f"@{call.from_user.username}")
    elif action == "choose":
        user_id = int(call.data.split("_")[2])
        act = call.data.split("_")[3]
        await call.message.edit_text(
            f'А теперь – самое интересное. Расскажи подробнее о своих приоритетах, и я подберу тебе вдохновляющего собеседника. \nНа чем сконцентрируемся в первую очередь?')
        if act == '0':
            await call.message.answer(f"Найти друзей 🚴‍♂")
            # await call.message.edit_text \
            #     (f'Отметь 3 варианта досуга, которые тебе нравятся больше всего',
            #      reply_markup=get_keyboard_friends_leisure(user_id, 'fl', 'r'))
            await call.message.answer \
                (f'Отметь 3 варианта досуга, которые тебе нравятся больше всего',
                 reply_markup=get_keyboard_friends_leisure(user_id, 'fl', 'r'))
        else:
            await call.message.answer(f"НайтРасширить сеть деловых контактов 💶♂")
            # await call.message.edit_text \
            #     (f'Расскажи, чем ты сейчас занимаешься?', reply_markup=get_keyboard_business(user_id, 'r'))
            await call.message.answer \
                (f'Расскажи, чем ты сейчас занимаешься?', reply_markup=get_keyboard_business(user_id, 'r'))
    elif action == "fl":
        user_id = int(call.data.split("_")[2])
        table_id = int(call.data.split("_")[3])
        act = call.data.split("_")[4]
        step = call.data.split("_")[5]
        if step == 'r' or step == 'm':
            if act == '0':
                await call.message.answer(u_fl.at[table_id - 1, 'name'])
                idict = {'ei': user_id, 'fli': table_id}
                lib.Query.addRecordByQuery('flu', idict)
            else:
                lib.Query.deleteRecordByQuery('flu',
                                              f'ei = {user_id} AND fli = {table_id};')
            if int(lib.Query.checkCountByQuery('flu', f'ei = {user_id}')) < 3:
                await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure(user_id, 'fl', step))
                if table_id == 17:
                    await bot.send_message(user_id, 'Напишите свое увлечение: ')
                    idict = {'status': 'else', 'ei': user_id}
                    lib.Query.addRecordByQuery('u_status', idict)
            else:
                if step == 'r' or step == 'm':
                    # await call.message.edit_text(f'Отметь 3 варианта досуга, которые тебе нравятся больше всего')
                    await call.message.edit_text(
                        f'А теперь – самое интересное. Расскажи подробнее о своих приоритетах, и я подберу тебе вдохновляющего собеседника. \nНа чем сконцентрируемся в первую очередь?')
                    await call.message.answer(f'Отметь 3 варианта досуга, которые тебе нравятся больше всего')
                    await call.message.answer(f'Супер! У тебя много единомышленников :)' \
                                              f'\nА теперь выбери еще до 3-х вещей, чем любишь заниматься',
                                              reply_markup=get_keyboard_friends_leisure_plus(user_id, 'r'))
                else:
                    # await call.message.edit_text(f'Супер! У тебя много единомышленников :)')
                    await call.message.answer(f'Супер! У тебя много единомышленников :)')
        else:
            if int(lib.Query.checkCountByQuery('flu', f'ei = {user_id}')) == 3:
                if act == '0':
                    # await call.message.edit_text(
                    #     f'Максимум три увлечения, просьба убрать одно из указанных (нажать повторно на выбранный вариант), чтобы добавить новое',
                    #     reply_markup=get_keyboard_friends_leisure(user_id, 'fl', step))
                    await call.message.answer(
                        f'Максимум три увлечения, просьба убрать одно из указанных (нажать повторно на выбранный вариант), чтобы добавить новое',
                        reply_markup=get_keyboard_friends_leisure(user_id, 'fl', step))
                else:
                    lib.Query.deleteRecordByQuery('flu',
                                                  f'ei = {user_id} AND fli = {table_id};')
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure(user_id, 'fl', step))
            elif int(lib.Query.checkCountByQuery('flu', f'ei = {user_id}')) == 2:
                if act == '0':
                    await call.message.answer(u_fl.at[table_id - 1, 'name'])
                    idict = {'ei': user_id, 'fli': table_id}
                    lib.Query.addRecordByQuery('flu', idict)
                    # await call.message.edit_text(f'Отметь 3 варианта досуга, которые тебе нравятся больше всего')
                    await call.message.edit_text(
                        f'А теперь – самое интересное. Расскажи подробнее о своих приоритетах, и я подберу тебе вдохновляющего собеседника. \nНа чем сконцентрируемся в первую очередь?')
                    await call.message.answer(f'Отметь 3 варианта досуга, которые тебе нравятся больше всего')
                    await call.message.answer(f"Посмотри, как будет выглядеть твой профиль для будущих друзей.")
                    await asyncio.sleep(5)
                    await finall_f(user_id)
                else:
                    lib.Query.deleteRecordByQuery('flu',
                                                  f'ei = {user_id} AND fli = {table_id};')
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure(user_id, 'fl', step))
            else:
                if act == '0':
                    idict = {'ei': user_id, 'fli': table_id}
                    lib.Query.addRecordByQuery('flu', idict)
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure(user_id, 'fl', step))
                else:
                    lib.Query.deleteRecordByQuery('flu',
                                                  f'ei = {user_id} AND fli = {table_id};')
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure(user_id, 'fl', step))
    elif action == "flp":
        user_id = int(call.data.split("_")[2])
        table_id = int(call.data.split("_")[3])
        act = call.data.split("_")[4]
        step = call.data.split("_")[5]
        if step == 'r' or step == 'm':
            if act == '0':
                await call.message.answer(u_fl.at[table_id - 1, 'name'])
                idict = {'ei': user_id, 'fli': table_id}
                lib.Query.addRecordByQuery('flu_plus', idict)
            else:
                lib.Query.deleteRecordByQuery('flu_plus',
                                              f'ei = {user_id} AND fli = {table_id};')
            if int(lib.Query.checkCountByQuery('flu_plus', f'ei = {user_id}')) < 3:
                await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure_plus(user_id, step))
            else:

                await call.message.edit_text(f'А теперь выбери еще до 3-х вещей, чем любишь заниматься')
                # await call.message.answer(f'А теперь выбери еще до 3-х вещей, чем любишь заниматься')
                await call.message.answer(
                    f"Отлично! Добавь еще пару слов о том, чем занимаешься по работе (минимум 60 символов):")
                if step == 'r':
                    idict = {'status': 'free_time', 'ei': user_id}
                elif step == 'm':
                    idict = {'status': 'free_time_match', 'ei': user_id}
                lib.Query.addRecordByQuery('u_status', idict)
        else:
            if int(lib.Query.checkCountByQuery('flu_plus', f'ei = {user_id}')) == 3:
                if act == '0':
                    # await call.message.edit_text(
                    #     f'Максимум три увлечения, просьба убрать одно из указанных (нажать повторно на выбранный вариант), чтобы добавить новое',
                    #     reply_markup=get_keyboard_friends_leisure_plus(user_id, step))
                    await call.message.answer(
                        f'Максимум три увлечения, просьба убрать одно из указанных (нажать повторно на выбранный вариант), чтобы добавить новое',
                        reply_markup=get_keyboard_friends_leisure_plus(user_id, step))
                else:
                    lib.Query.deleteRecordByQuery('flu_plus',
                                                  f'ei = {user_id} AND fli = {table_id};')
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure_plus(user_id, step))
            elif int(lib.Query.checkCountByQuery('flu_plus', f'ei = {user_id}')) == 2:
                if act == '0':
                    await call.message.answer(u_fl.at[table_id - 1, 'name'])
                    idict = {'ei': user_id, 'fli': table_id}
                    lib.Query.addRecordByQuery('flu_plus', idict)

                    # await call.message.edit_text(f'Посмотри, как будет выглядеть твой профиль.')
                    await call.message.answer(f'Посмотри, как будет выглядеть твой профиль.')
                    asyncio.sleep(5)
                    await call.message.answer(
                        f"Отлично! Добавь еще пару слов о том, чем занимаешься по работе (минимум 60 символов):")
                    # await call.message.edit_text(f"")
                    await finall_f(user_id)
                else:
                    lib.Query.deleteRecordByQuery('flu_plus',
                                                  f'ei = {user_id} AND fli = {table_id};')
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure_plus(user_id, step))
            else:
                if act == '0':
                    idict = {'ei': user_id, 'fli': table_id}
                    lib.Query.addRecordByQuery('flu_plus', idict)
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure_plus(user_id, step))
                else:
                    lib.Query.deleteRecordByQuery('flu_plus',
                                                  f'ei = {user_id} AND fli = {table_id};')
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure_plus(user_id, step))
    elif action == "de":
        user_id = int(call.data.split("_")[2])
        id_deal = call.data.split("_")[3]
        step = call.data.split("_")[4]
        if step == 'r' or step == 'm':
            await call.message.answer(deal_b.at[int(id_deal) - 1, 'name'])
            idict = {'ei': user_id, 'id_deal': id_deal}
            lib.Query.addRecordByQuery('business_deal_u', idict)
            if step == 'r':
                await call.message.edit_reply_markup()
                await call.message.answer(
                    'В какой сфере? Максимум можно выбрать 3 сферы. Если выберешь меньше, нажми Готово — и мы продолжим',
                    reply_markup=get_keyboard_business_sector(user_id, 'sect', 'r'))
            elif step == 'm':
                await call.message.edit_reply_markup()
                await call.message.answer(
                    'В какой сфере? Максимум можно выбрать 3 сферы. Если выберешь меньше, нажми Готово — и мы продолжим',
                    reply_markup=get_keyboard_business_sector(user_id, 'sect', 'm'))
        else:
            idict = {'ei': user_id, 'id_deal': id_deal}
            lib.Query.addRecordByQuery('business_deal_u', idict)
            # await call.message.edit_text(f"Посмотри, как будет выглядеть твой профиль.")
            await call.message.answer(f"Посмотри, как будет выглядеть твой профиль.")
            await finall(user_id)
    elif action == "sect":
        user_id = int(call.data.split("_")[2])
        id_sect = int(call.data.split("_")[3])
        act = call.data.split("_")[4]
        step = call.data.split("_")[5]
        if step == 'r' or step == 'm':
            if act == '0':
                await call.message.answer(sector_b.at[id_sect - 1, 'name'])
                idict = {'ei': user_id, 'id_sector': id_sect}
                lib.Query.addRecordByQuery('bsu', idict)
            else:
                lib.Query.deleteRecordByQuery('bsu',
                                              f'ei = {user_id} AND id_sector = {id_sect};')
            if act == 'all':
                # await call.message.edit_text(
                #     f'Чтобы у твоего собеседника сложилось более полное представление о твоей профессиональной деятельности, расскажи о 2-3 эпизодах в работе, которыми ты гордишься.')
                await call.message.edit_reply_markup()
                await call.message.answer(
                    f'Чтобы у твоего собеседника сложилось более полное представление о твоей профессиональной деятельности, расскажи о 2-3 эпизодах в работе, которыми ты гордишься.')
                idict = {'status': 'deal', 'ei': user_id}
                lib.Query.addRecordByQuery('u_status', idict)
            elif int(lib.Query.checkCountByQuery('bsu', f'ei = {user_id}')) < 3:
                await call.message.edit_reply_markup(reply_markup=get_keyboard_business_sector(user_id, 'sect', step))
            else:
                await call.message.edit_reply_markup()
                await call.message.answer(
                    f'Чтобы у твоего собеседника сложилось более полное представление о твоей профессиональной деятельности, расскажи о 2-3 эпизодах в работе, которыми ты гордишься.')
                if step == 'r':
                    idict = {'status': 'deal', 'ei': user_id}
                elif step == 'm':
                    idict = {'status': 'deal_match', 'ei': user_id}
                lib.Query.addRecordByQuery('u_status', idict)
        else:
            if int(lib.Query.checkCountByQuery('bsu', f'ei = {user_id}')) == 3:
                if act == '0':
                    # await call.message.edit_text(
                    #     f'Максимум три увлечения, просьба убрать одно из указанных (нажать повторно на выбранный вариант), чтобы добавить новое',
                    #     reply_markup=get_keyboard_business_sector(user_id, 'sect', step))
                    await call.message.answer(
                        f'Максимум три увлечения, просьба убрать одно из указанных (нажать повторно на выбранный вариант), чтобы добавить новое',
                        reply_markup=get_keyboard_business_sector(user_id, 'sect', step))
                else:
                    lib.Query.deleteRecordByQuery('bsu',
                                                  f'ei = {user_id} AND id_sector = {id_sect};')
                    await call.message.edit_reply_markup(
                        reply_markup=get_keyboard_business_sector(user_id, 'sect', step))
            elif int(lib.Query.checkCountByQuery('bsu', f'ei = {user_id}')) == 2:
                if act == '0':
                    await call.message.answer(sector_b.at[id_sect - 1, 'name'])
                    idict = {'ei': user_id, 'id_sector': id_sect}
                    lib.Query.addRecordByQuery('bsu', idict)
                    await call.message.edit_reply_markup()
                    await call.message.answer(f"Посмотри, как будет выглядеть твой профиль для будущих друзей.")
                    asyncio.sleep(5)
                    await finall(user_id)
                else:
                    lib.Query.deleteRecordByQuery('bsu',
                                                  f'ei = {user_id} AND id_sector = {id_sect};')
                    await call.message.edit_reply_markup(
                        reply_markup=get_keyboard_business_sector(user_id, 'sect', step))
            else:
                if act == '0':
                    await call.message.answer(sector_b.at[id_sect - 1, 'name'])
                    idict = {'ei': user_id, 'id_sector': id_sect}
                    lib.Query.addRecordByQuery('bsu', idict)
                    await call.message.edit_reply_markup(
                        reply_markup=get_keyboard_business_sector(user_id, 'sect', step))
                else:
                    lib.Query.deleteRecordByQuery('bsu',
                                                  f'ei = {user_id} AND id_sector = {id_sect};')
                    await call.message.edit_reply_markup(
                        reply_markup=get_keyboard_business_sector(user_id, 'sect', step))
    elif action == "cont":
        user_id = int(call.data.split("_")[2])
        table_id = int(call.data.split("_")[3])
        act = call.data.split("_")[4]
        step = call.data.split("_")[5]
        if step == 'r' or step == 'm':
            if act == '0':
                await call.message.answer(contact_b.at[table_id - 1, 'name'])
                idict = {'ei': user_id, 'id_contact': table_id}
                lib.Query.addRecordByQuery('bdcu', idict)
            else:
                lib.Query.deleteRecordByQuery('bdcu',
                                              f'ei = {user_id} AND id_contact = {table_id};')
            if int(lib.Query.checkCountByQuery('bdcu', f'ei = {user_id}')) < 2:
                await call.message.edit_reply_markup(reply_markup=get_keyboard_business_contact(user_id, step))
            else:
                await call.message.edit_reply_markup()
                await call.message.answer(
                    f'С какой сферой хочешь связать работу/бизнес? Максимум можно выбрать только 3 сферы, если выбрал меньше - нажми Готово и мы продолжим',
                    reply_markup=get_keyboard_business_sector(user_id, 'sect2', step))
        else:
            if act == '0':
                await call.message.answer(contact_b.at[table_id - 1, 'name'])
                idict = {'ei': user_id, 'id_contact': table_id}
                lib.Query.addRecordByQuery('bdcu', idict)
            else:
                lib.Query.deleteRecordByQuery('bdcu',
                                              f'ei = {user_id} AND id_contact = {table_id};')
            if int(lib.Query.checkCountByQuery('bdcu', f'ei = {user_id}')) < 2:
                await call.message.edit_reply_markup(reply_markup=get_keyboard_business_contact(user_id, step))
            else:
                await call.message.edit_reply_markup()
                await call.message.answer(f"Посмотри, как будет выглядеть твой профиль для будущих друзей.")
                asyncio.sleep(5)
                await finall(user_id)
    elif action == "sect2":
        user_id = int(call.data.split("_")[2])
        id_sect = int(call.data.split("_")[3])
        act = call.data.split("_")[4]
        step = call.data.split("_")[5]
        if step == 'r' or step == 'm':
            if act == '0':
                await call.message.answer(sector_b.at[id_sect - 1, 'name'])
                idict = {'ei': user_id, 'id_sector': id_sect}
                lib.Query.addRecordByQuery('bs2u', idict)
            else:
                lib.Query.deleteRecordByQuery('bs2u',
                                              f'ei = {user_id} AND id_sector = {id_sect};')
            if act == 'all':
                await call.message.edit_reply_markup()
                await call.message.answer(
                    'Дальше! \n\nОтлично! Добавь еще пару слов о том, чем увлекаешься в свободное время (можно выбрать до 3 вариантов)',
                    reply_markup=get_keyboard_friends_leisure(user_id, 'bl', step))
            elif int(lib.Query.checkCountByQuery('bs2u', f'ei = {user_id}')) < 3:
                await call.message.edit_reply_markup(reply_markup=get_keyboard_business_sector(user_id, 'sect2', step))
            else:
                await call.message.edit_reply_markup()
                await call.message.answer(
                    'Дальше! \n\nОтлично! Добавь еще пару слов о том, чем увлекаешься в свободное время (можно выбрать до 3 вариантов)',
                    reply_markup=get_keyboard_friends_leisure(user_id, 'bl', step))
        else:
            if int(lib.Query.checkCountByQuery('bs2u', f'ei = {user_id}')) == 3:
                if act == '0':
                    await call.message.edit_text(
                        f'Максимум три сферы, просьба убрать одну из указанных (нажать повторно на выбранный вариант), чтобы добавить новое',
                        reply_markup=get_keyboard_business_sector(user_id, 'sect2', step))
                    # await call.message.answer(
                    #     f'Максимум три сферы, просьба убрать одну из указанных (нажать повторно на выбранный вариант), чтобы добавить новое',
                    #     reply_markup=get_keyboard_business_sector(user_id, 'sect2', step))
                else:
                    lib.Query.deleteRecordByQuery('bs2u',
                                                  f'ei = {user_id} AND id_sector = {id_sect};')
                    await call.message.edit_reply_markup(
                        reply_markup=get_keyboard_business_sector(user_id, 'sect2', step))
            elif int(lib.Query.checkCountByQuery('bs2u', f'ei = {user_id}')) == 2:
                if act == '0':
                    await call.message.answer(sector_b.at[id_sect - 1, 'name'])
                    idict = {'ei': user_id, 'id_sector': id_sect}
                    lib.Query.addRecordByQuery('bs2u', idict)
                    await call.message.edit_reply_markup()
                    await call.message.answer(f"Посмотри, как будет выглядеть твой профиль.")
                    await finall(user_id)
                else:
                    lib.Query.deleteRecordByQuery('bs2u',
                                                  f'ei = {user_id} AND id_sector = {id_sect};')
                    await call.message.edit_reply_markup(
                        reply_markup=get_keyboard_business_sector(user_id, 'sect2', step))
            else:
                if act == '0':
                    await call.message.answer(sector_b.at[id_sect - 1, 'name'])
                    idict = {'ei': user_id, 'id_sector': id_sect}
                    lib.Query.addRecordByQuery('bs2u', idict)
                    await call.message.edit_reply_markup(
                        reply_markup=get_keyboard_business_sector(user_id, 'sect2', step))
                else:
                    lib.Query.deleteRecordByQuery('bs2u',
                                                  f'ei = {user_id} AND id_sector = {id_sect};')
                    await call.message.edit_reply_markup(
                        reply_markup=get_keyboard_business_sector(user_id, 'sect2', step))
    elif action == "bl":
        user_id = int(call.data.split("_")[2])
        table_id = int(call.data.split("_")[3])
        act = call.data.split("_")[4]
        step = call.data.split("_")[5]
        if step == 'r' or step == 'm':
            if act == '0':
                await call.message.answer(u_fl.at[table_id - 1, 'name'])
                idict = {'ei': user_id, 'leisure_id': table_id}
                lib.Query.addRecordByQuery('blu', idict)
            else:
                lib.Query.deleteRecordByQuery('blu',
                                              f'ei = {user_id} AND leisure_id = {table_id};')
            if int(lib.Query.checkCountByQuery('blu', f'ei = {user_id}')) < 3:
                await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure(user_id, 'bl', step))
            else:
                if step == 'r':
                    await call.message.edit_reply_markup()
                    idict = {'business': 1, 'week': 0}
                    lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
                    await call.message.answer(f"Посмотри, как будет выглядеть твой профиль.")
                    idict1 = {'ei': user_id}
                    lib.Query.addRecordByQuery('u_fee', idict1)
                    await finall(user_id)
                elif step == 'm':
                    await call.message.edit_reply_markup()
                    try:
                        await bot.set_my_commands(
                            commands=[
                                types.BotCommand('link', 'Поддержать проект'),
                                types.BotCommand('help', 'Написать в поддержку'),
                                types.BotCommand('edit_fl', 'Изменить в анкете друзья то, что нравится больше всего'),
                                types.BotCommand('edit_flp', 'Изменить в анкете друзья чем люблю заниматься'),
                                types.BotCommand('edit_fact', 'Изменить в анкете друзья факты о работе'),
                                types.BotCommand('edit_deal', 'Изменить в анкете бизнес вид своей деятельности'),
                                types.BotCommand('edit_sector', 'Изменить в анкете бизнес сферы деятельности'),
                                types.BotCommand('edit_deal_fact', 'Изменить в анкете бизнес свои достижения в работе'),
                                types.BotCommand('edit_contact', 'Изменить в анкете бизнес цель контактов'),
                                types.BotCommand('edit_sector2',
                                                 'Изменить в анкете бизнес сферы, с которыми хочешь связать работу/бизнес'),
                                types.BotCommand('edit_bl', 'Изменить в анкете бизнес увлечения в свободное время')
                            ],
                            scope=types.BotCommandScopeChat(chat_id=call.from_user.id)
                        )
                    except:
                        await bot.send_message(log_group,
                                               f'{datetime.datetime.now()} : \nОШИБКА.start.при отправке меню пользователю')
                    await call.message.answer(f"Отлично! Сейчас подберу тебе пару")
                    await match_business(user_id)
        else:
            if int(lib.Query.checkCountByQuery('blu', f'ei = {user_id}')) == 3:
                if act == '0':
                    await call.message.edit_text(
                        f'Максимум три сферы, просьба убрать одну из указанных (нажать повторно на выбранный вариант), чтобы добавить новое',
                        reply_markup=get_keyboard_friends_leisure(user_id, 'bl', step))
                else:
                    lib.Query.deleteRecordByQuery('blu',
                                                  f'ei = {user_id} AND leisure_id = {table_id};')
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure(user_id, 'bl', step))
            elif int(lib.Query.checkCountByQuery('blu', f'ei = {user_id}')) == 3:
                if act == '0':
                    await call.message.answer(u_fl.at[table_id - 1, 'name'])
                    idict = {'ei': user_id, 'leisure_id': table_id}
                    lib.Query.addRecordByQuery('blu', idict)
                    await call.message.edit_reply_markup()
                    await call.message.answer(f"Посмотри, как будет выглядеть твой профиль.")
                    await finall(user_id)
                else:
                    lib.Query.deleteRecordByQuery('blu',
                                                  f'ei = {user_id} AND leisure_id = {table_id};')
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure(user_id, 'bl', step))
            else:
                if act == '0':
                    idict = {'ei': user_id, 'leisure_id': table_id}
                    lib.Query.addRecordByQuery('blu', idict)
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure(user_id, 'bl', step))
                else:
                    lib.Query.deleteRecordByQuery('blu',
                                                  f'ei = {user_id} AND leisure_id = {table_id};')
                    await call.message.edit_reply_markup(reply_markup=get_keyboard_friends_leisure(user_id, 'bl', step))
    elif action == "fin":
        user_id = int(call.data.split("_")[2])
        act = call.data.split("_")[3]
        if (int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'business')) == 1) and (
                int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'friends')) == 0):
            try:
                await bot.set_my_commands(
                    commands=[
                        types.BotCommand('link', 'Поддержать проект'),
                        types.BotCommand('help', 'Написать в поддержку'),
                        types.BotCommand('edit_deal', 'Изменить в анкете бизнес вид своей деятельности'),
                        types.BotCommand('edit_sector', 'Изменить в анкете бизнес сферы деятельности'),
                        types.BotCommand('edit_deal_fact', 'Изменить в анкете бизнес свои достижения в работе'),
                        types.BotCommand('edit_contact', 'Изменить в анкете бизнес цель контактов'),
                        types.BotCommand('edit_sector2',
                                         'Изменить в анкете бизнес сферы, с которыми хочешь связать работу/бизнес'),
                        types.BotCommand('edit_bl', 'Изменить в анкете бизнес увлечения в свободное время')
                    ],
                    scope=types.BotCommandScopeChat(chat_id=call.from_user.id)
                )
            except:
                await bot.send_message(log_group,
                                       f'{datetime.datetime.now()} : \nОШИБКА.start.при отправке меню пользователю')
        elif int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'business')) == 1 and int(
                lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'friends')) == 1:
            try:
                await bot.set_my_commands(
                    commands=[
                        types.BotCommand('link', 'Поддержать проект'),
                        types.BotCommand('help', 'Написать в поддержку'),
                        types.BotCommand('edit_fl', 'Изменить в анкете друзья то, что нравится больше всего'),
                        types.BotCommand('edit_flp', 'Изменить в анкете друзья чем люблю заниматься'),
                        types.BotCommand('edit_fact', 'Изменить в анкете друзья факты о работе'),
                        types.BotCommand('edit_deal', 'Изменить в анкете бизнес вид своей деятельности'),
                        types.BotCommand('edit_sector', 'Изменить в анкете бизнес сферы деятельности'),
                        types.BotCommand('edit_deal_fact', 'Изменить в анкете бизнес свои достижения в работе'),
                        types.BotCommand('edit_contact', 'Изменить в анкете бизнес цель контактов'),
                        types.BotCommand('edit_sector2',
                                         'Изменить в анкете бизнес сферы, с которыми хочешь связать работу/бизнес'),
                        types.BotCommand('edit_bl', 'Изменить в анкете бизнес увлечения в свободное время')
                    ],
                    scope=types.BotCommandScopeChat(chat_id=call.from_user.id)
                )
            except:
                await bot.send_message(log_group,
                                       f'{datetime.datetime.now()} : \nОШИБКА.start.при отправке меню пользователю')
        else:
            try:
                await bot.set_my_commands(
                    commands=[
                        types.BotCommand('link', 'Поддержать проект'),
                        types.BotCommand('help', 'Написать в поддержку'),
                        types.BotCommand('edit_fl', 'Изменить в анкете друзья то, что нравится больше всего'),
                        types.BotCommand('edit_flp', 'Изменить в анкете друзья чем люблю заниматься'),
                        types.BotCommand('edit_fact', 'Изменить в анкете друзья факты о работе')
                    ],
                    scope=types.BotCommandScopeChat(chat_id=call.from_user.id)
                )
            except:
                await bot.send_message(log_group,
                                       f'{datetime.datetime.now()} : \nОШИБКА.start.при отправке меню пользователю')
        if act == '0':

            await call.message.edit_reply_markup()
            if (int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'business')) == 1):
                await call.message.answer(
                    f"Круто! Ты – жемчужина нашего делового сообщества! Уже не терпится представить тебя другим участникам.")
            else:
                await call.message.answer(
                    f"Кайф! От твоей анкеты не оторваться! Уже не терпится представить тебя другим участникам сообщества.")
                await asyncio.sleep(3)
            await call.message.answer(
                f"<b>Тестовый период</b> начался, у тебя есть 2️⃣ бесплатные встречи чтобы познакомиться с сервисом поближе, желаю удачи ✌️",
                parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(3)
            await call.message.answer(
                f"Дождись <b>четверга</b>, и я подберу тебе пару для общения. \nКак только получишь сообщение, напиши первым и договорись о <b>встрече</b> или <b>видеочате</b>.\n" \
                f"Всегда на связи, <b>Let's meet</b> бот, твой проводник к качественному окружению.\n\nПодписывайся на наш канал:\nhttps://t.me/+bztYAcGH3DcyNzli",
                parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(3)
        else:
            await call.message.edit_reply_markup()
            await call.message.answer(f"Ты всегда можешь откорректировать свою анкету, используя Меню.")
    elif action == "sup":
        user_id = int(call.data.split("_")[2])
        act = call.data.split("_")[3]
        await call.message.edit_reply_markup()
        if act == '0':
            await call.message.answer(f"У Вас крутая идея! Хочу поддержать")
            # await call.message.edit_text(f"Хочешь больше встреч? Подпишись", reply_markup=get_keyboard_link(user_id))
            await call.message.answer(f"Хочешь больше встреч? Подпишись", reply_markup=get_keyboard_link(user_id))
        else:
            await call.message.answer(f"В другой раз")
            # await call.message.edit_text(
            #     f"Дождись четверга, и я подберу тебе пару для общения. Как только получишь сообщение, напиши первым и договорись о встрече или видеочате.\n" \
            #     f"Всегда на связи, Let's meet бот, твой проводник к качественному окружению.\n\nПодписывайся на наш канал:\nhttps://t.me/+bztYAcGH3DcyNzli")
            await call.message.answer(
                f"Дождись четверга, и я подберу тебе пару для общения. Как только получишь сообщение, напиши первым и договорись о встрече или видеочате.\n" \
                f"Всегда на связи, Let's meet бот, твой проводник к качественному окружению.\n\nПодписывайся на наш канал:\nhttps://t.me/+bztYAcGH3DcyNzli")
    elif action == "link":
        user_id = int(call.data.split("_")[2])
        # await call.message.edit_text(
        #     f"Отлично, а через какую именно систему произошло пополнение?",
        #     reply_markup=get_keyboard_link_choose('r', user_id))
        await call.message.answer(
            f"Отлично, а через какую именно систему произошло пополнение?",
            reply_markup=get_keyboard_link_choose('r', user_id))
    elif action == 'lch':
        act = call.data.split("_")[2]
        user_id = int(call.data.split("_")[3])
        step = call.data.split("_")[4]
        await call.message.edit_reply_markup()
        if act == '0':
            if step == 'r':
                idict = {'status': 'email', 'ei': user_id}
            else:
                idict = {'status': 'email1', 'ei': user_id}
            lib.Query.addRecordByQuery('u_status', idict)
            # act = call.data.split("_")[3]
            # await call.message.edit_text(
            #     f"<b>Спасибо за поддержку!!!</b> \nПодскажи <b>email</b>, по которыму произошла подписка, чтобы мы могли найти тебя",
            #     parse_mode=types.ParseMode.HTML)
            await call.message.answer('Патреон')
            await call.message.answer(
                f"<b>Спасибо за поддержку!!!</b> \nПодскажи <b>email</b>, по которыму произошла подписка, чтобы мы могли найти тебя",
                parse_mode=types.ParseMode.HTML)
        else:
            if step == 'r':
                idict = {'status': 'pay', 'ei': user_id}
            else:
                idict = {'status': 'pay1', 'ei': user_id}
            lib.Query.addRecordByQuery('u_status', idict)
            await call.message.answer('Пейформ')
            # await call.message.edit_text(
            #     f"<b>Спасибо за поддержку!!!</b> \nПодскажи <b>номер телефона</b> в формате 7**********, по которыму произошла подписка, чтобы я мог найти тебя",
            #     parse_mode=types.ParseMode.HTML)
            await call.message.answer(
                f"<b>Спасибо за поддержку!!!</b> \nПодскажи <b>номер телефона</b> в формате 7**********, по которыму произошла подписка, чтобы я мог найти тебя",
                parse_mode=types.ParseMode.HTML)
            # pay
    elif action == "saturday":
        act = call.data.split("_")[2]
        user_id = call.from_user.id
        await call.message.edit_reply_markup()
        if act == '1':
            await call.message.answer(f"Да, мы договорились о встрече")
            # await call.message.edit_text(f"Отлично! Можешь поделиться впечатлениями о встрече?",
            #                              reply_markup=get_keyboard_feedback())
            await call.message.answer(f"Отлично! Можешь поделиться впечатлениями о встрече?",
                                      reply_markup=get_keyboard_feedback())
        else:
            await call.message.answer(f"Нет, партнёр не отвечает")
            # await call.message.edit_text(
            #     f"Окей, бывает. Сейчас постараюсь найти тебе ещё одну пару")  # ---------------------------ALARM LIST
            await call.message.answer(
                f"Окей, бывает. Сейчас постараюсь найти тебе ещё одну пару")
            u_f = lib.Query.getRecordsByQuery('u_business',
                                              f'ei != 0')  # забирает всех пользователей по анкете бизнес
            u = pd.DataFrame(u_f)
            idx_0 = u[pd.to_numeric(u["ei"], errors="coerce") == user_id].index
            tem_u = int(u.iloc[idx_0.to_list()[0]]['col_meet'])
            tem_u -= 1
            idict = {'meet': 0, 'col_meet': tem_u}
            lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
            if int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'business')) == 1:
                await match_business(user_id)

            else:
                await match_friends(user_id)
    elif action == "feedback":
        act = int(call.data.split("_")[2])
        user_id = call.from_user.id
        u_f = lib.Query.getRecordsByQuery('u', f'ei != 0')  # забирает всех пользователей
        u = pd.DataFrame(u_f)
        idx = u[pd.to_numeric(u["ei"], errors="coerce") == user_id].index
        await call.message.edit_reply_markup()
        await call.message.answer(act)
        for el in idx:
            if int(u.at[el, "friends"]) == 1:
                u_match = lib.Query.getRecordsByQuery('my_match',
                                                      f'ei != 0')  # забирает всех пользователей из матчей друзей
                tery = 'my_match'
            elif int(u.at[el, "business"]) == 1:
                u_match = lib.Query.getRecordsByQuery('my_match_b',
                                                      f'ei != 0')  # забирает всех пользователей из матчей бизнес
                tery = 'my_match_b'
            t_match = pd.DataFrame(u_match)
            idx1 = t_match[pd.to_numeric(t_match["ei"], errors="coerce") == user_id].index
            idx2 = t_match[pd.to_numeric(t_match["ei2"], errors="coerce") == user_id].index
            if idx1.to_list():
                for el in idx1.to_list():
                    # t_match.at[el, 'score1'] = act
                    idict = {'score1': act}
                    lib.Query.updateRecordByQuery(f'{tery}', idict, f'ei = {user_id}')
            if idx2.to_list():
                for el in idx2.to_list():
                    idict = {'score2': act}
                    lib.Query.updateRecordByQuery(f'{tery}', idict, f'ei2 = {user_id}')
        # await call.message.edit_text(
        #     f"Что именно оставило такое впечатление? (Напиши в сообщении или нажми Пропустить)",
        #     reply_markup=get_keyboard_feedback_pass(user_id))
        await call.message.answer(
            f"Что именно оставило такое впечатление? (Напиши в сообщении или нажми Пропустить)",
            reply_markup=get_keyboard_feedback_pass(user_id))
        idict = {'status': 'feedback', 'ei': user_id}
        lib.Query.addRecordByQuery('u_status', idict)
    elif action == "pass":
        await call.message.edit_reply_markup()
        await call.message.answer('Пропустить')
        user_id = int(call.data.split("_")[2])
        lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
        # await call.message.edit_text(f"Хочешь еще встречу?", reply_markup=get_keyboard_want(user_id))
        await call.message.answer(f"Хочешь еще встречу?", reply_markup=get_keyboard_want(user_id))
    elif action == "want":
        await call.message.edit_reply_markup()
        await call.message.answer('Хочу ещё!')
        user_id = int(call.data.split("_")[2])
        if int(lib.Query.checkCountByQuery('u_fee', f'ei = {user_id}')) > 0:
            u_fee = lib.Query.getRecordByQuery('u_fee', f'ei = {user_id}')  # забирает всех пользователей
            u_f = lib.Query.getRecordByQuery('u', f'ei = {user_id}')
            # if u_fee['tariff'] == 1 or u_fee['tariff'] == 2 or u_fee['tariff'] == 9:
            if int(u_fee['tariff']) != 9:
                if int(u_fee['tariff']) > int(u_f['col_meet']):
                    # await call.message.edit_text(f"Хорошо, с кем хочешь встретиться на этот раз?",
                    #                              reply_markup=get_keyboard_more(user_id))
                    await call.message.answer(f"Хорошо, с кем хочешь встретиться на этот раз?",
                                              reply_markup=get_keyboard_more(user_id))
                else:
                    # await call.message.edit_text(f"Хочешь больше встреч? Подпишись на наш pat или pay",
                    #                              reply_markup=get_keyboard_wantmore(user_id))
                    await call.message.answer(f"Хочешь больше встреч? Подпишись на наш pat или pay",
                                              reply_markup=get_keyboard_wantmore(user_id))
            else:
                # await call.message.edit_text(f"Хорошо, с кем хочешь встретиться на этот раз?",
                #                              reply_markup=get_keyboard_more(user_id))
                await call.message.answer(f"Хорошо, с кем хочешь встретиться на этот раз?",
                                          reply_markup=get_keyboard_more(user_id))
    elif action == "wantmore":
        act = call.data.split("_")[2]
        user_id = int(call.data.split("_")[3])
        await call.message.edit_reply_markup()
        if act == '1':
            await call.message.answer('Хочу больше встреч!')
            # await call.message.edit_text(f"Хочешь больше встреч? Подпишись", reply_markup=get_keyboard_link1(user_id))
            await call.message.answer(f"Хочешь больше встреч? Подпишись", reply_markup=get_keyboard_link1(user_id))
        else:
            await call.message.answer('Буду встречаться один раз в неделю')
            # await call.message.edit_text(
            #     f"Дождись четверга, и я подберу тебе пару для общения. Как только получишь сообщение, напиши первым и договорись о встрече или видеочате.\n" \
            #     f"Всегда на связи, Let's meet бот, твой проводник к качественному окружению.\n\nПодписывайся на наш канал:\nhttps://t.me/+bztYAcGH3DcyNzli")
            await call.message.answer(
                f"Дождись четверга, и я подберу тебе пару для общения. Как только получишь сообщение, напиши первым и договорись о встрече или видеочате.\n" \
                f"Всегда на связи, Let's meet бот, твой проводник к качественному окружению.\n\nПодписывайся на наш канал:\nhttps://t.me/+bztYAcGH3DcyNzli")
    elif action == "link1":
        await call.message.edit_reply_markup()
        user_id = int(call.data.split("_")[2])
        # await call.message.edit_text(
        #     f"Отлично, а через какую именно систему произошло пополнение?",
        #     reply_markup=get_keyboard_link_choose('m', user_id))
        await call.message.answer(
            f"Отлично, а через какую именно систему произошло пополнение?",
            reply_markup=get_keyboard_link_choose('m', user_id))
    elif action == "link2":
        await call.message.edit_reply_markup()
        user_id = int(call.data.split("_")[2])
        # await call.message.edit_text(f"Оформить подписку можно следующим образом",
        #                              reply_markup=get_keyboard_link(user_id))
        await call.message.answer(f"Оформить подписку можно следующим образом",
                                  reply_markup=get_keyboard_link(user_id))
    elif action == "more":
        await call.message.edit_reply_markup()
        act = call.data.split("_")[2]
        user_id = int(call.data.split("_")[3])
        idict = {'meet': 0}
        lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
        if act == '1':
            await call.message.answer('Найти друзей 🚴‍♂')
            if int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'friends')) == 1:
                # await call.message.edit_text(f'Хорошо, сейчас найду тебе пару')
                await call.message.answer(f'Хорошо, сейчас найду тебе пару')
                await match_friends(user_id)
                # pass # ----------------------------------------------------ИЩЕМ ПАРУ ПО ДРУЗЬЯМ
            else:
                # await call.message.edit_text(f'Не нашёл анкету по напрвлению поиска друзей. Сейчас можем заполнить. '
                #                              f'Отметь 3 варианта досуга, которые тебе нравятся больше всего',
                #                              reply_markup=get_keyboard_friends_leisure(user_id, 'fl', 'm'))
                await call.message.answer(f'Не нашёл анкету по напрвлению поиска друзей. Сейчас можем заполнить. '
                                          f'Отметь 3 варианта досуга, которые тебе нравятся больше всего',
                                          reply_markup=get_keyboard_friends_leisure(user_id, 'fl', 'm'))
                # pass # ---------------- Заполняем регистрацию по анкете друзей и сразу выдаём пару по итогу
        else:
            await call.message.answer('Расширить сеть деловых контактов  💶♂')
            if int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'business')) == 1:
                await call.answer()
                # await call.message.edit_text(f'Хорошо, сейчас найду тебе пару')
                await call.message.answer(f'Хорошо, сейчас найду тебе пару')
                await match_business(user_id)
                # pass # ---------------------------------------------ИЩЕМ ПАРУ ПО БИЗНЕСУ
            else:
                # await call.message.edit_text \
                #     (f'Не нашёл анкету по напрвлению поиска бизнес контактов. Сейчас можем заполнить. '
                #      f'Расскажи, чем ты сейчас занимаешься?', reply_markup=get_keyboard_business(user_id, 'm'))
                await call.message.answer \
                    (f'Не нашёл анкету по напрвлению поиска бизнес контактов. Сейчас можем заполнить. '
                     f'Расскажи, чем ты сейчас занимаешься?', reply_markup=get_keyboard_business(user_id, 'm'))
                # pass # --------------------- Заполняем регистрацию по анкете бизнеса и сразу выдаём пару по итогу
    elif action == "wed":
        await call.message.edit_reply_markup()
        act = call.data.split("_")[2]
        user_id = int(call.data.split("_")[3])
        idict = {'week': int(act)}
        lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
        if act == '0':
            await call.message.answer(f'Нет')
            await call.message.answer(f'Хорошо! Напишу тебе через недел')
            # await call.message.edit_text(f'Хорошо! Напишу тебе через неделю!')
        else:
            await call.message.answer(f'Да')
            t_sit_us = lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'sity')
            if str(t_sit_us) != 'Батуми' or str(t_sit_us) != 'Тбилиси':
                # await call.message.edit_text(f'В каком формате организовать эту встречу?',
                #                              reply_markup=get_keyboard_wedonline(user_id))
                await call.message.answer(f'В каком формате организовать эту встречу?',
                                          reply_markup=get_keyboard_wedonline(user_id))
            else:
                # await call.message.edit_text(f'Отлично!👍\nНапишу тебе в четверг.')
                await call.message.answer(f'Отлично!👍\nНапишу тебе в четверг.')
    elif action == "wedo":
        await call.message.edit_reply_markup()
        act = call.data.split("_")[2]
        user_id = int(call.data.split("_")[3])
        if act == '0':
            await call.message.answer(f'Онлайн')
            # await call.message.edit_text(f'Отлично!👍\nНапишу тебе в четверг.')
            await call.message.answer(f'Отлично!👍\nНапишу тебе в четверг.')
        else:
            await call.message.answer(f'Офлайн')
            # await call.message.edit_text(f'Из какого города собеседника ищем?',
            #                              reply_markup=get_keyboard_wedsity(user_id))
            await call.message.answer(f'Из какого города собеседника ищем?',
                                      reply_markup=get_keyboard_wedsity(user_id))
    elif action == "ws":
        await call.message.edit_reply_markup()
        act = call.data.split("_")[2]
        await call.message.answer(act)
        user_id = int(call.data.split("_")[3])
        idict = {'sity': act}
        lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
        # await call.message.edit_text(f'Отлично!👍\nНапишу тебе в четверг.')
        await call.message.answer(f'Отлично!👍\nНапишу тебе в четверг.')
    elif action == 'canf':
        await call.message.edit_reply_markup()
        await call.message.answer(f'Отмена')
        user_id = call.data.split("_")[2]
        lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
        await call.message.edit_text(f'Всё ок, вышел из режима оплаты подписки')
        await call.message.answer(f'Всё ок, вышел из режима оплаты подписки')
    elif action == "p":
        act = call.data.split("_")[2]
        step = call.data.split("_")[3]
        user_id = call.data.split("_")[4]
        user_email = call.data.split("_")[5]
        if act == '0':
            await bot.send_message(user_id,
                                   f'Привет, к сожалению, модераторы не нашли действующей подписки по указанному email/телефону: {user_email}. ' \
                                   f'Просьба проверить данные, в случае наличия активной подписки связаться с тех.поддержкой. Спасибо за понимание')
            # await call.message.edit_text(
            #     f'Вас понял, написал пользователю, что подписка не была найдена с просьбой повторить операцию, либо связаться с тех.поддержкой')
            await call.message.answer(
                f'Вас понял, написал пользователю, что подписка не была найдена с просьбой повторить операцию, либо связаться с тех.поддержкой')
        else:
            idict = {'ei': user_id, 'email': user_email, 'tariff': act}
            lib.Query.updateRecordByQuery('u_fee', idict, f'ei = {user_id}')
            idict1 = {'ei': user_id, 'col_meet': 0}
            lib.Query.updateRecordByQuery('u', idict1, f'ei = {user_id}')
            # await call.message.edit_text(f'Подписка подтверждена, данные в системе успешно обновлены')
            await call.message.answer(f'Подписка подтверждена, данные в системе успешно обновлены')
            if step != 'r':
                await bot.send_message(user_id, f'Привет, подписка успешно подтверждена, сейчас найду тебе новую пару')
                if int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'business')) == 1:
                    await match_business(user_id)
                elif int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'friends')) == 1:
                    await match_friends(user_id)
    await call.answer()


# функция ведения базы людей, взаимодействующих с ботом
@dp.message_handler(commands="start")
async def start(message: types.Message):
    try:
        print(message.from_user.id)
        await message.delete()
        user_id = int(message.from_user.id)
        o_user = lib.Query.checkCountByQuery('u', f'ei = {user_id}')
        if o_user == 0:
            user_username = message.from_user.username
            user_first_name = message.from_user.first_name
            idict = {'ei': user_id, 'external_username': f'{user_username}',
                     'first_name': f'{user_first_name}'}
            lib.Query.addRecordByQuery('u', idict)
            await message.answer(
                f"###########",
                reply_markup=get_keyboard_new_user(user_id), parse_mode=types.ParseMode.HTML)
        else:
            ttemp = lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'blocked')
            if ttemp == 0:
                await message.answer(
                    f'Мы с тобой уже знакомились! Если ты забыл меня, не переживай, я не обиделся :) А если ты сделал это нарочно – не делай так больше. Иначе мне придётся тебя заблокировать.')
                await message.bot.send_message(log_group, f"{datetime.datetime.now()} :\n[info] пользователь "
                                                          f"@{message.from_user.username}, уже зареган",
                                               reply_markup=get_keyboard_ban(int(message.from_user.id)))
            else:
                await message.answer(
                    f'К сожалению, ты был(а) заблокирован(а). Если это было ошибочно - просьба обратиться в техническую поддержку проекта')
                await message.bot.send_message(log_group,
                                               f"{datetime.datetime.now()} :\n[info] пользователь @{message.from_user.username} пытался нажать /start"
                                               f", но уже заблокирован",
                                               reply_markup=get_keyboard_unban(int(message.from_user.id)))
    except:
        await message.answer(
            'Мама мия!😰 Что-то пошло не так. Но я уже сообщил разработчику об ошибке, скоро всё уладим.')
        await bot.send_message(log_group,
                               f'{datetime.datetime.now()} : \nОШИБКА.start у пользователя @{message.from_user.username}')


# команда поддержать проект
@dp.message_handler(commands="link")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer('Хочешь больше встреч? Подпишись', reply_markup=get_keyboard_link(user_id))


# Генерация клавиатуры ОТМЕНА
def get_keyboard_cancel(id):
    buttons = [
        types.InlineKeyboardButton(text="Отменить", callback_data=f"num_cancel_{id}")
    ]
    keyboard_cancel = types.InlineKeyboardMarkup(row_width=1)
    keyboard_cancel.add(*buttons)
    return keyboard_cancel


# команда написать в поддержку
@dp.message_handler(commands="help")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    idict = {'status': 'help', 'ei': user_id}
    lib.Query.addRecordByQuery('u_status', idict)
    await message.answer('Можно написать свой вопрос, а я передам его в тех поддержку, после чего перешлю ответ',
                         reply_markup=get_keyboard_cancel(user_id))


# функция добавления интересов
@dp.message_handler(commands="fl")
async def fl(message: types.Message):
    await message.delete()
    await message.answer('Выбери три своих интереса',
                         reply_markup=get_keyboard_friends_leisure(int(message.from_user.id)))


# функция редактирования города
@dp.message_handler(commands="edit_sity")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer('В каком городе ты находишься большую часть времени? ',
                         reply_markup=get_keyboard_sity(user_id, 'e'))


# функция редактирования языков
@dp.message_handler(commands="edit_lang")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer('Сейчас у тебя выбраны следующие языки. Можешь какой то убрать или добавить ',
                         reply_markup=get_keyboard_lang(user_id, 'e'))


# функция редактирования даты рождения
@dp.message_handler(commands="edit_bday")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer('Готов помочь поменять твою дату рождения. Какого ты года?',
                         reply_markup=get_keyboard_year(user_id, 'e'))


# функция редактирования увлечений
@dp.message_handler(commands="edit_fl")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer(
        'Сейчас у тебя выбраны следующие увлечения. Максимум может быть 3, поэтому прежде чем что то добавить нужно что то убрать',
        reply_markup=get_keyboard_friends_leisure(user_id, 'fl', 'e'))


# функция редактирования увлечений2
@dp.message_handler(commands="edit_flp")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer(
        'Сейчас у тебя выбраны следующие увлечения. Максимум может быть 3, поэтому прежде чем что то добавить нужно что то убрать',
        reply_markup=get_keyboard_friends_leisure_plus(user_id, 'e'))


# функция редактирования фактов
@dp.message_handler(commands="edit_fact")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer('Хорошо, добавь пару слов о работе')
    idict = {'status': 'free_time', 'ei': user_id}
    lib.Query.addRecordByQuery('u_status', idict)


# функция редактирования чем ты сейчас занимаешься
@dp.message_handler(commands="edit_deal")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer('Можешь выбрать один актуальный род занятий', reply_markup=get_keyboard_business(user_id, 'e'))


# функция редактирования выбери три сферы деятельности
@dp.message_handler(commands="edit_sector")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer(
        'Сейчас у тебя выбраны следующие сферы. Максимум может быть 3, поэтому прежде чем что то выбрать нужно первое убрать',
        reply_markup=get_keyboard_business_sector(user_id, 'sect', 'e'))


# функция редактирования фактов
@dp.message_handler(commands="edit_deal_fact")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer('Хорошо, расскажи пару слов о том, чем гордишься')
    idict = {'status': 'editdeal', 'ei': user_id}
    lib.Query.addRecordByQuery('u_status', idict)


# функция редактирования цели контактов
@dp.message_handler(commands="edit_contact")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer(
        'Сейчас у тебя выбраны следующие цели контаков. Максимум может быть 2, поэтому прежде чем что то выбрать нужно что-то убрать',
        reply_markup=get_keyboard_business_contact(user_id, 'e'))


# функция редактирования выбери три сферы с какой бы хотел связать свою деятельность
@dp.message_handler(commands="edit_sector2")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer(
        'Сейчас у тебя выбраны следующие сферы. Максимум может быть 3, поэтому прежде чем что то выбрать нужно первое убрать',
        reply_markup=get_keyboard_business_sector(user_id, 'sect2', 'e'))


# функция редактирования выбора увлечения в свободное время
@dp.message_handler(commands="edit_bl")
async def fl(message: types.Message):
    await message.delete()
    user_id = int(message.from_user.id)
    await message.answer(
        'Сейчас у тебя выбраны следующие увлечения. Максимум может быть 3, поэтому прежде чем что то выбрать нужно что-то убрать',
        reply_markup=get_keyboard_friends_leisure(user_id, 'bl', 'e'))


async def tempo(id):
    print(id)


# @dp.message_handler(commands="match_business")
async def match_business(usertemp=None):
    ############


async def match_friends(usertemp=None):
    ############


# Генерация тестовой клавиатуры
def get_keyboard_test(id):
    buttons = [
        types.InlineKeyboardButton(text="Написать собеседнику", url=f"tg://user?id={id}")
    ]
    keyboard_fin = types.InlineKeyboardMarkup(row_width=1)
    keyboard_fin.add(*buttons)
    return keyboard_fin


# Генерация клавиатуры в среду
def get_keyboard_wednesday(id):
    buttons = [
        types.InlineKeyboardButton(text="Да", callback_data=f"num_wed_1_{id}"),
        types.InlineKeyboardButton(text="Нет", callback_data=f"num_wed_0_{id}")
    ]
    keyboard_wednesday = types.InlineKeyboardMarkup(row_width=2)
    keyboard_wednesday.add(*buttons)
    return keyboard_wednesday


async def saturday():
    u_f = lib.Query.getRecordsByQuery('u', f'ei != 0')  # забирает всех пользователей
    u = pd.DataFrame(u_f)
    idx = u[pd.to_numeric(u["meet"], errors="coerce") == 1].index
    for el in idx:
        try:
            await bot.send_message(int(u.at[el, "ei"]), f'Удалось договориться о встрече?',
                                   reply_markup=get_keyboard_saturday())
        except:
            await bot.send_message(log_group,
                                   f'{datetime.datetime.now()} : \n[error] при отправке сообщения пользователю {int(u.at[el, "ei"])}')
    idict = {'meet': 0, 'week': 0}
    lib.Query.updateRecordByQuery('u', idict, f'friends = 1')
    lib.Query.updateRecordByQuery('u', idict, f'business = 1')


async def no_limit():
    await asyncio.sleep(1)


async def wednesday():
    #############


# функция получения ID
@dp.message_handler(commands="id")
async def id(message: types.Message):
    await message.answer(f'You\'r id: {message.chat.id}', reply_markup=types.ReplyKeyboardRemove())
    await message.bot.send_message(log_group,
                                   f'{datetime.datetime.now()} : \n[info] пользователь @{message.from_user.username} использовал id')


# тестовая функция
@dp.message_handler(commands="test")
async def test(message: types.Message):
    await message.bot.send_message(log_group,
                                   f'{datetime.datetime.now()} : \n[info] пользователь @{message.from_user.username} использовал команду test')


# функция добавления чата поддержки
@dp.message_handler(commands="chat_support")
async def chat_support(message: types.Message):
    chat_id = message.chat.id
    tempo = int(lib.Query.checkCountByQuery('c', f'name = "chat_support"'))
    print(tempo)
    if tempo == 0:
        idict = {'name': 'chat_support', 'chat_id': chat_id}
        lib.Query.addRecordByQuery('c', idict)
        await message.answer(f'Успешно добавил чат поддержки')
    else:
        idict = {'name': 'chat_support', 'chat_id': chat_id}
        lib.Query.updateRecordByQuery('c', idict, f'name = "chat_support"')
        await message.answer(f'Успешно обновил чат поддержки')


# ниже пул тестовых команд, чтобы ускорить процессы или для ручного запуска
@dp.message_handler(commands="lm_wednesday")
async def lm_wednesday(message: types.Message):
    try:
        await wednesday()
        await bot.send_message(log_group,
                               f'{datetime.datetime.now()} : \n[info] успешно опросил пользователей по СРЕДЕ')
        await message.bot.send_message(log_group,
                                       f'{datetime.datetime.now()} : \n[info] пользователь @{message.from_user.username} использовал команду lm_wednesday')
    except:
        await bot.send_message(log_group,
                               f'{datetime.datetime.now()} : \n[error] ошибка при опросе пользователей по среде')


@dp.message_handler(commands="lm_test_b")
async def lm_test_b(message: types.Message):
    try:
        await match_business()
        await bot.send_message(log_group,
                               f'{datetime.datetime.now()} : \n[info] успешно смэтчил всех пользоватлей по бизнесу в ЧЕТВЕРГ')
        await message.bot.send_message(log_group,
                                       f'{datetime.datetime.now()} : \n[info] пользователь @{message.from_user.username} использовал команду lm_test_b')
    except:
        await bot.send_message(log_group,
                               f'{datetime.datetime.now()} : \n[error] ошибка при мэтчинге всех пользоватлей по бизнесу в ЧЕТВЕРГ')


@dp.message_handler(commands="lm_test_f")
async def lm_test_f(message: types.Message):
    try:
        await match_friends()
        await bot.send_message(log_group,
                               f'{datetime.datetime.now()} : \n[info] успешно смэтчил всех пользоватлей по дружбе в ЧЕТВЕРГ')
        await message.bot.send_message(log_group,
                                       f'{datetime.datetime.now()} : \n[info] пользователь @{message.from_user.username} использовал команду lm_test_f')
    except:
        await bot.send_message(log_group,
                               f'{datetime.datetime.now()} : \n[error] ошибка при мэтчинге всех пользоватлей по дружбе в ЧЕТВЕРГ')


@dp.message_handler(commands="lm_saturday")
async def lm_saturday(message: types.Message):
    try:
        await saturday()
        await bot.send_message(log_group, f'{datetime.datetime.now()} : \n[info] успешно опросил в СУББОТУ')
        await message.bot.send_message(log_group,
                                       f'{datetime.datetime.now()} : \n[info] пользователь @{message.from_user.username} использовал команду lm_saturday')
    except:
        await bot.send_message(log_group, f'{datetime.datetime.now()} : \n[error] ошибка при опросе в СУББОТУ')



@dp.message_handler()
async def test(message: types.Message):
    user_id = int(message.from_user.id)
    global c
    status = lib.Query.getFieldByQuery('u_status', f'ei = {user_id}', 'status')
    if status == 'name':
        idict = {'first_name': message.text}
        lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
        lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
        await message.answer(f'Рад знакомству, {message.text}! Выбери свой пол',
                             reply_markup=get_keyboard_gender(user_id))
    elif status == 'else':
        pass

    elif status == "sendEveryone":
        ids = lib.Query.runAnyQuery(f'SELECT ei FROM `u`', 'select', s_mode='all')
        ids = [el for el, _ in groupby(ids)]
        ids.remove({'ei': user_id})
        for i in ids:
            await bot.send_message(i['ei'], message.text)
        await bot.send_message(user_id, 'Сообщение успешно отправлено')

    elif status == "sendFriends":
        ids = lib.Query.runAnyQuery(f'SELECT ei FROM `u_`', 'select', s_mode='all')
        ids = [el for el, _ in groupby(ids)]
        ids.remove({'ei': user_id})
        for i in ids:
            await bot.send_message(i['ei'], message.text)
        await bot.send_message(user_id, 'Сообщение успешно отправлено')

    elif status == "sendBusiness":
        ids = lib.Query.runAnyQuery(f'SELECT ei FROM `u_business`', 'select', s_mode='all')
        ids = [el for el, _ in groupby(ids)]
        ids.remove({'ei': user_id})
        for i in ids:
            await bot.send_message(i['ei'], message.text)
        await bot.send_message(user_id, 'Сообщение успешно отправлено')

    elif status == 'help':
        block = lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'blocked')
        if str(message).find("private") != -1:
            try:
                if int(block) == 0:
                    try:
                        await bot.send_message(str(c.at[0, 'chat_id']), message.text,
                                               reply_markup=get_keyboard_ban(int(message.from_user.id)))
                        await message.answer('Твой вопрос был успешно доставлен, просьба ожидать ответа')
                        lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
                    except:
                        await message.answer(
                            '[error] Мама мия!😰 Что-то пошло не так. Но я уже сообщил разработчику об ошибке, скоро всё уладим.')
                else:
                    await bot.delete_message(message.chat.id, message.message_id)
                    await message.answer(
                        '[error] Не так быстро! Я вас заблокировал. Если вы сами этого добились, может быть стоит оставить всё как есть? Но если вы считаете, что это была моя ошибка, пожалуйста, сообщите @iplakunov.')
                    await message.bot.send_message(log_group,
                                                   f'{datetime.datetime.now()} : \n[info] пользователь попытался '
                                                   f'отправить вопрос, но он заблокирован',
                                                   reply_markup=get_keyboard_unban(int(message.from_user.id)))
            except:
                await bot.send_message(log_group, f'{datetime.datetime.now()} : \nОШИБКА.при пересылке сообщения в чат')
    elif status == 'sity':
        idict = {'sity': message.text}
        lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
        lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
        await message.answer(f'Запомнил! Со временем смогу подобрать ребят на офлайн встречу и из "{message.text}" :)' \
                             f'\nНа каких языках тебе будет удобно общаться на встречах? Выбери все подходящие варианты',
                             reply_markup=get_keyboard_lang(user_id, 'r'))
    elif status == 'sityedit':
        idict = {'sity': message.text}
        lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
        # lib.Query.runAnyQuery(f"DELETE FROM u_status WHERE ei = {user_id}", "delete")
        lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
        if (int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'business')) == 1) and (
                int(lib.Query.getFieldByQuery('u', f'ei = {user_id}', 'friends')) == 0):
            await finall(user_id)
        else:
            await finall_f(user_id)
        # await finall_f(user_id)
    elif status == 'deal':
        if len(message.text) > 59:
            idict = {'deal': message.text}
            lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
            lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
            await message.answer(
                f'Хорошо. Какого рода деловые контакты тебе интересно получать? Отметь 2 наиболее подходящих варианта',
                reply_markup=get_keyboard_business_contact(user_id, 'r'))
        else:
            await message.answer(
                f'Прости, но нужно написать более развёрнуто, хотя бы пару предложений (от 60 символов)')
    elif status == 'deal_match':
        if len(message.text) > 59:
            idict = {'deal': message.text}
            lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
            lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
            await message.answer(
                f'Хорошо. Какого рода деловые контакты тебе интересно получать? Отметь 2 наиболее подходящих варианта',
                reply_markup=get_keyboard_business_contact(user_id, 'm'))
        else:
            await message.answer(
                f'Прости, но нужно написать более развёрнуто, хотя бы пару предложений (от 60 символов)')
    elif status == 'editdeal':
        if len(message.text) > 59:
            idict = {'deal': message.text}
            lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
            lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
            await message.answer(f'Запомнил! Посмотри, как будет выглядеть твой профиль для будущих друзей.')
            asyncio.sleep(5)
            await finall(user_id)
        else:
            await message.answer(
                f'Прости, но нужно написать более развёрнуто, хотя бы пару предложений (от 60 символов)')
    elif status == 'free_time':
        if len(message.text) > 59:

            idict = {'free_time': message.text, 'friends': 1, 'week': 1}
            lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
            lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
            idict1 = {'ei': user_id}
            lib.Query.addRecordByQuery('u_fee', idict1)
            await message.answer(f"Посмотри, как будет выглядеть твой профиль для будущих друзей.")
            asyncio.sleep(5)
            await finall_f(user_id)
        else:
            await message.answer(
                f'Прости, но нужно написать более развёрнуто, хотя бы пару предложений (от 60 символов)')
    elif status == 'free_time_match':
        if len(message.text) > 59:
            idict = {'free_time': message.text}
            lib.Query.updateRecordByQuery('u', idict, f'ei = {user_id}')
            lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
            try:
                await bot.set_my_commands(
                    commands=[
                        types.BotCommand('link', 'Поддержать проект'),
                        types.BotCommand('help', 'Написать в поддержку'),
                        types.BotCommand('edit_fl', 'Изменить в анкете друзья то, что нравится больше всего'),
                        types.BotCommand('edit_flp', 'Изменить в анкете друзья чем люблю заниматься'),
                        types.BotCommand('edit_fact', 'Изменить в анкете друзья факты о работе'),
                        types.BotCommand('edit_deal', 'Изменить в анкете бизнес вид своей деятельности'),
                        types.BotCommand('edit_sector', 'Изменить в анкете бизнес сферы деятельности'),
                        types.BotCommand('edit_deal_fact', 'Изменить в анкете бизнес свои достижения в работе'),
                        types.BotCommand('edit_contact', 'Изменить в анкете бизнес цель контактов'),
                        types.BotCommand('edit_sector2',
                                         'Изменить в анкете бизнес сферы, с которыми хочешь связать работу/бизнес'),
                        types.BotCommand('edit_bl', 'Изменить в анкете бизнес увлечения в свободное время')
                    ],
                    scope=types.BotCommandScopeChat(chat_id=message.from_user.id)
                )
            except:
                await bot.send_message(log_group,
                                       f'{datetime.datetime.now()} : \nОШИБКА.start.при отправке меню пользователю')
            await message.answer(f"Отлично! Сейчас найду тебе пару")
            await match_friends(user_id)
        else:
            await message.answer(
                f'Прости, но нужно написать более развёрнуто, хотя бы пару предложений (от 60 символов)')
    elif status == 'email':
        email_t = message.text
        user_t = lib.Query.getRecordByQuery('u', f'ei = {user_id}')
        lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
        await message.answer(
            f"Отлично! Дождись четверга, и я подберу тебе пару для общения. Как только получишь сообщение, напиши первым и договорись о встрече или видеочате.\n" \
            f"Всегда на связи, Let's meet бот, твой проводник к качественному окружению.\n\nПодписывайся на наш канал:\nhttps://t.me/+bztYAcGH3DcyNzli")
        await bot.send_message(str(c.at[0, 'chat_id']),
                               f"[info] НОВАЯ заявка на подписку:\n\nИмя: {user_t['first_name']}\nEmail/телефон: {email_t}" \
                               f"\n\nПросьба подтвердить или отклонить",
                               reply_markup=get_keyboard_fee_accept('r', user_id, email_t))
    
    elif status == 'email1':
        idict = {'ei': user_id, 'email': message.text, 'fee': 1}
        lib.Query.addRecordByQuery('u_fee', idict)
        # lib.Query.updateRecordByQuery('u_fee', idict, f'ei = {user_id}')
        lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
        await message.answer(
            f"Отлично! Сейчас отправил запрос на подтверждение, после его одобрения смогу подобрать тебе пару")  # ------------------------------------------------------------------------------------------------------------------ ALARM LIST
        await bot.send_message(str(c.at[0, 'chat_id']),
                               f"[info] НОВАЯ заявка на подписку:\n\nИмя: {user_t['first_name']}\nEmail: {email_t}" \
                               f"\n\nПросьба подтвердить или отклонить",
                               reply_markup=get_keyboard_fee_accept('m', user_id, email_t))
    elif status == 'feedback':
        lib.Query.deleteRecordByQuery('u_status', f'ei = {user_id};')
        u_f = lib.Query.getRecordsByQuery('u', f'ei != 0')  # забирает всех пользователей
        u = pd.DataFrame(u_f)
        idx = u[pd.to_numeric(u["ei"], errors="coerce") == user_id].index
        for el in idx:
            if int(u.at[el, "friends"]) == 1:
                u_match = lib.Query.getRecordsByQuery('my_match',
                                                      f'ei != 0')  # забирает всех пользователей из матчей друзей
                tery = 'my_match'
            elif int(u.at[el, "business"]) == 1:
                u_match = lib.Query.getRecordsByQuery('my_match_b',
                                                      f'ei != 0')  # забирает всех пользователей из матчей бизнес
                tery = 'my_match_b'
            t_match = pd.DataFrame(u_match)
            idx1 = t_match[pd.to_numeric(t_match["ei"], errors="coerce") == user_id].index
            idx2 = t_match[pd.to_numeric(t_match["ei2"], errors="coerce") == user_id].index
            if idx1.to_list():
                for el1 in idx1.to_list():
                    # t_match.at[el, 'score1'] = act
                    idict = {'feedback1': message.text}
                    lib.Query.updateRecordByQuery(f'{tery}', idict, f'ei = {user_id}')
            if idx2.to_list():
                for el2 in idx2.to_list():
                    idict = {'feedback2': message.text}
                    lib.Query.updateRecordByQuery(f'{tery}', idict, f'ei2 = {user_id}')
        await message.answer(f"Хочешь еще встречу?", reply_markup=get_keyboard_want(user_id))
    else:
        if str(message).find("reply_to_message") != -1 and str(message).find("private") == -1:
            tem = str(message).split('*')
            await bot.send_message(tem[1],
                                   f'Надеюсь, ответ не заставил себя долго ждать! Скорее смотри, что написала тебе тех.поддержка:\n{message.text}')
            await message.answer('[info] Успешно отправил ответ пользователю')
        else:
            await message.delete()
            await message.answer(f'Ничего не понял, просьба использовать меню для работы со мной')


async def on_startup(x):
    await bot.send_message(log_group, f'{datetime.datetime.now()} : \n[info] бот успешно запущен')
    if int(datetime.datetime.weekday(datetime.datetime.today())) == 3:
        if int((datetime.datetime.now()).strftime('%H')) == 9:
            try:
                await match_business()
                await bot.send_message(log_group, f"{datetime.datetime.now()} : \n[info] успешно смэтчил по бизнесу")
            except:
                await bot.send_message(log_group, f"{datetime.datetime.now()} : \nОШИБКА.вызов def match_business")
            try:
                await match_friends()
                await bot.send_message(log_group, f"{datetime.datetime.now()} : \n[info] успешно смэтчил по дружбе")
            except:
                await bot.send_message(log_group, f"{datetime.datetime.now()} : \nОШИБКА.вызов def match_friends")
    elif int(datetime.datetime.weekday(datetime.datetime.today())) == 2:
        if int((datetime.datetime.now()).strftime('%H')) == 9:
            try:
                await wednesday()
                await bot.send_message(log_group, f"{datetime.datetime.now()} : \n[info] успешно опросил в среду")
            except:
                await bot.send_message(log_group, f"{datetime.datetime.now()} : \nОШИБКА.вызов def wednesday")
    elif int(datetime.datetime.weekday(datetime.datetime.today())) == 5:
        if int((datetime.datetime.now()).strftime('%H')) == 9:
            try:
                await saturday()
                await bot.send_message(log_group, f"{datetime.datetime.now()} : \n[info] успешно опросил в субботу")
            except:
                await bot.send_message(log_group, f"{datetime.datetime.now()} : \nОШИБКА.вызов def saturday")


# запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False,
                           on_startup=on_startup)  # skip_updates - пропускать ли обновления, которые были офлайн
