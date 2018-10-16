from flask import render_template, session, Markup, request
from app import app, LINK, get_preview

from requests import post
from json import loads
import markdown

@app.route('/user/<int:id>')
@app.route('/user/<int:id>/')
def user(id):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	req = {
		'method': 'users.get',
		'ip': ip,
		'id': id,
	}

	if 'token' in session:
		req['token'] = session['token']

	users = loads(post(LINK, json=req).text)

	if users['error']:
		return render_template('message.html', cont=users['message'])

	users = users['user']
	users['description'] = Markup(markdown.markdown(users['description']))

	return render_template('user.html',
		title = '',
		description = '',
		tags = [],
		url = 'user/%d' % id,

		user = user,

		LINK = LINK,
		preview = get_preview,
		round = round,

		users = users,
	)