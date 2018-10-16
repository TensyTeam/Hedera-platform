from flask import render_template, session, Markup, request
from app import app, LINK

from requests import post
from json import loads

@app.route('/admin')
@app.route('/admin/')
def admin():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	if user['admin'] < 4:
		return render_template('message.html', cont='No access rights')

	req = {
		'method': 'feedback.gets',
		'token': session['token'],
		'ip': ip,
	}

	feedback = loads(post(LINK, json=req).text)

	for i in range(len(feedback['feedback'])):
		feedback['feedback'][i]['cont'] = Markup(feedback['feedback'][i]['cont'])

	return render_template('admin.html',
		title = 'Admin',
		description = 'Admin',
		tags = ['admin'],
		url = 'admin',

		user = user,

		LINK = LINK,

		feedback = feedback['feedback'],
	)