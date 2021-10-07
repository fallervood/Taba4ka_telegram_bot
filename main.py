# -*- coding: utf-8 -*-

import telebot
from telebot import types
import reader
import content
from content import Client
import datetime
import random

# Телега - @Fallervood , пишите по всем вопросам
programmer_id = '1587111554'

# Bot's API Token
bot = telebot.TeleBot('TOKEN')

user_dic = {}
user_page = {}
user_time = {}
carts = {}


def get_current_time() -> datetime:
	delta = datetime.timedelta(hours=3, minutes=0)
	return datetime.datetime.now(datetime.timezone.utc) + delta


def check_user(id):
	if reader.read_clients(id):
		user_dic[id] = reader.read_client_info(id)
		print("User add to active.")
		return True
	else:
		try:
			user = reader.read_client_info(id)
			if str(user.client_id) == str(id):
				print("Id was found. Add to user_dic..")
				user_dic[id] = user
			else:
				print("Id not found. Write in base..")
				new_user = Client(client_id=id, name=None, phone=None, location=None, time=None)
				user_dic[id] = new_user
				reader.write_client(user_dic[id])
		except Exception as exp:
			print("Error in check_user", exp)


@bot.message_handler(commands=['start', 'id'])
def get_commands(message):
	try:
		setting = content.settingsUpdate()
		if message.text == '/start':
			if int(setting['Режим']) == 0:
				bot.send_message(
					chat_id=message.chat.id,
					text=setting['ТекстРежимаНоль'])
			else:
				check_user(message.chat.id)
				bot.send_message(
					chat_id=message.chat.id,
					text='Выберите ближайшую к Вам локацию',
					reply_markup=keyboard_locations())
		elif message.text == '/id':
			bot.send_message(message.chat.id, f'Ваш id: {message.chat.id}')
	except Exception as exp:
		print("ERROR IN COMMANDS", exp)


@bot.message_handler(content_types=['text'])
def get_message(message):
	bot.send_message(message.chat.id, 'Я Вас не понимаю, попробуйте снова.')


def get_name(message):
	try:
		user_dic[message.chat.id].name = message.text
		msg = bot.send_message(chat_id=message.chat.id, text='Введите Ваш номер телефона')
		bot.register_next_step_handler(msg, get_phone)
	except Exception as exp:
		print("Error in get_name", exp)


def get_phone(message):
	try:
		user_dic[message.chat.id].phone = message.text
		bot.send_message(chat_id=message.chat.id,
		                 text=f'Ваши контакты:\n'
		                      f'{user_dic[message.chat.id].name}\n'
		                      f'{user_dic[message.chat.id].phone}',
		                 reply_markup=keyboard_confirm_contacts())
	except Exception as exp:
		print("Error in get_phone", exp)
		bot.send_message(message.chat.id, text="Ваша корзина пуста!", reply_markup=keyboard_locations())


@bot.callback_query_handler(func=lambda call: True)
def get_callback(call):
	try:
		if call.message.chat.id not in list(user_dic.keys()):
			check_user(call.message.chat.id)
	except Exception as exp:
		print("Error in check user (callback)", exp)

	try:
		settings = content.settingsUpdate()
		if int(settings['Режим']) == 0:
			bot.send_message(chat_id=call.message.chat.id, text=settings['ТекстРежимаНоль'])
	except Exception as exp:
		print("Error in settings update (callback)", exp)

	# --- Locations ---
	if 'loc_' in call.data:
		try:
			if len(call.data[4:]) > 0:
				print(user_dic)
				user_dic[call.message.chat.id].location = call.data[4:]
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text='Выберите товар',
					reply_markup=keyboard_brand())
			else:
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text='Выберите локацию',
					reply_markup=keyboard_locations())
		except Exception as exp:
			print("Error in locations", exp)

	# --- Brands ---
	elif 'brand_' in call.data:
		try:
			Brand = call.data[6:]
			if len(Brand) > 0:
				# Creating user's cart
				try:
					Cart = carts[call.message.chat.id]
					if len(Cart.brand) > 0:
						try:
							Taste = Cart.taste[Cart.brand.index(Cart.brand[-1])]
						except IndexError:
							Cart.brand.remove(Cart.brand[-1])
						finally:
							Cart.brand.append(Brand)
					else:
						Cart.brand.append(Brand)
				except KeyError:
					print('Created new cart')
					carts[call.message.chat.id] = content.Cart(user_id=call.message.chat.id,
					                                           brand=[Brand],
					                                           taste=[],
					                                           count=[],
					                                           cost=[])
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text='Выберите объем',
					reply_markup=keyboard_volume(Brand))
			else:
				try:
					if carts[call.message.chat.id].brand[-1] in reader.read_brands():
						carts[call.message.chat.id].brand.remove(carts[call.message.chat.id].brand[-1])
					bot.edit_message_text(
						chat_id=call.message.chat.id,
						message_id=call.message.id,
						text='Выберите товар',
						reply_markup=keyboard_brand())
				except KeyError:
					bot.edit_message_text(
						chat_id=call.message.chat.id,
						message_id=call.message.id,
						text='Выберите локацию',
						reply_markup=keyboard_locations())
		except Exception as exp:
			print("Error with brand", exp)

	# --- Volume ---
	elif 'volume_' in call.data:
		try:
			# Cart Update
			volume = call.data[7:]
			if len(volume) > 0:
				carts[call.message.chat.id].brand[-1] += (" " + volume)
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text='Выберите вкус',
					reply_markup=keyboard_taste(carts[call.message.chat.id].brand[-1]))
			else:
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text='Выберите объем',
					reply_markup=keyboard_volume(carts[call.message.chat.id].brand[-1]))
		except Exception as exp:
			print("Error with volume", exp)

	# --- Taste ---
	elif 'taste_' in call.data:
		try:
			Taste = call.data[6:]
			cart = carts[call.message.chat.id]
			add = True
			if len(cart.taste) != 0:
				print(cart.brand)
				for i in range(0, len(cart.taste)):
					if (cart.brand[-1] + ' ' + Taste) == (cart.brand[i] + ' ' + cart.taste[i]):
						add = False
						bot.answer_callback_query(
							callback_query_id=call.id, text="Этот продукт уже у Вас в корзине!", show_alert=True)
						break
			if add:
				cart.taste.append(Taste)
				cart.count.append(1)
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text=f'Выберите кол-во',
					reply_markup=keyboard_count(count=cart.count[-1]))
		except Exception as exp:
			print("Error with taste", exp)

	# --- Count ---
	elif call.data == 'count_plus':
		try:
			cart = carts[call.message.chat.id]
			Product = content.Product(cart.brand[-1], cart.taste[-1])
			if reader.check_product(product=Product) <= cart.count[-1]:
				bot.answer_callback_query(callback_query_id=call.id, text="Больше товара нет!", show_alert=True)
			else:
				cart.count[-1] += 1
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text=f'Выбрано кол-во: {cart.count[-1]}',
					reply_markup=keyboard_count(count=cart.count[-1]))
		except Exception as exp:
			print("Error with count_plus", exp)

	elif call.data == 'count_minus':
		try:
			cart = carts[call.message.chat.id]
			if cart.count[-1] > 1:
				cart.count[-1] -= 1
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text=f'Выбрано кол-во: {cart.count[-1]}',
					reply_markup=keyboard_count(count=cart.count[-1]))
			else:
				bot.answer_callback_query(callback_query_id=call.id, text="Меньше нельзя!", show_alert=True)
		except Exception as exp:
			print("Error with count_minus", exp)

	elif 'count_' in call.data:
		try:
			if carts[call.message.chat.id] is not None:
				cart = carts[call.message.chat.id]
				if len(call.data[6:]) > 0:
					cost = int(cart.count[-1]) * int(reader.read_cost(volume=cart.brand[-1]))
					cart.cost.append(str(cost))
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text=f'Корзина:',
					reply_markup=keyboard_choice(cart))
			else:
				bot.send_message(
					chat_id=call.message.chat.id,
	                text='Либо Ваша корзина пуста, либо потерялись данные. Пожалуйста, попробуйте снова.',
					reply_markup=keyboard_locations())
		except KeyError as error:
			print("No cart:", error)
			bot.answer_callback_query(callback_query_id=call.id,
			                          text="Ваша корзина пуста!",
			                          show_alert=True)
		except Exception as exp:
			print("Error in count_", exp)

	# --- Choice ---
	elif call.data == 'yes':
		try:
			user_page[call.message.chat.id] = 0
			bot.edit_message_text(
				chat_id=call.message.chat.id,
				message_id=call.message.id,
				text='Выберите время',
				reply_markup=keyboard_time())
		except Exception as exp:
			print("Error in Choice_yes", exp)

	elif call.data == 'no':
		try:
			bot.edit_message_text(
				chat_id=call.message.chat.id,
				message_id=call.message.id,
				text='Выберите товар',
				reply_markup=keyboard_brand())
		except Exception as exp:
			print("Error in Choice_no", exp)

	# --- Time ---
	elif call.data == 'time_next':
		try:
			settings = content.settingsUpdate()
			settings['ЧасСейчас'] = int(get_current_time().hour)
			if int(settings['МаксЧас']) <= user_page[call.message.chat.id] + int(settings['МинЧас']):
				bot.answer_callback_query(callback_query_id=call.id, text="Это максимальное время!", show_alert=True)
			elif int(settings['МаксЧас']) <= user_page[call.message.chat.id] + int(get_current_time().hour):
				bot.answer_callback_query(callback_query_id=call.id, text="Это максимальное время!", show_alert=True)
			else:
				user_page[call.message.chat.id] += 1
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text='Выберите время',
					reply_markup=keyboard_time(page=user_page[call.message.chat.id]))
		except Exception as exp:
			print("Error in time_next", exp)

	elif call.data == 'time_back':
		try:
			settings = content.settingsUpdate()
			if int(settings['МинЧас']) >= user_page[call.message.chat.id] + int(settings['МинЧас']):
				bot.answer_callback_query(callback_query_id=call.id, text="Это минимальное время!", show_alert=True)
			else:
				user_page[call.message.chat.id] -= 1
				bot.edit_message_text(
					chat_id=call.message.chat.id,
					message_id=call.message.id,
					text='Выберите время',
					reply_markup=keyboard_time(page=user_page[call.message.chat.id]))
		except Exception as exp:
			print("Error in time_back", exp)

	elif 'time_' in call.data:
		try:
			Time = call.data[5:]
			if int(get_current_time().minute) > int(Time[3:]) and int(Time[:2]) == int(get_current_time().hour):
				bot.answer_callback_query(callback_query_id=call.id,
				                          text="Невозможно выбрать это время!",
				                          show_alert=True)
			elif int(Time[3:]) - int(get_current_time().minute) < 6 and int(Time[:2]) == int(get_current_time().hour):
				bot.answer_callback_query(callback_query_id=call.id,
				                          text="Курьер не успеет доставить в это время!\nВремя доставки: 5 мин",
				                          show_alert=True)
			else:
				user_dic[call.message.chat.id].time = Time
				if user_dic[call.message.chat.id].name is not None and user_dic[call.message.chat.id].phone is not None:
					bot.send_message(chat_id=call.message.chat.id,
					                 text=f'Ваши контакты:\n'
					                      f'{user_dic[call.message.chat.id].name}\n'
					                      f'{user_dic[call.message.chat.id].phone}',
					                 reply_markup=keyboard_confirm_contacts())
				else:
					bot.send_message(
						chat_id=call.message.chat.id,
						text='Отправьте Ваши данные',
						reply_markup=keyboard_contacts())
		except Exception as exp:
			print("Error in time_", exp)

	# --- Contacts ---
	elif call.data == 'contact_yes':
		try:
			settings = content.settingsUpdate()
			# print(user_dic[call.message.chat.id].client_id)
			reader.write_client(user_dic[call.message.chat.id])
			if len(carts[call.message.chat.id].brand) > 0:
				text = make_paycheck(call.message.chat.id)
				bot.send_message(chat_id=call.message.chat.id, text=text)
				bot.send_message(chat_id=call.message.chat.id, text='Выберите локацию', reply_markup=keyboard_locations())
				bot.send_message(chat_id=settings['ПродавецId'], text=text)
				reader.delete_offer(carts[call.message.chat.id])
				user_page[call.message.chat.id] = None
				carts[call.message.chat.id] = content.Cart(user_id=call.message.chat.id,
				                                           brand=[],
				                                           taste=[],
				                                           count=[],
				                                           cost=[])
				for id in settings['АдминыId'][:-1].split(','):
					bot.send_message(chat_id=id, text=text)
			else:
				bot.send_message(call.message.chat.id, text="Ваша корзина пуста!", reply_markup=keyboard_locations())
		except Exception as exp:
			print("Error in contact_yes", exp)

	elif call.data == 'contact_no':
		try:
			msg = bot.send_message(chat_id=call.message.chat.id, text="Введите Ваше имя:")
			bot.register_next_step_handler(msg, get_name)
		except Exception as exp:
			print("Error in contact_no", exp)

	elif 'delete_' in call.data:
		try:
			index = int(call.data[7:])
			cart = carts[call.message.chat.id]
			cart.brand.pop(index)
			cart.taste.pop(index)
			cart.count.pop(index)
			cart.cost.pop(index)
			bot.edit_message_text(
				chat_id=call.message.chat.id,
				message_id=call.message.id,
				text=f'Корзина:',
				reply_markup=keyboard_choice(cart))
		except Exception as exp:
			print("Error in delete_", exp)

	else:
		bot.send_message(call.message.chat.id, 'В настоящий момент времени, эта функция недоступна.')


def make_paycheck(id):
	global carts, user_dic
	try:
		print(user_dic[id])
		print(user_dic[id].time)
		print(user_dic[id].location)
		settings = content.settingsUpdate()
		settings['ЧасСейчас'] = get_current_time().hour

		plus = 0
		if int(settings['ЧасСейчас']) > int(settings['МаксЧас']):
			plus = 1
		else:
			plus = 0

		if len(carts[id].brand) > 0:
			products = ' '
			for i in range(0, len(carts[id].brand)):
				products += "{:<15}{:>13}{:>10}\n{:<15}\n".format(carts[id].brand[i],
				                                                  carts[id].count[i],
				                                                  carts[id].cost[i],
				                                                  carts[id].taste[i])
			text = f'''
	Итоговый чек
Заказ №{settings['КолвоЗаказов']}{get_current_time().day + plus}{random.randint(1000, 9999)}
__________________________________
Название            Кол-во    Цена
{products}
__________________________________
🙍‍♂️ Покупатель: {user_dic[id].name}
📞 Телефон: {user_dic[id].phone}
__________________________________
👤 Продавец/Курьер: {settings['Продавец'][:-1]}
📞 Телефон: {settings['Телефон']}
📍 Локация: {user_dic[id].location}
🕙 Время: {get_current_time().date().replace(day=get_current_time().day + plus)} | {user_dic[id].time}
			'''
			return text
		else:
			bot.send_message(id, text="Ваша корзина пуста!", reply_markup=keyboard_locations())
	except Exception as exp:
		print("Error in make_paycheck", exp)
		bot.send_message(chat_id=id,
		                 text='Упс! Возможно ваша корзина пуста или что-то пошло не так.\nПопробуйте оформить снова '
		                      'через команду /start')


# Обработка контактов
@bot.message_handler(content_types=['contact'])
def get_contact_messsage(message):
	try:
		settings = content.settingsUpdate()
		if int(settings['Режим']) == 0:
			bot.send_message(chat_id=message.chat.id, text=settings['ТекстРежимаНоль'])
		elif message.contact is not None:
			try:
				user_dic[message.chat.id].name = message.contact.first_name
				user_dic[message.chat.id].phone = message.contact.phone_number
				bot.send_message(chat_id=message.chat.id,
				                 text=f'Ваши контакты:\n'
				                      f'{message.contact.first_name}\n'  # {message.contact.last_name}'
				                      f'{message.contact.phone_number}',
				                 reply_markup=keyboard_confirm_contacts())
			except Exception as exp:
				print(exp)
				if user_dic[message.chat.id].name is None or user_dic[message.chat.id].phone is None:
					msg = bot.send_message(
						chat_id=message.chat.id,
						text="У Вас есть незаполненные данные.\nВведите Ваше имя:"
					)
					bot.register_next_step_handler(msg, get_name)
	except Exception as exp:
		print("Error in get_contact_message", exp)


# Keyboards
def keyboard_locations():
	markup = types.InlineKeyboardMarkup()
	settings = content.settingsUpdate()
	for k in list(settings.keys()):
		if 'Локация' in k and settings[k][:-1] != '0':
			# print(settings[k])
			markup.add(
				types.InlineKeyboardButton(f"{settings[k]}", callback_data=f"loc_{settings[k]}"))
	return markup


def keyboard_brand():
	markup = types.InlineKeyboardMarkup()
	brands = reader.read_brands()
	for e in brands:
		markup.add(types.InlineKeyboardButton(f'{e}', callback_data=f'brand_{e}'))
	markup.add(types.InlineKeyboardButton(text='Корзина', callback_data=f'count_'),
	           types.InlineKeyboardButton(text='Назад', callback_data=f'loc_'))
	return markup


def keyboard_volume(brand):
	markup = types.InlineKeyboardMarkup()
	volumes = reader.read_volumes(brand)
	for i in range(0, len(volumes[1])):
		markup.add(types.InlineKeyboardButton(f'{volumes[1][i]}', callback_data=f'volume_{volumes[0][i]}'))
	markup.add(types.InlineKeyboardButton(text='Назад', callback_data=f'brand_'))
	return markup


def keyboard_taste(brandV):
	markup = types.InlineKeyboardMarkup()
	tastes = reader.read_tastes(brandV)
	for e in tastes:
		markup.add(types.InlineKeyboardButton(f'{e}', callback_data=f'taste_{e}'))
	markup.add(types.InlineKeyboardButton(text='Назад', callback_data=f'brand_'))
	return markup


def keyboard_count(count=0):
	markup = types.InlineKeyboardMarkup()
	btn_minus = types.InlineKeyboardButton('-', callback_data='count_minus')
	btn_count = types.InlineKeyboardButton(f'{count}', callback_data=f'count_{count}')
	btn_plus = types.InlineKeyboardButton('+', callback_data='count_plus')
	btn_add = types.InlineKeyboardButton('Готово', callback_data=f'count_{count}')
	markup.row(btn_minus, btn_count, btn_plus)
	markup.add(btn_add)
	return markup


def keyboard_choice(cart):
	markup = types.InlineKeyboardMarkup()
	# Checking carts
	try:
		print(cart.brand)
		for i in range(0, len(cart.brand)):
			markup.row(
				types.InlineKeyboardButton(text=f'{cart.brand[i]} {cart.taste[i]} {cart.count[i]} шт {cart.cost[i]} руб',
				                           callback_data="nothing"))
			markup.add(
				types.InlineKeyboardButton(text='Удалить ❌', callback_data=f'delete_{i}'))
	except Exception as exp:
		print("Error in keyboard_choice:", exp)
	btn_yes = types.InlineKeyboardButton("Заказать", callback_data='yes')
	btn_more = types.InlineKeyboardButton("Добавить еще", callback_data='no')
	markup.add(btn_yes, btn_more)
	return markup


def keyboard_time(page=0):
	markup = types.InlineKeyboardMarkup()
	settings = content.settingsUpdate()
	settings['ЧасСейчас'] = get_current_time().hour
	if int(settings['ЧасСейчас']) > int(settings['МаксЧас']):
		timeHour = page + int(settings['МинЧас'])
	elif int(settings['ЧасСейчас']) > int(settings['МинЧас']):
		timeHour = page + int(settings['ЧасСейчас'])
	else:
		timeHour = page + int(settings['МинЧас'])
	# print('timeHour is', timeHour)
	markup.add(types.InlineKeyboardButton(f'{timeHour}:00', callback_data=f'time_{timeHour}:00'),
	           types.InlineKeyboardButton(f'{timeHour}:0{1 * 5}', callback_data=f'time_{timeHour}:{1 * 5}'))
	markup.add(types.InlineKeyboardButton(f'{timeHour}:{2 * 5}', callback_data=f'time_{timeHour}:{2 * 5}'),
	           types.InlineKeyboardButton(f'{timeHour}:{3 * 5}', callback_data=f'time_{timeHour}:{3 * 5}'))
	markup.add(types.InlineKeyboardButton(f'{timeHour}:{4 * 5}', callback_data=f'time_{timeHour}:{4 * 5}'),
	           types.InlineKeyboardButton(f'{timeHour}:{5 * 5}', callback_data=f'time_{timeHour}:{5 * 5}'))
	markup.add(types.InlineKeyboardButton(f'{timeHour}:{6 * 5}', callback_data=f'time_{timeHour}:{6 * 5}'),
	           types.InlineKeyboardButton(f'{timeHour}:{7 * 5}', callback_data=f'time_{timeHour}:{7 * 5}'))
	markup.add(types.InlineKeyboardButton(f'{timeHour}:{8 * 5}', callback_data=f'time_{timeHour}:{8 * 5}'),
	           types.InlineKeyboardButton(f'{timeHour}:{9 * 5}', callback_data=f'time_{timeHour}:{9 * 5}'))
	markup.add(types.InlineKeyboardButton(f'{timeHour}:{10 * 5}', callback_data=f'time_{timeHour}:{10 * 5}'),
	           types.InlineKeyboardButton(f'{timeHour}:{11 * 5}', callback_data=f'time_{timeHour}:{11 * 5}'))
	markup.add(types.InlineKeyboardButton(f'{timeHour + 1}:00', callback_data=f'time_{timeHour + 1}:00'))
	time_next = types.InlineKeyboardButton('>>', callback_data='time_next')
	time_back = types.InlineKeyboardButton('<<', callback_data='time_back')
	markup.row(time_back, time_next)
	markup.add(types.InlineKeyboardButton('Назад', callback_data='count_'))
	return markup


def keyboard_contacts():
	markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
	btn_send_contacts = types.KeyboardButton(text="Отправить данные", request_contact=True)
	markup.add(btn_send_contacts)
	return markup


def keyboard_confirm_contacts():
	markup = types.InlineKeyboardMarkup()
	btn_yes = types.InlineKeyboardButton(text="Да, это мои данные", callback_data="contact_yes")
	btn_no = types.InlineKeyboardButton(text="Нет", callback_data="contact_no")
	markup.add(btn_yes)
	markup.add(btn_no)
	return markup


if __name__ == '__main__':
	bot.polling(none_stop=True)
