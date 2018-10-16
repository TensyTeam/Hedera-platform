from flask import render_template, session, redirect, request
from app import app, LINK

from requests import post
from json import loads

@app.route('/admin/add/ladder')
@app.route('/admin/add/ladder/')
def add_ladder():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	url = 'admin/add/ladder'

	if 'token' in session:
		return render_template('ladder_add.html',
			title = 'Add ladder',
			description = 'Admin panel: add ladder',
			tags = ['admin panel', 'add ladder'],
			url = url,

			user = user,

			LINK = LINK,
		)
	else:
		return redirect(LINK + 'login?url=' + url)