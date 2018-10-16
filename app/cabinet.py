from flask import render_template, session, request, redirect
from app import app, LINK, get_preview

from requests import post
from json import loads

@app.route('/cabinet')
@app.route('/cabinet/')
def cabinet():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	x = request.args.get('url')

	if 'token' in session:
		user['description'] = user['description'].replace('<br>', '\r\n')

		return render_template('cabinet.html',
			title = 'Profile',
			description = 'Profile, personal area, settings, account',
			tags = ['profile', 'personal area', 'settings', 'account'],
			url = 'cabinet',

			user = user,

			LINK = LINK,
			preview = get_preview,

			loc = x if x else 'cabinet',
			token = session['token'],
		)

	else:
		return redirect(LINK + 'login?url=cabinet')