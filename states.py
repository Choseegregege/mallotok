from aiogram.dispatcher.filters.state import State, StatesGroup

class CatalogState(StatesGroup):
    category = State()
    brand = State()
    item = State()
    Photo = State()
    quantity = State()