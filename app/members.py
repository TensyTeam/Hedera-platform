from flask import render_template, session, request
from app import app, LINK, get_preview

from requests import post
from json import loads

@app.route('/user')
@app.route('/user/')
@app.route('/users')
@app.route('/users/')
@app.route('/members')
@app.route('/members/')
def members():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	req = {
		'method': 'members.gets',
		'ip': ip,
	}
	if 'token' in session:
		req['token'] = session['token']

	members = loads(post(LINK, json=req).text)['users']

	return render_template('members.html',
		title = 'Members',
		description = 'Users, members',
		tags = ['users', 'members'],
		url = 'members',

		user = user,

		LINK = LINK,
		preview = get_preview,

		members = members,
	)