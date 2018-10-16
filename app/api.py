from flask import request
from app import app, LINK, IP_CLIENT, PLATFORM_WALLET, CONTRACT_ADDRESS, TOPIC_LESSON_STARTED, TOPIC_LESSON_PREPARED

import time
import base64
from mongodb import *
from re import findall, match, search
from hashlib import md5
from json import dumps, loads
from random import randint
from os import listdir, remove
import requests

# Socket.IO
from threading import Lock
from flask_socketio import SocketIO, emit

async_mode = None
socketio = SocketIO(app, async_mode=async_mode)

thread = None
thread_lock = Lock()


generate = lambda length=32: ''.join(['1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'[randint(0, 61)] for _ in range(length)])

def max_image(url):
	x = listdir(url)
	k = 0
	for i in x:
		j = findall(r'\d+', i)
		if len(j) and int(j[0]) > k:
			k = int(j[0])
	return k+1

def load_image(url, data, adr=None, format='jpg', type='base64'):
	if type == 'base64':
		data = base64.b64decode(data)

	if adr:
		id = adr

		for i in listdir(url):
			if search(r'^' + str(id) + '\.', i):
				remove(url + '/' + i)
	else:
		id = max_image(url)

	with open('%s/%s.%s' % (url, str(id), format), 'wb') as file:
		file.write(data)

	return id

def errors(x, filters):
	for i in filters:
		if i[0] in x:
			# Неправильный тип данных
			if type(x[i[0]]) != i[2] or (type(x[i[0]]) == list and any(type(j) != i[3] for j in x[i[0]])):
				mes = 'Invalid data type: %s (required %s' % (i[0], str(i[2]))
				if i[2] == list:
					mes += ' - %s' % str(i[3])
				mes += ')'
				return dumps({'error': 4, 'message': mes})

		# Не все поля заполнены
		elif i[1]:
			return dumps({'error': 3, 'message': 'Not all required fields are filled in: %s' % i[0]})

def reimg(s, type='steps', id1=0, id2=0):
	i = 1
	k = 0

	while True:
		x = search(r'<img ', s[k:])
		if x:
			st = list(x.span())
			st[1] = st[0] + s[k+st[0]:].index('>')
			vs = ''
			if 'src="' in s[k+st[0]:k+st[1]]:
				adr = '%d-%d' % (id2, i)
				if id1: adr = str(id1) + '-' + adr

				if search(r'image/.*;', s[k+st[0]:k+st[1]]) and 'base64,' in s[k+st[0]:k+st[1]]:
					start = k + st[0] + s[k+st[0]:].index('base64,') + 7
					stop = start + s[start:].index('"')

					b64 = s[start:stop]
					form = search(r'image/.*;', s[k+st[0]:start]).group(0)[6:-1]
					load_image('app/static/load/' + type, b64, adr, form)

					vs = '<img src="' + '/static/load/' + type + '/' + adr + '.' + form + '">' 
					# s = s[:k+s[k:].index('src="')+5] + '/static/load/' + type + '/' + adr + '.' + form + s[stop:]
				else:
					start = k + search(r'src=".*', s[k:]).span()[0] + 5
					stop = start + s[start:].index('"')
					href = s[start:stop]
					if href[:7] == '/static':
						href = LINK + href[1:]
					if href[:4] == 'http':
						b64 = str(base64.b64encode(requests.get(href).content))[2:-1]
						form = href.split('.')[-1]
						if 'latex' in form:
							form = 'png'
						load_image('app/static/load/' + type, b64, adr, form)

						vs = '<img src="' + '/static/load/' + type + '/' + adr + '.' + form + '">'

			if vs:
				s = s[:k+st[0]] + vs + s[k+st[1]+1:]
				k += st[0] + len(vs)
				i += 1
			else:
				k += st[1]
		else:
			break

	return s

def get_user(id):
	if id:
		req = db['users'].find_one({'id': id}, {'id': True, 'login': True, 'name': True, 'surname': True, '_id': False})
	else:
		req = 0
	return req


# type_transactions = (
# 	'Unknown transaction',
# 	'Send',
# 	'Registration',
# 	'Lesson',
# )


@app.route('/', methods=['POST'])
def process():
	x = request.json
	# print(x)

	if 'method' not in x:
		return dumps({'error': 2, 'message': 'Wrong method'})

	# Убираем лишние отступы
	for i in x:
		if type(x[i]) == str:
			x[i] = x[i].strip()

	# Определение пользователя
	if 'token' in x:
		user_id = db['tokens'].find_one({'token': x['token']}, {'id': True, '_id': False})['id']
		if user_id:
			user = db['users'].find_one({'id': user_id})
		else:
			return dumps({'error': 5, 'message': 'Invalid token'})

	else:
		user = {
			'id': 0,
			'admin': 2,
		}

	timestamp = time.time()

	req = {
		'time': timestamp,
		'user': user['id'],
		'admin': user['admin'],
		'request': x,
	}

	ip = request.remote_addr
	if 'ip' in x and ip == IP_CLIENT:
		req['ip'] = x['ip']
	else:
		req['ip'] = ip

	db['actions'].insert(req)

	try:
# Регистрация
		if x['method'] == 'profile.reg':
			# Не все поля заполнены
			mes = errors(x, (
				('login', True, str),
				('pass', True, str),
				('mail', True, str),
				('name', False, str),
				('surname', False, str),
			))
			if mes: return mes

			x['login'] = x['login'].lower()

			# Логин уже зарегистрирован
			if len(list(db['users'].find({'login': x['login']}, {'_id': True}))):
				return dumps({'error': 6, 'message': 'This login already exists'})

			# Недопустимый логин
			if not 3 <= len(x['login']) <= 10 or len(findall('[^a-z0-9]', x['login'])) or not len(findall('[a-z]', x['login'])):
				return dumps({'error': 7, 'message': 'Wrong login: length must be more than 3 and less than 10 characters, consist only of digits and at least a few latin letters'})

			# Почта уже зарегистрирована
			if len(list(db['users'].find({'mail': x['mail']}, {'_id': True}))):
				return dumps({'error': 8, 'message': 'This mail already exsists'})

			# Недопустимый пароль
			if not 6 <= len(x['pass']) <= 40 or len(findall('[^a-zA-z0-9!@#$%^&*()-_+=;:,./?\|`~\[\]{}]', x['pass'])) or not len(findall('[a-zA-Z]', x['pass'])) or not len(findall('[0-9]', x['pass'])):
				return dumps({'error': 9, 'message': 'Invalid password: the length must be from 6 to 40 characters, consist of mandatory digits, characters:! @, #, $, %, ^, &, *, (, ), -, _, +, =, ;, :, ,, ., /, ?, |, `, ~, [, ], {, } and necessarily Latin letters'})

			# Недопустимая почта
			if match('.+@.+\..+', x['mail']) == None:
				return dumps({'error': 10, 'message': 'Invalid mail'})

			# Недопустимое имя
			if 'name' in x and not x['name'].isalpha():
				return dumps({'error': 11, 'message': 'Invalid name'})

			# Недопустимая фамилия
			if 'surname' in x and not x['surname'].isalpha():
				return dumps({'error': 12, 'message': 'Invalid surname'})

			try:
				id = db['users'].find({}, {'id': True, '_id': False}).sort('id', -1)[0]['id'] + 1
			except:
				id = 1

			db['users'].insert({
				'id': id,
				'login': x['login'],
				'password': md5(bytes(x['pass'], 'utf-8')).hexdigest(),
				'mail': x['mail'],
				'name': x['name'].title() if 'name' in x else None,
				'surname': x['surname'].title() if 'surname' in x else None,
				'description': '',
				'rating': 0,
				'admin': 3,
				'ladders': {},
				'steps': [],
				'balance': 1000, #
			})

			token = generate()
			db['tokens'].insert({
				'token': token,
				'id': id,
				'time': timestamp,
			})

			return dumps({'error': 0, 'id': id, 'token': token})

# Авторизация
		elif x['method'] == 'profile.auth':
			mes = errors(x, (
				('login', True, str),
				('pass', True, str),
			))
			if mes: return mes

			x['login'] = x['login'].lower()

			# Неправильный логин
			if not len(list(db['users'].find({'login': x['login']}, {'_id': True}))):
				return dumps({'error': 6, 'message': 'Login does not exist'})

			password = md5(bytes(x['pass'], 'utf-8')).hexdigest()

			req = db['users'].find_one({'login': x['login'], 'password': password}, {'id': True, '_id': False})
			
			# Неправильный пароль
			if not req:
				return dumps({'error': 7, 'message': 'Invalid password'})

			token = generate()
			db['tokens'].insert({'token': token, 'id': req['id'], 'time': timestamp})

			return dumps({'error': 0, 'id': req['id'], 'token': token})

# Изменение личной информации
		elif x['method'] == 'profile.edit':
			mes = errors(x, (
				('token', True, str),
				('name', False, str),
				('surname', False, str),
				('description', False, str),
				('photo', False, str),
			))
			if mes: return mes

			if 'name' in x:
				# Недопустимое имя
				if not x['name'].isalpha():
					return dumps({'error': 6, 'message': 'Invalid name'})

				user['name'] = x['name'].title()

			if 'surname' in x:
				# Недопустимая фамилия
				if not x['surname'].isalpha():
					return dumps({'error': 7, 'message': 'Invalid surname'})

				user['surname'] = x['surname'].title()

			if 'description' in x:
				user['description'] = x['description']

			db['users'].save(user)

			if 'photo' in x:
				try:
					load_image('app/static/load/users', x['photo'], user['id'])

				# Ошибка загрузки фотографии
				except:
					return dumps({'error': 8, 'message': 'Error uploading photo'})

			return dumps({'error': 0})

# Закрытие сессии
		elif x['method'] == 'profile.exit':
			mes = errors(x, (
				('token', True, str),
			))
			if mes: return mes

			req = db['tokens'].find_one({'token': x['token']}, {'_id': True})
			db['tokens'].remove(req['_id'])
			return dumps({'error': 0})

# Добавление ледера
		elif x['method'] == 'ladders.add':
			mes = errors(x, (
				('token', True, str),
				('name', True, str),
				('description', True, str),
				('tags', True, list, str),
				# ('category', True, int),
				('preview', False, str),
			))
			if mes: return mes

			try:
				id = db['ladders'].find({}, {'id': True, '_id': False}).sort('id', -1)[0]['id'] + 1
			except:
				id = 1

			query = {
				'id': id,
				'user': user['id'],
				'time': timestamp,
				'status': 1,
				'view': [],
				'like': [],
				'dislike': [],
				'comment': [],
				'steps': [{
					'id': 0,
					'name': 'You have read and agreed to Honor code?',
					'cont': '<a href="/codex">Link to Honor code</a>',
					'options': ['Yes', 'No', 'Don\'t understand'],
					'answers': [1,],
					'theory': '<a href="/codex">Link to Honor code</a>',
					'user': user['id'],
					'view': [],
					'complete': [],
					'comment': [],
					'status': 3,
					'total': 0,
				},],
			}

			for i in ('name', 'tags', 'description'): # , 'category'
				if i in x:
					query[i] = x[i]

			db['ladders'].insert(query)

			if 'preview' in x:
				try:
					load_image('app/static/load/ladders', x['preview'], id, x['file'].split('.')[-1] if 'file' in x else None)

				# Ошибка загрузки изображения
				except:
					return dumps({'error': 6, 'message': 'Error uploading image'})

			return dumps({'error': 0, 'id': id})

# Изменение ледера
		elif x['method'] == 'ladders.edit':
			mes = errors(x, (
				('token', True, str),
				('id', True, int),
				('name', False, str),
				('description', False, str),
				('tags', False, list, str),
				('preview', False, str),
			))
			if mes: return mes

			query = db['ladders'].find_one({'id': x['id']})

			# Неправильный ледер
			if not query:
				return dumps({'error': 6, 'message': 'Ladder does not exsist'})

			# Нет прав на редактирование
			if user['admin'] < 5:
				return dumps({'error': 7, 'message': 'No access rights'})

			for i in ('name', 'description', 'tags'): # 'category'
				if i in x: query[i] = x[i]

			query['status'] = 3 if user['admin'] >= 5 else 2

			db['ladders'].save(query)

			if 'preview' in x:
				try:
					load_image('app/static/load/ladders', x['preview'], x['id'], x['file'].split('.')[-1] if 'file' in x else None)

				# Ошибка загрузки изображения
				except:
					return dumps({'error': 8, 'message': 'Error uploading image'})

			return dumps({'error': 0})

# Список ледеров # сделать выборку полей
		elif x['method'] == 'ladders.gets':
			mes = errors(x, (
				('count', False, int),
				('category', False, int)
			))
			if mes: return mes

			count = x['count'] if 'count' in x else None

			category = None
			# if 'category' in x:
			# 	category = [x['category'],]
			# 	for i in db['categories'].find({'parent': x['category']}, {'id': True, '_id': False}):
			# 		category.append(i['id'])
			# 	category = {'category': {'$in': category}}

			ladders = list(db['ladders'].find(category, {'_id': False, 'id': True, 'name': True, 'steps.complete': True}))
			for i in range(len(ladders)):
				ladders[i]['complete'] = sum(len(j['complete']) for j in ladders[i]['steps'])

			ladders.sort(key=lambda i: i['complete'], reverse=-1)

			for i in range(len(ladders)):
				del ladders[i]['steps']
				del ladders[i]['complete']

			# ! Преобразовать поле просмотров

			return dumps({'error': 0, 'ladders': ladders})

# Получение ледера
		elif x['method'] == 'ladders.get':
			mes = errors(x, (
				('token', False, str),
				('id', True, int),
			))
			if mes: return mes

			ladder = db['ladders'].find_one({'id': x['id']})

			# Неправильный ледер
			if not ladder:
				return dumps({'error': 6, 'message': 'Ladder does not exsist'})

			ladder['view'].append(user['id'])
			db['ladders'].save(ladder)
			s = str(x['id'])

			step_id = -1
			step_num = -1

			if user['admin'] >= 3:
				if s in user['ladders']:
					j = user['ladders'][s]

					for i, el in enumerate(ladder['steps']):
						if ((user['admin'] >= 5 and el['status']) or el['status'] >= 3) and el['id'] not in j:
							step_id = el['id']
							step_num = i
							break
				else:
					for i, el in enumerate(ladder['steps']):
						if (user['admin'] >= 5 and el['status']) or el['status'] >= 3:
							step_id = el['id']
							step_num = i
							break

					user['ladders'][s] = []
					db['users'].save(user)
			else:
				for i, el in enumerate(ladder['steps']):
					if el['status'] >= 3:
						step_id = el['id']
						step_num = i
						break

			view = set(ladder['view'])
			user_top = []
			for i in view:
				filter_db = {'_id': False, 'ladders': True, 'name': True, 'surname': True, 'login': True}
				users = db['users'].find_one({'id': i, 'admin': {'$gte': 3}}, filter_db)
				if not users:
					continue

				steps = [j['id'] for j in ladder['steps']]
				kol = len(set(users['ladders'][s]) & set(steps)) # При ошибке: обнулить view ladder
				user_info = {
					'id': i,
					'name': users['name'],
					'surname': users['surname'],
					'login': users['login'],
					'complete': kol,
				}
				user_top.append((kol, user_info))
			user_top = [i[1] for i in sorted(user_top, key=lambda y: y[0], reverse=True)]

			for i in range(len(ladder['steps'])):
				ladder['steps'][i]['price'] = (20 + i) * 10

			# !

			del ladder['_id']
			del ladder['view']
			del ladder['time']
			del ladder['user']
			for i in range(len(ladder['steps'])):
				for j in ('answers', 'view', 'cont', 'options', 'comment', 'user', 'theory'):
					del ladder['steps'][i][j]

			i = 0
			while i < len(ladder['steps']):
				if not ladder['steps'][i]['status']:
					del ladder['steps'][i]
				else:
					i += 1

			def get_step(j):
				for i, el in enumerate(ladder['steps']):
					if el['id'] == j:
						return {
							'id': j,
							'name': el['name'],
							'num': i,
						}
				return None

			user_steps = []
			if 'token' in x:
				for i in user['ladders'][str(x['id'])]:
					s = get_step(i)
					if s:
						user_steps.append(s)
				user_steps.sort(key=lambda i: i['num'], reverse=-1)

			req = {
				'error': 0,
				'ladder': ladder,
				'step': step_id,
				'num': step_num,
				'experts': user_top,
				'steps': user_steps
			}

			return dumps(req)

# Добавление степа # добавлять по id # менять местами
		elif x['method'] == 'step.add':
			mes = errors(x, (
				('token', True, str),
				('id', False, int),
				('after', False, bool),
				('ladder', True, int),
				('name', True, str),
				('options', True, list, str),
				('answers', False, list, int),
				('cont', False, str),
				('theory', True, str),
			))
			if mes: return mes

			ladder = db['ladders'].find_one({'id': x['ladder']})

			# Неправильный ледер
			if not ladder:
				return dumps({'error': 6, 'message': 'Wrong id of ladder'})

			try:
				step_all = [i['id'] for i in ladder['steps']]
				step_id = max(step_all) + 1
			except:
				step_all = []
				step_id = 0

			if 'id' in x:
				if x['id'] not in step_all:
					return dumps({'error': 7, 'message': 'Wrong id of step'})
			else:
				x['id'] = step_all[-1]
				x['after'] = True

			if x['theory'] and 'answers' in x:
				if user['admin'] >= 5:
					status = 3
				else:
					status = 2
			else:
				status = 1

			step = {
				'id': step_id,
				'name': x['name'],
				'options': [i.strip() for i in x['options']],
				'answers': x['answers'] if 'answers' in x else [],
				'user': user['id'],
				'view': [],
				'comment': [],
				'status': status,
				'cont': reimg(x['cont'], 'steps', x['ladder'], step_id) if 'cont' in x else '',
				'theory': reimg(x['theory'], 'theory', x['ladder'], step_id),
				'complete': [],
			}

			after = x['after'] if 'after' in x else False

			if 'id' in x and x['id'] in step_all and not (after and step_all.index(x['id']) == (len(step_all) - 1)):
				step_num = step_all.index(x['id']) + after
				ladder['steps'] = ladder['steps'][:step_num+after] + [step] + ladder['steps'][step_num+after:]
			else:
				step_num = len(step_all)
				ladder['steps'].append(step)

			db['ladders'].save(ladder)

			return dumps({'error': 0, 'id': step_id, 'num': step_num})

# Изменение степа
		elif x['method'] == 'step.edit':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('step', True, int),
				('name', False, str),
				('options', False, list, str),
				('answers', False, list, int),
				('cont', False, str),
				('theory', False, str),
				('id', False, int),
				('after', False, bool),
			))
			if mes: return mes

			ladder = db['ladders'].find_one({'id': x['ladder']})

			# Неправильный ледер
			if not ladder:
				return dumps({'error': 6, 'message': 'Wrong id of ladder'})

			try:
				step_all = [i['id'] for i in ladder['steps']]
			except:
				step_all = []

			# Неправильный степ
			if x['step'] not in step_all:
				return dumps({'error': 7, 'message': 'Wrong id of step'})

			step_num = step_all.index(x['step'])

			# Нет прав на редактирование
			if user['admin'] < 5 and user['id'] != ladder['steps'][step_num]['user']:
				return dumps({'error': 8, 'message': 'No access rights'})

			for i in ('name', 'options', 'answers', 'cont', 'theory'):
				if i in x:
					if type(x[i]) == list and type(x[i][0]) == str:
						x[i] = [j.strip() for j in x[i]]

					if i == 'cont':
						x[i] = reimg(x[i], 'steps', x['ladder'], x['step'])
					elif i == 'theory':
						x[i] = reimg(x[i], 'theory', x['ladder'], x['step'])

					ladder['steps'][step_num][i] = x[i]

			ladder['steps'][step_num]['status'] = 2 if user['admin'] < 5 else 3

			if 'id' in x:
				if x['id'] not in step_all:
					return dumps({'error': 9, 'message': 'Wrong id of step'})

				step = ladder['steps'][step_num]
				del ladder['steps'][step_num]
				del step_all[step_num]

				after = x['after'] if 'after' in x else False

				if x['id'] in step_all and not (after and step_all.index(x['id']) == (len(step_all) - 1)):
					step_num = step_all.index(x['id']) + after
					ladder['steps'] = ladder['steps'][:step_num+after] + [step] + ladder['steps'][step_num+after:]
				else:
					step_num = len(step_all)
					ladder['steps'].append(step)

			db['ladders'].save(ladder)

			return dumps({'error': 0, 'num': step_num})

# Удаление степа
		elif x['method'] == 'step.delete':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('step', True, int),
			))
			if mes: return mes

			ladder = db['ladders'].find_one({'id': x['ladder']})

			# Неправильный ледер
			if not ladder:
				return dumps({'error': 6, 'message': 'Wrong id of ladder'})

			try:
				step_all = [i['id'] for i in ladder['steps']]
			except:
				step_all = []

			# Неправильный степ
			if x['step'] not in step_all:
				return dumps({'error': 7, 'message': 'Wrong id of step'})

			step_num = step_all.index(x['step'])

			# Нет прав на удаление
			if user['admin'] < 6:
				return dumps({'error': 8, 'message': 'No access rights'})

			# del ladder['steps'][step_num]
			ladder['steps'][step_num]['status'] = 0

			db['ladders'].save(ladder)

			# Куда перекинуть после удаления
			step_next = -1
			if len(ladder['steps']) > step_num + 1:
				for e in ladder['steps'][step_num+1:]:
					if user['admin'] >= 5 or e['status'] >= 3:
						step_next = e['id']
						break

			step_num -= step_num != 0

			return dumps({'error': 0, 'num': step_num, 'step': step_next})

# Получение степа
		elif x['method'] == 'step.get':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('step', True, int),
			))
			if mes: return mes

			ladder = db['ladders'].find_one({'id': x['ladder']})

			# Неправильный ледер
			if not ladder:
				return dumps({'error': 6, 'message': 'Ladder does not exsist'})

			try:
				step_all = [j['id'] for j in ladder['steps']]
				step_available = [j['id'] for j in ladder['steps'] if (user['admin'] >= 6 and j['status']) or j['status'] >= 3]
			except:
				step_all = []
				step_available = []

			# Неправильный степ
			if x['step'] not in step_all:
				return dumps({'error': 7, 'message': 'Step does not exsist'})

			step_num = step_all.index(x['step'])
			step_num_available = step_available.index(x['step'])

			s = str(x['ladder'])

			if s not in user['ladders']:
				user['ladders'][s] = []
				db['users'].save(user)

			# Степ недоступен
			try:
				step_user = max(step_available.index(i) for i in user['ladders'][s] if i in step_available)
			except:
				step_user = 0

				for i, el in enumerate(ladder['steps']):
					if (user['admin'] >= 5 and el['status']) or el['status'] >= 3:
						step_user = i
						break

			if (user['admin'] < 7 and step_num_available > step_user + 1 and ladder['steps'][step_num]['user'] != user['id']) or (user['admin'] < 5 and ladder['steps'][step_num]['status'] < 3 and ladder['steps'][step_num]['user'] != user['id']):
				return dumps({'error': 8, 'message': 'You are not yet available this step'})

			ladder['steps'][step_num]['view'].append(user['id'])
			db['ladders'].save(ladder)

			if ladder['steps'][step_num]['user'] != user['id'] and user['admin'] <= 3:
				del ladder['steps'][step_num]['answers']

			author = get_user(ladder['steps'][step_num]['user'])

			step = ladder['steps'][step_num]

			step['next'] = None
			for i, el in enumerate(ladder['steps']): # ! обрезать
				if ((user['admin'] >= 5 and el['status']) or el['status'] >= 3) and i > step_num:
					step['next'] = {
						'id': el['id'],
						'name': el['name'],
					}

			step['prev'] = None
			for i, el in enumerate(ladder['steps']): # ! обрезать
				if ((user['admin'] >= 5 and el['status']) or el['status'] >= 3) and i < step_num:
					step['prev'] = {
						'id': el['id'],
						'name': el['name'],
					}

			del step['view']

			spaces = list(db['study'].find({'student': user['id'], 'ladder': x['ladder'], 'step': x['step'], 'teacher': {'$ne': 0}}, {'_id': False, 'id': True, 'teacher': True}))
			for i in range(len(spaces)):
				users = db['users'].find_one({'id': spaces[i]['teacher']}, {'_id': False, 'name': True, 'surname': True, 'login': True})
				for j in ('name', 'surname', 'login'):
					spaces[i][j] = users[j]

			res = {
				'error': 0,
				'step': step,
				'num': step_num,
				'name': ladder['name'],
				'tags': ladder['tags'],
				'author': author,
				'complete': True if x['step'] in user['ladders'][str(x['ladder'])] else False,
				'spaces': spaces,
			}

			return dumps(res)

# Список степов
		elif x['method'] == 'step.gets':
			mes = errors(x, (
				('token', False, str),
				('ladder', True, int),
			))
			if mes: return mes

			filter_db = {'steps.name': True, 'steps.id': True, '_id': False, 'steps.status': True}
			# status = 1 if user['admin'] >= 5 else 3
			# 'status': {'$gte': status}
			ladder = db['ladders'].find_one({'id': x['ladder']}, filter_db)

			# Неправильный ледер
			if not ladder:
				return dumps({'error': 6, 'message': 'Ladder does not exsist'})

			try:
				step_list = [[j['id'], j['name']] for j in ladder['steps'] if j['status'] >= 1]
			except:
				step_list = []

			return dumps({'error': 0, 'steps': step_list})

# Проверка ответов
		elif x['method'] == 'step.check':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('step', True, int),
				('answers', True, list, int),
			))
			if mes: return mes

			ladder = db['ladders'].find_one({'id': x['ladder']})

			# Неправильный ледер
			if not ladder:
				return dumps({'error': 6, 'message': 'Ladder does not exsist'})

			# status = 3 if user['admin'] < 5 else 1 # Неподтверждённые степы обычным пользователям не отображаются
			# if j['status'] >= status

			try:
				step_all = [j['id'] for j in ladder['steps']]
				step_available = [j['id'] for j in ladder['steps'] if (user['admin'] >= 6 and j['status']) or j['status'] >= 3]
			except:
				step_all = []
				step_available = []

			# Неправильный степ
			if x['step'] not in step_available:
				return dumps({'error': 7, 'message': 'Step does not exsist'})

			step_num = step_all.index(x['step'])
			step_num_available = step_available.index(x['step'])

			# Нет прав на проверку ответов
			if user['admin'] < 3:
				return dumps({'error': 8, 'message': 'No access rights'})

			# Ледер недоступен
			s = str(x['ladder'])
			if s not in user['ladders']:
				dumps({'error': 9, 'message': 'You are not yet available this ladder'})

			# Степ недоступен
			try:
				step_user = max(step_available.index(i) for i in user['ladders'][s] if i in step_available)
			except:
				step_user = 0

				for i, el in enumerate(ladder['steps']):
					if (user['admin'] >= 5 and el['status']) or el['status'] >= 3:
						step_user = i
						break

			if (user['admin'] < 7 and step_num_available > step_user + 1 and ladder['steps'][step_num]['user'] != user['id']) or (user['admin'] < 5 and ladder['steps'][step_num]['status'] < 3 and ladder['steps'][step_num]['user'] != user['id']):
				return dumps({'error': 10, 'message': 'You are not yet available this step'})

			suc = set(x['answers']) == set(ladder['steps'][step_num]['answers'])

			if suc:
				if x['step'] not in user['ladders'][s]:
					# Обновить информацию пользователя
					ladder['steps'][step_num]['complete'].append(user['id'])
					db['ladders'].save(ladder)

					user['ladders'][s].append(x['step'])

					# Добавить в список для обучения
					step = {
							'ladder': x['ladder'],
							'step': x['step'],
							'price': (20 + x['step']) * 10, # !
						}

					user['steps'].append(step)

					db['users'].save(user)

					# Обновить список степов для поиска онлайн учителя
					users = db['online'].find_one({'id': user['id']})
					if users:
						users['steps'].append(step)

				# Следующий степ
				step_next = -1
				for u, e in enumerate(ladder['steps']):
					if e['id'] not in user['ladders'][s] and e['status'] >= 3:
						step_next = e['id']
						break

				# if step_next == -1:
				# 	if step_num < len(step_all):
				# 		step_next = step_all[step_num]

			return dumps({'error': 0, 'correct': suc, 'step': step_next if suc else x['step']})

# Список учителей
		elif x['method'] == 'study.gets':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('step', True, int),
			))
			if mes: return mes

			ladder = db['ladders'].find_one({'id': x['ladder']}, {'_id': False, 'steps.id': True})

			# Неправильный ледер
			if not ladder:
				return dumps({'error': 6, 'message': 'Ladder does not exsist'})

			try:
				step_all = [j['id'] for j in ladder['steps']]
			except:
				step_all = []

			# Неправильный степ
			if x['step'] not in step_all:
				return dumps({'error': 7, 'message': 'Step does not exsist'})

			step_num = step_all.index(x['step'])

			# Нет прав на обучение
			if user['admin'] < 3:
				return dumps({'error': 8, 'message': 'No access rights'})

			# Удалить предыдущие сеансы
			for i in db['teachers'].find({'user': user['id']}):
				socketio.emit('remove', {
					'ladder': i['ladder'],
					'step': i['step'],
					'user': i['user'],
				}, namespace='/study')

				db['teachers'].remove(i['_id'])

			filter_db = {'_id': False, 'user': True, 'price': True}
			users = list(db['teachers'].find({'ladder': x['ladder'], 'step': x['step']}, filter_db))

			for i, el in enumerate(users):
				filter_db = {'_id': False, 'id': True, 'name': True, 'surname': True, 'login': True}
				req = db['users'].find_one({'id': el['user']}, filter_db)
				for j in req:
					users[i][j] = req[j]

				users[i]['rating'] = 0 #

			# Список пользователей онлайн
			ladder_str = str(x['ladder'])

			online = []
			for i in db['online'].find({'user': {'$ne': user['id']}, 'steps': {'$elemMatch': {'ladder': x['ladder'], 'step': x['step']}}}, {'_id': False, 'user': True, 'steps': True}):
				req = {'user': i['user']}
				for j in i['steps']:
					if j['ladder'] == x['ladder'] and j['step'] == x['step']:
						req['price'] = j['price']
				online.append(req)

			for i, el in enumerate(online):
				filter_db = {'_id': False, 'id': True, 'name': True, 'surname': True, 'login': True}
				req = db['users'].find_one({'id': el['user']}, filter_db)
				for j in req:
					online[i][j] = req[j]

				online[i]['price'] = el['price']
				online[i]['rating'] = 0 #

			req = {
				'error': 0,
				'bot': {
					'price': (20 + step_num) * 10, #
				},
				'teachers': [],
				'users': users,
				'online': online,
			}

			return dumps(req)

# Начало обучения
		elif x['method'] == 'study.start':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('step', True, int),
				('teacher', True, int),
			))
			if mes: return mes

			filter_db = {'_id': False, 'steps.id': True, 'steps.user': True}
			ladder = db['ladders'].find_one({'id': x['ladder']}, filter_db)

			# Неправильный ледер
			if not ladder:
				return dumps({'error': 6, 'message': 'Ladder does not exsist'})

			try:
				step_all = [j['id'] for j in ladder['steps']]
			except:
				step_all = []

			# Неправильный степ
			if x['step'] not in step_all:
				return dumps({'error': 7, 'message': 'Step does not exsist'})

			step_num = step_all.index(x['step'])

			# Нет прав на обучение
			if user['admin'] < 3:
				return dumps({'error': 8, 'message': 'No access rights'})

			# Нельзя учить самого себя
			if user['id'] == x['teacher']:
				return dumps({'error': 9, 'message': 'You can not teach yourself!'})

			try:
				id = db['study'].find({}, {'_id': False, 'id': True}).sort('id', -1)[0]['id'] + 1
			except:
				id = 1

			request_user = False

			if x['teacher']:
				users = db['teachers'].find_one({'user': x['teacher'], 'ladder': x['ladder'], 'step': x['step']}, {'_id': False, 'price': True})

				# Если пользователь ожидает ученика
				if users:
					price = users['price']

				else:
					# Онлайн пользователь
					condition_db = {
						'user': x['teacher'],
						'steps': {
							'$elemMatch': {
								'ladder': x['ladder'],
								'step': x['step'],
							}
						}
					}
					filter_db = {'_id': False, 'steps': True}

					users = db['online'].find_one(condition_db, filter_db)

					# Запрос онлайн пользователю
					if users:
						for i in users['steps']:
							if i['ladder'] == x['ladder'] and i['step'] == x['step']:
								price = i['price']

						request_user = True

					# Учитель не найден
					else:
						return dumps({'error': 10, 'message': 'Teacher is not available!'})
			else:
				price = (20 + x['step']) * 10

			#

			if price > user['balance']:
				return dumps({'error': 11, 'message': 'Not enough tokens!'})

			if not x['teacher']:
				user['balance'] -= price
				db['users'].save(user)

			#
		
			db['study'].insert_one({
				'id': id,
				'teacher': x['teacher'],
				'student': user['id'],
				'ladder': x['ladder'],
				'step': x['step'],
				'price': price,
				'time': timestamp,
				'status': 0 if x['teacher'] else 17,
				'messages': [],
			})

			author_wallet = db['users'].find_one({'id': ladder['steps'][step_num]['user']}, {'_id': False, 'public': True})['public']

			# ! переделать на общее пространство сайта

			if x['teacher']:
				if request_user:
					socketio.emit('teacher', {
						'teacher': x['teacher'],
						'id': id,
						'user': user['id'],
						'ladder': x['ladder'],
						'step': x['step'],
						'price': price,
					}, namespace='/main')
				else:
					socketio.emit('study', {
						'teacher': x['teacher'],
						'id': id,
						'user': user['id'],
						'ladder': x['ladder'],
						'step': x['step'],
						'price': price,
						'wallet_student': user['public'],
						'wallet_author': author_wallet,
						'wallet_platform': PLATFORM_WALLET,
					}, namespace='/teach')

			return dumps({'error': 0, 'id': id})

# Конец обучения
		elif x['method'] == 'study.stop':
			mes = errors(x, (
				('token', True, str),
				('id', True, int),
				('status', True, int),
			))
			if mes: return mes

			study = db['study'].find_one({'id': x['id']})

			if not study:
				return dumps({'error': 6, 'message': 'Training session does not exsist'})

			if x['status'] == 0:
				study['status'] = 2

			elif x['status'] == 1:
				study['status'] = 3

			else:
				return dumps({'error': 7, 'message': 'Invalid training status'})

			db['study'].save(study)

			return dumps({'error': 0, 'ladder': study['ladder'], 'step': study['step']})

# Получение пространства обучения
		elif x['method'] == 'study.get':
			mes = errors(x, (
				('token', True, str),
				('id', True, int),
			))
			if mes: return mes

			study = db['study'].find_one({'id': x['id']})

			if not study:
				return dumps({'error': 6, 'message': 'Training session does not exsist'})

			if user['id'] != study['student'] and user['id'] != study['teacher'] and user['admin'] < 6:
				return dumps({'error': 7, 'message': 'No access rights'})

			# Учитель подтвердил начало обучения
			if user['id'] == study['teacher'] and study['status'] == 0:
				study['status'] = 1
				# study['height'] = loads(requests.get('https://testnet.qtum.org/insight-api/sync').text)['blockChainHeight']
				db['study'].save(study)

				# Удалить объявления об обучении
				for i in db['teachers'].find({'user': study['teacher']}):
					socketio.emit('remove', {
						'ladder': i['ladder'],
						'step': i['step'],
						'user': i['user'],
					}, namespace='/study')

					db['teachers'].remove(i['_id'])

				wallet_teacher = db['users'].find_one({'id': study['teacher']}, {'_id': False, 'public': True})['public']

				socketio.emit('accept', {
					'id': x['id'],
					'teacher': wallet_teacher,
					'price': study['price'],
				}, namespace='/space')

			filter_db = {
				'_id': False,
				'name': True,
				'tags': True,
				'steps.id': True,
				'steps.name': True,
				'steps.cont': True,
				'steps.theory': True
			}

			ladder = db['ladders'].find_one({'id': study['ladder']}, filter_db)

			step_all = [j['id'] for j in ladder['steps']]
			step_num = step_all.index(study['step'])

			step = ladder['steps'][step_num]

			study['step_name'] = step['name']
			study['step_cont'] = step['cont']
			study['theory'] = step['theory']
			study['ladder_name'] = ladder['name']
			study['tags'] = ladder['tags']

			filter_db = {'_id': False, 'name': True, 'surname': True, 'login': True, 'id': True}
			users = db['users'].find_one({'id': study['student']}, filter_db)
			study['student'] = users

			if study['teacher']:
				study['wallet'] = db['users'].find_one({'id': study['teacher']}, {'_id': False, 'public': True})['public']
			else:
				study['wallet'] = PLATFORM_WALLET

			if study['teacher']:
				filter_db = {'_id': False, 'name': True, 'surname': True, 'login': True, 'id': True}
				users = db['users'].find_one({'id': study['teacher']}, filter_db)
				study['teacher'] = users

			del study['_id']

			finished = study['status'] not in (0, 1, 14, 17, 18, 19)

			return dumps({'error': 0, 'study': study, 'finished': finished})

# Начало обучения
		elif x['method'] == 'teach.start':
			mes = errors(x, (
				('token', True, str),
				('steps', True, list, dict),
			))
			if mes: return mes

			filter_db = {'_id': False, 'id': True, 'steps.id': True}
			ladder_list = {str(i['id']): [j['id'] for j in i['steps']] for i in db['ladders'].find({}, filter_db)}

			for i in x['steps']:
				lad = str(i['ladder'])
				if type(i['ladder']) != int or lad not in ladder_list:
					return dumps({'error': 6, 'message': 'Invalid ladder: ' + lad})

				if type(i['step']) != int or i['step'] not in ladder_list[lad]:
					return dumps({'error': 7, 'message': 'Invalid step: ' + str(i['step']) + ' in ladder: ' + lad})
				if i['step'] not in user['ladders'][lad]:
					return dumps({'error': 8, 'message': 'Can not teach step: ' + str(i['step']) + ' in ladder: ' + lad})

				# if type(i['price']) != int or i['price'] < 0:
				# 	return dumps({'error': 9, 'message': 'Invalid count of tokens'})

			user['steps'] = x['steps']
			db['users'].save(user)

			url = '/static/load/users/'
			img = url + '0.png'
			for i in listdir('app' + url):
				if search(r'^' + str(user['id']) + '\.', i):
					img = url + i

			for i in db['teachers'].find({'user': user['id']}):
				socketio.emit('remove', {
					'ladder': i['ladder'],
					'step': i['step'],
					'user': i['user'],
				}, namespace='/study')

				db['teachers'].remove(i['_id'])


			for i in x['steps']:
				socketio.emit('add', {
					'ladder': i['ladder'],
					'step': i['step'],
					'user': user['id'],
					'photo': img,
					'name': user['name'],
					'login': user['login'],
					'rating': 0,
					'tokens': i['price'],
				}, namespace='/study')

				db['teachers'].insert_one({
					'user': user['id'],
					'ladder': i['ladder'],
					'step': i['step'],
					'price': i['price'],
					'time': timestamp,
				})

			return dumps({'error': 0})

# Получение пользователя
		elif x['method'] == 'users.get':
			mes = errors(x, (
				('token', False, str),
				('id', True, int),
			))
			if mes: return mes

			users = db['users'].find_one({'id': x['id']}, {'_id': False, 'password': False})

			# Неправильный пользователь
			if not users:
				return dumps({'error': 6, 'message': 'User does not exsist'})

			if users['admin'] < 3 and user['admin'] < 6:
				return dumps({'error': 7, 'message': 'The user is blocked'})

			for i in users['ladders']:
				filter_db = {'_id': False, 'steps.id': True, 'steps.status': True, 'name': True}
				ladder = db['ladders'].find_one({'id': int(i)}, filter_db)
				step_all_published = [j['id'] for j in ladder['steps'] if j['status'] >= 3]

				j = 0
				while j < len(users['ladders'][i]):
					if users['ladders'][i][j] not in step_all_published:
						del users['ladders'][i][j]
					else:
						j += 1

				users['ladders'][i] = {
					'name': ladder['name'],
					'steps': users['ladders'][i],
					'complete': len(set(users['ladders'][i]) & set(step_all_published)),
					'all': len(step_all_published)
				}

			return dumps({'error': 0, 'user': users})

# Блокировка пользователя
		elif x['method'] == 'users.block':
			mes = errors(x, (
				('token', True, str),
				('id', True, int),
			))
			if mes: return mes

			users = db['users'].find_one({'id': x['id']})

			# Неправильный пользователь
			if not users:
				return dumps({'error': 6, 'message': 'User does not exsist'})

			# Нет прав на блокировку
			if user['admin'] < 6 or users['admin'] > user['admin']:
				return dumps({'error': 7, 'message': 'No access rights'})

			users['admin'] = 1
			db['users'].save(users)

			return dumps({'error': 0})

# Список пользователей
		elif x['method'] == 'members.gets':
			mes = errors(x, (
				('token', False, str),
				('count', False, int),
				('sort', False, int),
			))
			if mes: return mes

			count = x['count'] if 'count' in x else None

			filter_db = {'_id': False, 'id': True, 'login': True, 'name': True, 'surname': True} # rating

			if 'sort' in x:
				users = db['users'].find({'admin': {'$gte': 2}}, filter_db).sort('rating.' + str(x['sort']), -1)
			else:
				users = db['users'].find({'admin': {'$gte': 2}}, filter_db)
			
			return dumps({'error': 0, 'users': [i for i in users[:count]]})

# Добавление новостей
		elif x['method'] == 'news.add':
			mes = errors(x, (
				('token', True, str),
				('name', True, str),
				('description', True, str),
				('cont', True, str),
				('preview', True, str),
			))
			if mes: return mes

			try:
				id = db['news'].find({}, {'id': True, '_id': False}).sort('id', -1)[0]['id'] + 1
			except:
				id = 1

			# Нет прав на создание новости
			if user['admin'] < 6:
				return dumps({'error': 6, 'message': 'No access rights'})

			query = {
				'id': id,
				'name': x['name'],
				'description': x['description'],
				'cont': reimg(x['cont'], 'news', 0, id),
				'user': user['id'],
				'time': timestamp,
				'view': [],
				'like': [],
				'dislike': [],
				'comment': [],
			}

			db['news'].insert(query)

			if 'preview' in x:
				try:
					load_image('app/static/load/news', x['preview'], id, x['file'].split('.')[-1] if 'file' in x else None)

				# Ошибка загрузки изображения
				except:
					return dumps({'error': 7, 'message': 'Error uploading image'})

			return dumps({'error': 0, 'id': id})

# Изменение новостей
		elif x['method'] == 'news.edit':
			mes = errors(x, (
				('token', True, str),
				('id', True, int),
				('name', False, str),
				('description', False, str),
				('cont', False, str),
				('preview', False, str),
			))
			if mes: return mes

			query = db['news'].find_one({'id': x['id']})

			# Неправильная новость
			if not query:
				return dumps({'error': 6, 'message': 'News does not exsist'})

			# Нет прав на редактирование
			if user['admin'] < 6:
				return dumps({'error': 7, 'message': 'No access rights'})

			for i in ('name', 'description'):
				if i in x:
					query[i] = x[i]

			if 'cont' in x:
				query['cont'] = reimg(x['cont'])

			db['news'].save(query)

			if 'preview' in x:
				try:
					load_image('app/static/load/news', x['preview'], x['id'], x['file'].split('.')[-1] if 'file' in x else None)

				# Ошибка загрузки изображения
				except:
					return dumps({'error': 8, 'message': 'Error uploading image'})

			return dumps({'error': 0})

# Список новостей
		elif x['method'] == 'news.gets':
			mes = errors(x, (
				('token', False, str),
				('count', False, int),
			))
			if mes: return mes

			count = x['count'] if 'count' in x else None

			filter_db = {'_id': False, 'name': True, 'id': True}

			news = list(db['news'].find({}, filter_db).sort('time', -1))

			return dumps({'error': 0, 'news': news})

# Получение новости
		elif x['method'] == 'news.get':
			mes = errors(x, (
				('token', False, str),
				('id', True, int),
			))
			if mes: return mes

			req = db['news'].find_one({'id': x['id']})
			req['view'].append(user['id'])
			db['news'].save(req)

			# Неправильная новость
			if not req:
				return dumps({'error': 6, 'message': 'News does not exsist'})

			#

			del req['_id']
			del req['view']
			del req['user']

			return dumps({'error': 0, 'news': req})

# Удаление новости
		elif x['method'] == 'news.delete':
			mes = errors(x, (
				('token', True, str),
				('id', True, int),
			))
			if mes: return mes

			# Нет прав на удаление
			if user['admin'] < 6:
				return dumps({'error': 6, 'message': 'No access rights'})

			news = db['news'].find_one({'id': x['id']}, {'_id': True})

			# Неправильная новость
			if not news:
				return dumps({'error': 7, 'message': 'Wrong id of news'})

			db['news'].remove(news['_id'])

			return dumps({'error': 0})

# Добавление ошибок и предложений
		elif x['method'] == 'feedback.add':
			mes = errors(x, (
				('token', False, str),
				('name', True, str),
				('cont', True, str),
			))
			if mes: return mes

			try:
				id = db['feedback'].find({}, {'_id': False, 'id': True}).sort('id', -1)[0]['id'] + 1
			except:
				id = 1

			query = {
				'id': id,
				'name': x['name'],
				'cont': reimg(x['cont'], 'feedbacks', 0, id),
				'user': user['id'],
				'time': timestamp,
				'success': 0,
			}

			db['feedback'].insert(query)

			return dumps({'error': 0, 'id': id})

# Список ошибок и предложений
		elif x['method'] == 'feedback.gets':
			mes = errors(x, (
				('token', False, str),
				('count', False, int),
			))
			if mes: return mes

			# Нет прав на просмотр отзывов
			if user['admin'] < 4:
				return dumps({'error': 6, 'message': 'No access rights'})

			count = x['count'] if 'count' in x else None

			news = list(db['feedback'].find({}, {'_id': False}).sort('time', -1)[0:count])

			for i in range(len(news)):
				news[i]['user'] = get_user(news[i]['user'])

			return dumps({'error': 0, 'feedback': news})

# Удаление ошибок и предложений
		elif x['method'] == 'feedback.delete':
			mes = errors(x, (
				('token', True, str),
				('id', True, int),
			))
			if mes: return mes

			feedback = db['feedback'].find_one({'id': x['id']}, {'_id': True})

			# Неправильный отзыв
			if not feedback:
				return dumps({'error': 6, 'message': 'Wrong id of ladder'})

			# Нет прав на удаление отзыва
			if user['admin'] < 5:
				return dumps({'error': 7, 'message': 'No access rights'})

			db['feedback'].remove(feedback['_id'])

			return dumps({'error': 0})

# Поиск
		elif x['method'] == 'search':
			mes = errors(x, (
				('token', False, str),
				('cont', True, str),
			))
			if mes: return mes

			# Пустой запрос
			if not x['cont']:
				return dumps({'error': 6, 'message': 'Empty request'})

			# Новости
			news = []
			for i in db['news'].find({}, {'_id': False, 'name': True, 'description': True, 'cont': True, 'comment': True, 'id': True}):
				if any(x['cont'] in j.lower() for j in (i['name'], i['description'], i['cont'])) or any(x['cont'] in j.lower() for j in i['comment']):
					news.append(i)

			# Пользователи
			users = []
			for i in db['users'].find({}, {'_id': False, 'name': True, 'surname': True, 'mail': True, 'description': True, 'id': True, 'login': True}):
				if any(x['cont'] in j.lower() for j in (i['name'], i['surname'], i['mail'], i['description'], i['login'])):
					users.append(i)

			# Ледеры
			ladders = []
			for i in db['ladders'].find({}, {'_id': False, 'name': True, 'description': True, 'comment': True, 'tags': True, 'id': True, 'steps.complete': True}):
				if any(x['cont'] in j.lower() for j in (i['name'], i['description'])) or any(x['cont'] in j.lower() for j in i['tags']) or any(x['cont'] in j.lower() for j in i['comment']):

					ladders.append(i)

			if len(ladders):
				print(ladders)

				for i in range(len(ladders)):
					ladders[i]['complete'] = sum(len(j['complete']) for j in ladders[i]['steps'])

				ladders.sort(key=lambda i: i['complete'], reverse=-1)

				for i in range(len(ladders)):
					del ladders[i]['steps']
					del ladders[i]['complete']

			# Степы
			steps = []
			filter_db = {
				'_id': False,
				'id': True,
				'steps.name': True,
				'steps.cont': True,
				'steps.theory': True,
				'steps.options': True,
				'steps.id': True,
				'steps.comment': True,
			}
			status = 3 if user['admin'] < 5 else 1

			for i in db['ladders'].find({'status': {'$gte': status}}, filter_db):
				for j in i['steps']:
					if any(x['cont'] in u.lower() for u in (j['name'], j['cont'], j['theory'])) or any(x['cont'] in u.lower() for u in j['comment']) or any(x['cont'] in u.lower() for u in j['options']):
						j['ladder'] = i['id']
						steps.append(j)

			res = {
				'error': 0,
				'news': news,
				'users': users,
				'ladders': ladders,
				'steps': steps,
				'comments': [],
			}

			return dumps(res)

# Добавить сообщение
		elif x['method'] == 'space.add':
			mes = errors(x, (
				('token', False, str),
				('id', True, int),
				('cont', True, str),
			))
			if mes: return mes

			study = db['study'].find_one({'id': x['id']})

			if not study:
				return dumps({'error': 6, 'message': 'Training session does not exsist'})

			if not x['cont']:
				return dumps({'error': 7, 'message': 'Empty message'})

			if len(study['messages']):
				id = study['messages'][-1]['id'] + 1
			else:
				id = 1

			out = study['student'] == user['id']

			x['cont'] = reimg(x['cont'], 'spaces', x['id'], id)

			study['messages'].append({
				'id': id,
				'out': out,
				'cont': x['cont'],
				'time': timestamp,
			})
			db['study'].save(study)

			socketio.emit('message', {
				'session': x['id'],
				'id': id,
				'out': out,
				'cont': x['cont'],
				'time': timestamp,
			}, namespace='/space')

			return dumps({'error': 0})

# Получение категорий
# 		elif x['method'] == 'categories.gets':
# 			categories = []
# 			for i in db['categories'].find().sort('priority', -1): #{"$unwind": "$Applicants"}
# 				# print('!!!', i)
# 				# time.sleep(2)
# 				del i['_id']

# 				categories.append(i)
# 			return dumps(categories)

# db['categories'].insert({
# 	'id': 1,
# 	'parent': 0,
# 	'name': 'Раздел 1',
# 	'url': 'art',
# 	'priority': 50,
#	'plus': 'ladder',
# })

		else:
			return dumps({'error': 2, 'message': 'Wrong method'})

	# Серверная ошибка
	except Exception as e:
		print(e)
		return dumps({'error': 1, 'message': 'Server error'})


@socketio.on('connect', namespace='/teach')
def test_connect():
	emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('wait', namespace='/teach')
def wait_teach(mes):
	for i in db['teachers'].find({'user': mes['id']}):
		i['time'] = time.time()
		db['teachers'].save(i)

# Убрать в общее пространство
@socketio.on('cancel', namespace='/teach')
def cancel_teach(mes):
	study = db['study'].find_one({'id': mes['id']})
	study['status'] = 5
	db['study'].save(study)

	socketio.emit('cancel', {
		'id': mes['id'],
	}, namespace='/space')

@socketio.on('cancel', namespace='/main')
def cancel_teach(mes):
	study = db['study'].find_one({'id': mes['id']})
	study['status'] = 5
	db['study'].save(study)

	socketio.emit('cancel', {
		'id': mes['id'],
	}, namespace='/space')

@socketio.on('stop_yes', namespace='/space')
def stop_yes(mes):

	#

	study = db['study'].find_one({'id': mes['id']})

	users = db['users'].find_one({'id': study['teacher']})
	users['balance'] += int(study['price'] * 0.9)
	db['users'].save(users)

	ladder = db['ladders'].find_one({'id': study['ladder']})
	steps_all = [i['id'] for i in ladder['steps']]
	step_num = steps_all.index(study['step'])

	users = db['users'].find_one({'id': ladder['steps'][step_num]['user']})
	users['balance'] += int(study['price'] * 0.03)
	db['users'].save(users)

	ladder['steps'][step_num]['total'] += int(study['price'] * 0.03)
	db['ladders'].save(ladder)

	#

	socketio.emit('stop_yes', {
		'id': mes['id'],
	}, namespace='/space')

@socketio.on('stop_no', namespace='/space')
def stop_no(mes):
	socketio.emit('stop_no', {
		'id': mes['id'],
	}, namespace='/space')

@socketio.on('student_accept', namespace='/space')
def student_accept(mes):
	study = db['study'].find_one({'id': mes['id']})
	study['status'] = 19 # 14
	db['study'].save(study)

	#

	users = db['users'].find_one({'id': study['student']})
	users['balance'] -= study['price']
	db['users'].save(users)

	#

	socketio.emit('accept_to_teacher', {
		'id': mes['id'],
	}, namespace='/space')

@socketio.on('student_cancel', namespace='/space')
def student_cancel(mes):
	study = db['study'].find_one({'id': mes['id']})
	study['status'] = 15
	db['study'].save(study)

	socketio.emit('cancel_to_teacher', {
		'id': mes['id'],
	}, namespace='/space')

@socketio.on('public', namespace='/reg')
def reg_private(mes):
	user_id = db['tokens'].find_one({'token': mes['token']})['id']
	users = db['users'].find_one({'id': user_id})

	users['public'] = mes['key']
	db['users'].save(users)

@socketio.on('password', namespace='/auth')
def check_password(mes):
	users = db['users'].find_one({'id': mes['id'], 'password': mes['cont']})
	res = True if users else False

	socketio.emit('result', {
		'id': mes['id'],
		'cont': res,
	}, namespace='/auth')

@socketio.on('online', namespace='/main')
def online_users(mes):
	global thread
	with thread_lock:
		if thread is None:
			thread = socketio.start_background_task(target=background_thread)

	x = db['online'].find_one({'user': mes['id']})
	if x:
		x['time'] = time.time()
		db['online'].save(x)
	else:
		y = db['users'].find_one({'id': mes['id']}, {'_id': False, 'steps': True})
		x = {
			'user': mes['id'],
			'time': time.time(),
			'steps': y['steps'],
		}
		db['online'].insert_one(x)

		socketio.emit('user_add', {
			'id': mes['id'],
		}, namespace='/study')


if __name__ == '__main__':
	socketio.run(app, debug=True)


def background_thread():
	while True:
		timestamp = time.time()

		# Удалять старые объявления об обучении
		for i in db['teachers'].find():
			if timestamp - i['time'] > 60:
				socketio.emit('remove', {
					'ladder': i['ladder'],
					'step': i['step'],
					'user': i['user'],
				}, namespace='/study')

				db['teachers'].remove(i['_id'])

		# Ученик не подтвердил вовремя начало урока
		for i in db['study'].find({'status': 1}):
			if timestamp - i['time'] > 60:
				socketio.emit('student_cancel', {
					'id': i['id'],
				}, namespace='/study')

				i['status'] = 16
				db['study'].save(i)

		# Если учитель не открыл вовремя урок
		for i in db['study'].find({'status': 0}):
			if timestamp - i['time'] > 60:
				i['status'] = 11
				db['study'].save(i)

				for j in db['teachers'].find({'user': i['teacher']}):
					socketio.emit('remove', {
						'ladder': j['ladder'],
						'step': j['step'],
						'user': j['user'],
					}, namespace='/study')

					db['teachers'].remove(j['_id'])

				socketio.emit('timeout', {
					'id': i['id'],
				}, namespace='/space')

				socketio.emit('timeout', {
					'id': i['teacher'],
				}, namespace='/teach')

		# Если долго не было сообщений
		for i in db['study'].find({'status': {'$in': (14, 18, 19)}}):
			# 5 минут от пользователей
			if len(i['messages']):
				if timestamp - i['messages'][-1]['time'] > 300:
					i['status'] = 7 if i['messages'][-1]['out'] else 6
					db['study'].save(i)

					socketio.emit('time', {
						'id': i['id'],
					}, namespace='/space')
			else:
				if timestamp - i['time'] > 300:
					i['status'] = 13
					db['study'].save(i)

					socketio.emit('time', {
						'id': i['id'],
					}, namespace='/space')

			# 25 минут с начала урока
			if timestamp - i['time'] > 1500:
				i['status'] = 12
				db['study'].save(i)

				socketio.emit('time', {
					'id': i['id'],
				}, namespace='/space')

		# Ожидание транзакций
		# for i in db['study'].find({'status': 14}):
		# 	url = 'http://40.67.212.77:3000/searchlogs/%s/latest/%s/%s' % (i['height'], CONTRACT_ADDRESS, TOPIC_LESSON_PREPARED)
		# 	print('!!!', url)
		# 	x = loads(requests.get(url).text)

		# 	wallet = db['users'].find_one({'id': i['teacher']})['public']
				
		# 	if len(x['data']):
		# 		req = {
		# 			'id': i['id'],
		# 			'teacher': wallet,
		# 			'price': i['price'],
		# 		}

		# 		socketio.emit('transaction_teacher', req, namespace='/space')

		# 		i['status'] = 18
		# 		db['study'].save(i)

		# for i in db['study'].find({'status': 18}):
		# 	url = 'http://40.67.212.77:3000/searchlogs/%s/latest/%s/%s' % (i['height'], CONTRACT_ADDRESS, TOPIC_LESSON_STARTED)
		# 	print('!!!', url)
		# 	x = loads(requests.get(url).text)
				
		# 	if len(x['data']):
		# 		req = {
		# 			'id': i['id'],
		# 		}

		# 		socketio.emit('transaction_student', req, namespace='/space')

		# 		i['status'] = 19
		# 		db['study'].save(i)

		# Удаление онлайн пользователей
		for i in db['online'].find({'time': {'$lt': timestamp - 15}}):
			socketio.emit('user_remove', {
				'id': i['user'],
			}, namespace='/study')

			db['online'].remove(i['_id'])

		time.sleep(15)