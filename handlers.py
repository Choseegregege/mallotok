import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from config import TOKEN
from states import CatalogState
from catalog_data import catalog
from aiogram import types



logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())



# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Каталог", callback_data="catalog"))
    markup.add(InlineKeyboardButton("О нас", callback_data="about"))
    markup.add(InlineKeyboardButton("Контакты", callback_data="contacts"))
    await bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    
    # Обработчик кнопки "Вернуться в меню"
@dp.callback_query_handler(lambda c: c.data == 'menu', state="*")
async def process_menu(callback_query: types.CallbackQuery, state: FSMContext):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Каталог", callback_data="catalog"))
    markup.add(InlineKeyboardButton("О нас", callback_data="about"))
    markup.add(InlineKeyboardButton("Контакты", callback_data="contacts"))
    await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=markup)
    await state.finish()


# Обработчик кнопки "О нас"
@dp.callback_query_handler(lambda c: c.data == 'about', state="*")
async def process_about(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "О нас: Mallotook - это компания, специализирующаяся на продаже и обслуживании профессионального инструмента и оборудования. Мы предлагаем широкий ассортимент качественных товаров от ведущих производителей, а также обеспечиваем высокий уровень сервиса и поддержки. Наша цель - предоставить покупателям надежные инструменты, которые помогут сделать их работу проще и эффективнее.")

# Обработчик кнопки "Контакты"
@dp.callback_query_handler(lambda c: c.data == 'contacts', state="*")
async def process_contacts(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Наши контакты:\n\nТелефон: +7 (776) 830-98-99\nEmail: Mallotook@mail.com")

# Обработчик для выбора категории товара
@dp.callback_query_handler(lambda c: c.data == 'catalog', state="*")
async def process_catalog_start(callback_query: types.CallbackQuery, state: FSMContext):
    markup = InlineKeyboardMarkup()
    for category in catalog.keys():
        markup.add(InlineKeyboardButton(category, callback_data=f"category:{category}"))
    markup.add(InlineKeyboardButton("Вернуться в меню", callback_data="menu"))
    await bot.send_message(callback_query.from_user.id, "Выберите категорию товара:", reply_markup=markup)
    await CatalogState.category.set()

# Обработчик для выбора бренда товара
@dp.callback_query_handler(lambda c: c.data.startswith('category:'), state=CatalogState.category)
async def process_category(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data.split(':')[1]
    await state.update_data(category=category)

    markup = InlineKeyboardMarkup()
    for brand in catalog[category].keys():
        markup.add(InlineKeyboardButton(brand, callback_data=f"brand:{brand}"))
    markup.add(InlineKeyboardButton("Вернуться в меню", callback_data="menu"))

    await bot.send_message(callback_query.from_user.id, f"Выберите бренд для категории {category}:", reply_markup=markup)
    await CatalogState.brand.set()

# Обработчик для выбора товара
@dp.callback_query_handler(lambda c: c.data.startswith('brand:'), state=CatalogState.brand)
async def process_brand(callback_query: types.CallbackQuery, state: FSMContext):
    brand = callback_query.data.split(':')[1]
    data = await state.get_data()
    category = data['category']
    await state.update_data(brand=brand)

    markup = InlineKeyboardMarkup()
    for item in catalog[category][brand]:
        markup.add(InlineKeyboardButton(item['name'], callback_data=f"item:{item['name']}"))
    markup.add(InlineKeyboardButton("Вернуться в меню", callback_data="menu"))

    await bot.send_message(callback_query.from_user.id, f"Выберите товар для бренда {brand}:", reply_markup=markup)
    await CatalogState.item.set()

@dp.callback_query_handler(lambda c: c.data.startswith('item:'), state=CatalogState.item)
async def process_item(callback_query: types.CallbackQuery, state: FSMContext):
    item_name = callback_query.data.split(':')[1]
    await state.update_data(item=item_name)

    data = await state.get_data()
    category = data['category']
    brand = data['brand']
    item = None
    for i in catalog[category][brand]:
        if i['name'] == item_name:
            item = i
            break

    if not item:
        await bot.send_message(callback_query.from_user.id, "Товар не найден. Пожалуйста, попробуйте еще раз.")
        return

    await bot.send_photo(chat_id=callback_query.from_user.id, photo=item['photo'], caption=f"{item['name']}\n\n{item['description']}\n\nЦена: {item['price']} {item['currency']}")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Вернуться в меню", callback_data="menu"))


    item_info = f"{item['name']}:\n\n{item['description']}\n\nЦена: {item['price']} {item['currency']}\n\nВыберите количество:"
    for i in range(1, 6):
        markup.add(InlineKeyboardButton(str(i), callback_data=f"quantity:{i}"))
    await bot.send_message(callback_query.from_user.id, item_info, reply_markup=markup)
    await CatalogState.quantity.set()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Вернуться в меню", callback_data="menu"))
    # Обработчик для подтверждения заказа
@dp.callback_query_handler(lambda c: c.data.startswith('quantity:'), state=CatalogState.quantity)
async def process_quantity(callback_query: types.CallbackQuery, state: FSMContext):
    quantity = int(callback_query.data.split(':')[1])
    data = await state.get_data()
    category = data['category']
    brand = data['brand']
    item_name = data['item']

    item = None
    for i in catalog[category][brand]:
        if i['name'] == item_name:
            item = i
            break

    if not item:
        await bot.send_message(callback_query.from_user.id, "Товар не найден. Пожалуйста, попробуйте еще раз.")
        return

    total_price = item['price'] * quantity
    whatsapp_link = "https://wa.me/+77768309899"
    order_info = f"Ваш заказ:\n\n{item['name']} x {quantity}\n\nИтого: {total_price} {item['currency']}\n\nДля оформления заказа, пожалуйста, свяжитесь с нами по [телефону]({whatsapp_link}) +7 (776) 830-98-99 или по email info@example.com."
    await bot.send_message(callback_query.from_user.id, order_info, parse_mode="Markdown")
    
    

    # Завершение состояния
    await state.finish()


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)