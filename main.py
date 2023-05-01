import asyncio
import pandas as pd
import numpy as np
import time
import datetime
import os
import aiogram
from aiogram import Bot, Dispatcher, types, filters, executor
from config import TOKEN
from asyncio import sleep
import matplotlib.pyplot as plt
import tracemalloc
from portfel import Portfel
import random, asyncio

import STICKER_PACK as SP

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

stock_dict = {}

# Set up aiogram
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot = bot, storage = storage)

users_username = {} #словарь ников пользователей
users_balance = {} #словарь для баланса пользователя
users_level = {} #словарь для уровня пользователей
users_bet_state = {} #словарь для ставки
slots_bet = {} #словарь для ставок каждого отдельного пользователя
# класс состояний пользователя
class UserState(StatesGroup):
    waiting_for_bet = State()
    waiting_for_bet_slots = State()
    waiting_for_slot = State()
    waiting_for_edit = State()
    waiting_for_buy = State()
    waiting_for_sell = State()

# Set up simulation parameters
os.chdir(r'F:\python_vsCode\fin_bot')
price_one = 100
price_two = 100
price_three = 100

timka_id = -1001853288680 #440487792
chatik_id = -955163522

jackpot = 1_000

tes = 0
tes_q = 0
sber4days = 0
yndx4days = 0
tsla4days = 0

def high_change(l, s):
    return np.random.normal(loc=l, scale=s)

async def send_message():
    # отправляем первое сообщение с текущим временем
    now = datetime.datetime.now().strftime('%H:%M:%S')
    message = f"Сейчас {now}"
    msg = await bot.send_message(chat_id=message.chat.id, text=message)
    while True:
        # обновляем текст сообщения с новым временем
        now = datetime.datetime.now().strftime('%H:%M:%S')
        message = f"Сейчас {now}"
        await bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=message)
        await asyncio.sleep(2)  # 5 минут

# Define task to simulate stock prices and save to CSV
async def simulate_stock_prices():
    global stock_data, price_one, price_two, price_three, tes, sber4days, yndx4days, tsla4days, tes_q
    stock_data = pd.DataFrame(columns=['date', 'SBER', 'YNDX','TSLA'])
    pd.set_option('display.float_format', lambda x: '{:.5f}'.format(x))

    counter = 0
    tick = 1
    q = 90
    while True:
        tracemalloc.start()

        if counter == 360:
            # tes = np.random.choice(a = [-15,-10,-6,-2,2,6,10,15], p = [2,3,8,12,15,41,15,4])
            tes = np.random.normal(loc = 6, scale = 5)
            tes_q = tes ** (1 / 4)

        if q == 90:
            sber4days = np.random.normal(loc = tes_q, scale = 0.1)
            yndx4days = np.random.normal(loc = tes_q, scale = 0.15)
            tsla4days = np.random.normal(loc = tes_q, scale = 0.2)

        price_change_SBER = round(np.random.normal(sber4days, 0.001) * 0.01, 3)
        price_change_YNDX = round(np.random.normal(yndx4days, 0.002) * 0.01, 3)
        price_change_TSLA = round(np.random.normal(tsla4days, 0.003) * 0.01, 3)

        price_SBER = round(price_one * (1 + price_change_SBER), 5)      
        price_YNDX = round(price_two * (1 + price_change_YNDX), 5) 
        price_TSLA = round(price_three * (1 + price_change_TSLA), 5) 

        new_row = pd.DataFrame({'date': tick, 'SBER': price_SBER, 'YNDX': price_YNDX, 'TSLA': price_TSLA}, index=[0])
        stock_data = pd.concat([stock_data, new_row]).reset_index(drop=True)

        price_one = price_SBER
        price_two = price_YNDX
        price_three = price_TSLA

        # Save the DataFrame to CSV
        stock_data.to_csv('stock_data.csv', index=False, sep='\t')
        await asyncio.sleep(0.1)
        counter += 1
        tick += 1
        # Отображение статистики
        current, peak = tracemalloc.get_traced_memory()
        print(f"Использовано {current / 10**6} МБ, пиковое значение {peak / 10**6} МБ | {tes}")
        tracemalloc.stop()
        
# Start the stock price simulation
loop = asyncio.get_event_loop()
task = loop.create_task(simulate_stock_prices())

# Define handler for the /start command
HELP_INFO ="""
В этом боте можно зарабатывать <b>нЕреАльныЙе</b> бапки 🤑💸💰
ПРОСТО отправь мне фотографии твоей <em>БанковСКОй КАрты</em> с двух старон!
спасибо 🥺\n
<b>/game</b> - начать играть
<b>/shop</b> - магазинчик
<b>/kazik</b> - угадай число от 0 до 9 (х3)
<b>/slots</b> - однорукий бандит
<b>/top</b> - топ игроков
<b>/balance</b> - баланс
<b>/grafik<b> - график

"""
url = 'https://cdn.fishki.net/upload/post/2018/01/02/2473934/1-015.jpg'

sticker = 'CAACAgIAAxkBAAEImvNkO-IjNFog5gFHs7CCOu4pX2KVkAACbCEAAtt0aUmFco3TMQyV2C8E'

def cb_inline_keyboard() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton('+1', callback_data = 'btn_increase'), InlineKeyboardButton('-1', callback_data = 'btn_decrease')],
    ])
    return ikb

async def reg(user_id, message):
    if user_id not in users_balance:
        users_balance[user_id] = 10_000
        users_level[user_id] = 1
        users_username[user_id] = message.from_user.username
    else:
        pass

async def delete_message(message: types.Message, delay: int):
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except Exception as ex:
        pass

#################################################################################
@dp.message_handler(commands = ['start', 'help'])
async def start_cmd(message: types.Message):
    first = await bot.send_photo(message.chat.id, url)
    second = await bot.send_sticker(message.chat.id, sticker)
    await bot.send_message(message.chat.id, HELP_INFO, parse_mode = 'HTML')
    await delete_message(first, 3)
    await delete_message(second, 1)
    await message.delete()

@dp.message_handler(commands = 'game')
async def game_command(message: types.Message):
    user_id = message.from_user.id
    await reg(user_id = user_id, message = message)

    await message.answer(f'Текущее количество денях = {users_balance[user_id]}', reply_markup = cb_inline_keyboard())
    await message.delete()

@dp.message_handler(Text(equals=["отмена","cancel", 'хватит'], ignore_case=True), state=UserState.states)
async def cancel(message: types.Message, state: FSMContext):
    # сбрасываем состояние пользователя
    await state.finish()
    # отправляем сообщение об отмене
    s = await message.answer("Действие отменено")
    # users_bet_state[message.from_user.id] = 0
    await asyncio.sleep(3)
    await message.delete()
    await delete_message(s,2)

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('btn'))
async def cb_counter(callback: types.CallbackQuery):
    ### НАДО СДЕЛАТЬ КАК С МАГАЗИНОМ, ЧТОБЫ ЗАКРЫВАЛОСЬ ПОСЛЕ НАЖАТИЯ, ЛИБО ЧТО_ТО ПРИДУМАТЬ
    user_id = callback.from_user.id
    
    if callback.data == 'btn_increase':
        users_balance[user_id] += 1 * users_level[user_id]
        await callback.answer('заработали баблишко')
        s = await callback.message.edit_text(f'Текущее количество денях = {users_balance[user_id]}', reply_markup = cb_inline_keyboard())
        await delete_message(callback.message, 30)
    elif callback.data == 'btn_decrease':
        users_balance[user_id] -= 1 * users_level[user_id]
        await callback.answer('заПЛОТили налоги')
        photo = await bot.send_photo(callback.message.chat.id,'https://i.pinimg.com/originals/b1/b4/53/b1b453f34bcfc6c9057bc8665f785686.jpg')
        s = await callback.message.edit_text(f'Текущее количество денях = {users_balance[user_id]}', reply_markup = cb_inline_keyboard())
        await delete_message(photo, 1)
        await delete_message(callback.message, 30)

def cb_keyboard_shop() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton('Улучшить кнопку', callback_data = 'upgrade')],
    ])
    return ikb

@dp.message_handler(commands = 'shop')
async def shop_cmd(message: types.Message):
    user_id = message.from_user.id
    await reg(user_id = user_id, message = message)
    await bot.send_message(message.chat.id, f'Вы всегда можете улучшить свой заработок, если есть деньги конечно 😅\n Текущий баланс: {users_balance[message.from_user.id]}\n Текущий уровень: {users_level[message.from_user.id]}',
                           reply_markup = cb_keyboard_shop())
    await message.delete()

@dp.callback_query_handler(text = 'upgrade')
async def shop_cb(callback: types.CallbackQuery):

    if users_balance[callback.from_user.id] < 10:
        await callback.answer('нема денех дружище, тебе надо поработать ещё')
        await callback.message.delete()
        s = await bot.send_message(callback.message.chat.id, f'Вы всегда можете улучшить свой заработок, если есть деньги конечно 😅\n Текущий баланс: {users_balance[callback.from_user.id]}\n Текущий уровень: {users_level[callback.from_user.id]}', reply_markup = cb_keyboard_shop())
        await delete_message(s, 5)
    else:
        users_level[callback.from_user.id] += 1
        users_balance[callback.from_user.id] -= 10
        await callback.answer('Уровень успешно повышен')
        await callback.message.delete()
        s = await bot.send_message(callback.message.chat.id, f'Вы всегда можете улучшить свой заработок, если есть деньги конечно 😅\n Текущий баланс: {users_balance[callback.from_user.id]}\n Текущий уровень: {users_level[callback.from_user.id]}', reply_markup = cb_keyboard_shop())
        await delete_message(s,5)

@dp.message_handler(commands = 'kazik')
async def kazik_cmd(message: types.Message):
    user_id = message.from_user.id
    users_bet_state[user_id] = True
    await reg(user_id = user_id, message = message)

    await UserState.waiting_for_bet.set()
    await bot.send_message(message.chat.id, f'Какую сумму поставить? \nТвой баланс: {users_balance[user_id]}\nПосле суммы через пробел укажи цифру от 0 до 9\nПример:\n100 7 \n\n* для выхода из игры напиши "отмена" в чатик')

@dp.message_handler(state=UserState.waiting_for_bet)
async def get_bet(message: types.Message, state: FSMContext):
    user_id = message.from_user.id


    try:
        # Преобразуем каждый элемент списка в целое число
        amount = [int(i) for i in message.text.split(' ')]
        # Проверяем, является ли каждый элемент списка целым числом
        if all(isinstance(i, int) for i in amount):
            # Если все элементы являются целыми числами, продолжаем выполнение кода
            pass
        else:
            # Если есть хотя бы один элемент, который не является целым числом, генерируем исключение
            raise ValueError()
    except ValueError:
        await bot.send_message(message.chat.id, 'Сумму и ставку указывайте цифрами (целыми)')
        return 'невалидное число'


    if amount[0] > users_balance[user_id]:
        await bot.send_message(message.chat.id, 'не хватает денях')
    elif amount[0] <= 0:
        await bot.send_message(message.chat.id, 'больше 0 число')
    else:
        await bot.send_message(message.chat.id, f'начинаем игру! \nВаша ставка {amount[0]} на {amount[1]}')
        await sleep(1)
        r = random.randint(0,9)
        await bot.send_message(message.chat.id, f'бот выкидывает {r}')
        if r == amount[1]:
            users_balance[user_id] += amount[0] * 3
            await bot.send_message(message.chat.id, f'поздравляю ваш выигыш составил: {amount[0] * 3} \nВаш баланс: {users_balance[user_id]} \n\n* для выхода из игры напиши "отмена" в чатик')
        else:
            users_balance[user_id] -= amount[0]
            await bot.send_message(message.chat.id, f'кажется вы проиграли(( \nВаш баланс: {users_balance[user_id]} \n\n* для выхода из игры напиши "отмена" в чатик')

    # конец        

@dp.message_handler(commands = 'top')
async def top_cmd(message: types.Message):
    user_id = message.from_user.id
    df = pd.DataFrame(list(zip(users_username.values(), users_balance.values(), users_level.values())), index=users_username.values(), columns=['username', 'balance', 'level'])
    await reg(user_id = user_id, message = message)
    # сохранение таблицы в HTML с выравниванием по центру
    html_table = df.style.set_properties(**{"text-align": "center"}).render()

    # создание изображения и сохранение его в файл
    fig, ax = plt.subplots(figsize=(8, 1))
    ax.axis("off")
    ax.axis("tight")
    ax.table(cellText=df.values, colLabels=df.columns, loc="center", cellLoc='center')
    plt.savefig("table.png")

    # отправка сообщения с таблицей в формате картинки
    with open("table.png", "rb") as photo:
        await message.answer_photo(photo)

@dp.message_handler(commands = ['balance'])
async def balance_cmd(message: types.Message):
    await message.answer(users_balance[message.from_user.id])

@dp.message_handler(commands = ['slots'])
async def slots_cmd(message: types.Message):
    user_id = message.from_user.id
    await reg(user_id = user_id, message = message)
    await message.answer(f'Бурмалда\n\nСначала сделай свою ставку, затем крути барабан\n\nБаланс: {users_balance[user_id]}')
    await UserState.waiting_for_bet_slots.set()
    await message.delete()


@dp.message_handler(state=UserState.waiting_for_bet_slots)
async def bet_for_slots(message: types.Message, state: FSMContext):
    user_bet = message.text

    try:
        user_bet = int(user_bet)
        if isinstance(user_bet, int) and user_bet > 0 and user_bet <= users_balance[message.from_user.id]:
            await state.finish()
            slots_bet[message.from_user.id] = user_bet
            await message.answer(f'Ваша ставка {user_bet}, крутите барабан\n\nБаланс{users_balance[message.from_user.id]}')
            await UserState.waiting_for_slot.set()
            pass
        else:
            if user_bet > users_balance[message.from_user.id]:
                await message.answer(f'кажется, у вас недостаточно денег\n\nБаланс: {users_balance[message.from_user.id]}')
            else:
                await message.reply(f'введите ставку (натуральное число)\n\nБаланс{users_balance[message.from_user.id]}')

    except Exception as ex:
        await message.reply(f'введите ставку (натуральное число)\n\nБаланс{users_balance[message.from_user.id]}')

    
@dp.message_handler(content_types=types.ContentType.DICE, state = UserState.waiting_for_slot)
async def slot_cmd(message: types.Message, state: FSMContext):
    global jackpot
    amount = slots_bet[message.from_user.id]
    msg_number = message.dice.value
    user_id = message.from_user.id
    if amount <= users_balance[user_id]:
        if msg_number in [1,22,43]:
            win_amount = amount * 20
            users_balance[user_id] += win_amount
            s = await message.answer(f'Выигрыш составил: {win_amount} \n\nТекущий баланс: {users_balance[user_id]}\n\nТекущий джекпот: {jackpot}')
            await asyncio.sleep(3)
            await message.delete()
            await delete_message(s, 1)
            
        elif msg_number == 64:
            win_amount = jackpot
            users_balance[user_id] += win_amount
            jackpot = 0
            j = await bot.send_sticker(message.chat.id, random.choice(SP.STICKER_ARTHAS_jackpot))
            s = await message.answer(f'Джекпот!!!\n\nВыигрыш составил: {win_amount} \n\nТекущий баланс: {users_balance[user_id]}\n\nТекущий джекпот: {jackpot}')
            await asyncio.sleep(3)
            await message.delete()
            await delete_message(j,2)
            await delete_message(s,1)
            
        else:
            jackpot += amount * 10
            users_balance[user_id] -= amount
            l = await bot.send_sticker(message.chat.id, random.choice(SP.STICKER_NO_MONEY))
            s = await message.answer(f'Неудача\n\nТекущий баланс: {users_balance[user_id]}\n\nТекущий джекпот: {jackpot}')
            await asyncio.sleep(3)
            await message.delete()
            await delete_message(l, 2)
            await delete_message(s, 1)
    else:
        s = await message.answer(f'необходимо больше золота!\n\nБалана: {users_balance[message.from_user.id]}')
        await delete_message(s, 2)



@dp.message_handler(commands = 'id')
async def id_id(message: types.Message):
    await message.answer(message.chat.id)
    user_portfel = {
        message.from_user.id : 0,
        'SBER' : 0,
        'YNDX' : 0,
        'TSLA' : 0
    }
# Define handler for all other commands
@dp.message_handler(commands = 'grafik')
async def default_handler(message: types.Message):   
    tracemalloc.start()
    # Считываем данные из CSV файла
    stock_data = pd.read_csv('stock_data.csv', sep='\t')
    n = message.text.split(' ')
    n = int(n[-1])
    stock_data = stock_data.tail(n)

    # Удаляем колонку даты, так как мы будем использовать ее для индексации
    dates = stock_data['date']
    stock_data.drop('date', axis=1, inplace=True)


    # Создаем график
    fig, ax = plt.subplots()
    ax.plot(dates, stock_data['SBER'],   label=f'ГлеБанк      |{stock_data.iloc[-1, 0]}')
    ax.plot(dates, stock_data['YNDX'], label=f'АрсБанк |{stock_data.iloc[-1, 1]}')
    ax.plot(dates, stock_data['TSLA'],  label=f'Тимкофф        |{stock_data.iloc[-1, 2]}')
    ax.set_xlabel('Дата')
    ax.set_ylabel('Цена акции')
    ax.set_title('График котировок акций')
    ax.legend()
    # Убираем отображение на оси X
    ax.set_xticks([])
    # Отображаем график
    plt.savefig('fig.png')
    photo = open('fig.png', 'rb') # здесь указываем путь к файлу фото
    await bot.send_photo(chat_id=message.chat.id, photo=types.InputFile(photo), caption='') # отправляем фото вместе с подписью
    photo.close()
    # Отображение статистики
    current, peak = tracemalloc.get_traced_memory()
    print(f"Использовано {current / 10**6} МБ, пиковое значение {peak / 10**6} МБ")
    tracemalloc.stop()

TICKERS_INFO = """
SBER - Сбербанк
YNDX - Яндекс
TSLA - Тесла
"""

@dp.message_handler(commands = 'tes')
async def buy_cmd(message: types.Message):
    await bot.send_message(message.chat.id, TICKERS_INFO)
    await bot.send_message(message.chat.id, '[-2; 2]')
    await UserState.waiting_for_edit.set()

@dp.message_handler(state=UserState.waiting_for_edit)
async def get_buy_info(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    global tes
    tes = int(message.text)
    await state.finish()

sber = Portfel("SBER")
yndx = Portfel("YNDX")
tsla = Portfel("TSLA")

def get_price(symbol):
    stock_data = pd.read_csv('stock_data.csv', sep='\t')
    price = stock_data[f'{symbol}'].values[-1]
    return price

stocks = {
    "SBER" : Portfel(symbol = "SBER"),
    "YNDX" : Portfel(symbol = "YNDX"),
    "TSLA" : Portfel(symbol = "TSLA")
}

@dp.message_handler(commands = 'buy')
async def buy_cmd(message: types.Message):
    user_id = message.from_user.id
    z = message.text.split(' ')
    q = int(z[2])
    stock_name = z[1].upper()
    p = get_price(stock_name)
    if users_balance[user_id] >= p * q:
        stocks[f"{stock_name}"].buy_share(user_id = user_id, quantity = q, price = p)
        stocks[f"{stock_name}"].get_info(user_id)
        users_balance[user_id] -= p * q
        await message.answer(f"Сделка успешно проведена!\n{q} акций компании {stock_name} было приобретено по цене {p}\nБаланс: {round(users_balance[user_id], 3)}")
    elif users_balance[user_id] < p * q:
        await message.answer('недостаточно денег')
    else:
        await message.answer('проверьте правильность ввода')

        
@dp.message_handler(commands = 'sell')
async def buy_cmd(message: types.Message):
    user_id = message.from_user.id
    z = message.text.split(' ')
    q = int(z[2])
    stock_name = z[1].upper()
    p = get_price(stock_name)
    if q <= sum(stocks[f"{stock_name}"].symbol[user_id]['quantity']):
        stocks[f"{stock_name}"].sell_share(user_id = user_id, quantity = q, price = p)
        users_balance[user_id] += p * q
        await message.answer(f"Сделка успешно проведена!\n{q} акций компании {stock_name} было продано по цене {p}\nБаланс: {round(users_balance[user_id], 3)}")
    else:
        await message.answer('недостаточно акций')


@dp.message_handler(commands = 'z')
async def lol_cmd(message: types.Message):
    user_id = message.from_user.id
    z = message.text.split(' ')
    q = int(z[2])
    stock_name = z[1].upper()
    p = get_price(stock_name)
    print(stocks[f"{stock_name}"].symbol[user_id]['quantity'])
    print(sum(stocks[f"{stock_name}"].symbol[user_id]['quantity']))




if __name__ == '__main__':
    # Start the aiogram bot
    executor.start_polling(dp, skip_updates=True)



#