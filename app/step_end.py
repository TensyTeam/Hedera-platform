from flask import render_template, session, redirect, request
from app import app, LINK

from requests import post
from json import loads

@app.route('/ladder/<int:ladder>/question/-1')
@app.route('/ladder/<int:ladder>/question/-1/')
def step_end(ladder):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	if 'token' not in session:
		return redirect(LINK + 'login?url=ladder/' + str(ladder))

	url = 'ladder/%d/question/-1' % ladder

	return render_template('step_end.html',
		title = 'End of the ladder',
		description = 'End of the ladder',
		tags = ['end', 'ladder'],
		url = url,

		user = user,

		LINK = LINK,

		ladder = ladder,
	)