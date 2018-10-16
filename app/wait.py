from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
from json import loads

@app.route('/wait', methods=['POST'])
def wait():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	if 'token' in session:
		x = request.form

		# По степу получать, добавить цену
		step_list = []
		for i in x:
			if '-' in i:
				y = i.split('-')
				step_list.append({
					'ladder': int(y[0]),
					'step': int(y[1]),
					'price': int(x[y[0] + 'price' + y[1]]),
				})

		req = {
			'method': 'teach.start',
			'token': session['token'],
			'ip': ip,
			'steps': step_list,
		}

		req = loads(post(LINK, json=req).text)

		if not req['error']:
			return render_template('wait.html',
				title = 'Wait',
				description = 'wait',
				tags = ['wait'],
				url = 'wait',

				user = user,
				
				LINK = LINK,
			)
		else:
			return render_template('message.html', cont=req['message'])
	else:
		return redirect(LINK + 'login?url=teach')