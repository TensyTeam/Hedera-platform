from flask import render_template, session, redirect, request
from app import app, LINK

from requests import post
from json import loads

@app.route('/feedback')
@app.route('/feedback/')
def feedback():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}
	link = request.args.get('url')

	return render_template('feedback.html',
		title = 'Feedback',
		description = 'Feedback & troubles',
		tags = ['feedback', 'troubles'],
		url = 'feedback',

		user = user,

		LINK = LINK,

		link = link,
	)