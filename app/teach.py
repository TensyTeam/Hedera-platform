from flask import render_template, session, request, redirect
from app import app, LINK

from requests import post
from json import loads

@app.route('/teach')
@app.route('/teach/')
def teach():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	if 'token' in session:
		not_empty = False

		for ladder in user['ladders']:
			req = loads(post(LINK, json={'method': 'ladders.get', 'ip': ip, 'id': int(ladder), 'token': session['token']}).text)['ladder']
			for step in range(len(user['ladders'][ladder]['steps'])):
				id = user['ladders'][ladder]['steps'][step]
				name = ''
				price = 0
				checked = False

				not_empty = True

				for i in req['steps']:
					if i['id'] == id:
						name = i['name']
						price = i['price']

				for i in user['steps']:
					if i['ladder'] == int(ladder) and i['step'] == id:
						checked = True
						price = i['price']

				user['ladders'][ladder]['steps'][step] = {
					'id': id,
					'name': name,
					'price': price,
					'checked': checked,
				}

		return render_template('teach.html',
			title = 'Teach',
			description = 'teach',
			tags = ['teach'],
			url = 'teach',

			user = user,

			LINK = LINK,

			error = request.args.get('error'),
			not_empty = not_empty,
		)

	else:
		return redirect(LINK + 'login?url=teach')