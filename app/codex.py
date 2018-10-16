from flask import render_template, session, request
from app import app, LINK

from requests import post
from json import loads

@app.route('/codex')
@app.route('/codex/')
def codex():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	return render_template('codex.html',
		title = 'Codex',
		description = 'Codex',
		tags = ['codex', 'honor code'],
		url = 'codex',

		user = user,

		LINK = LINK,
	)