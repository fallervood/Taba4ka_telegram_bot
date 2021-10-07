def settingsUpdate():
	settings = {}
	with open('settings.txt', 'r', encoding='utf-8') as file:
		for row in file:
			line = row.split(':')
			settings[line[0]] = line[1]
		# print('Update in settings:\n',settings)
		return settings


def settingsWrite():
	lines = []
	with open('settings.txt', 'r', encoding='utf-8') as file:
		for row in file:
			if 'КолвоЗаказов' in row:
				line = row.split(':')
				try:
					line = 'КолвоЗаказов:' + str(int(line[1]) + 1)
					row = line
				except:
					line.append(1)
			lines.append(row)
	with open('settings.txt', 'w', encoding='utf-8') as file:
		for line in lines:
			file.write(line)
			

class Client:
	def __init__(self, client_id, name, phone, location, time):
		self.client_id = client_id
		self.name = name
		self.phone = phone
		self.location = location
		self.time = time


class Product:
	def __init__(self, brand, taste):
		self.brand = brand
		self.taste = taste


class Cart:
	def __init__(self, user_id, brand, taste, count, cost):
		self.user_id = user_id
		self.brand = brand
		self.taste = taste
		self.count = count
		self.cost = cost
