from flask import render_template, session, redirect, request
from app import app, LINK, get_preview

from requests import post
from json import loads

@app.route('/ladder/<int:ladder>/study/<int:step>')
@app.route('/ladder/<int:ladder>/study/<int:step>/')
def study(ladder, step):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	if 'token' in session:
		req = loads(post(LINK, json={
			'method': 'study.gets',
			'token': session['token'],
			'ip': ip,
			'ladder': ladder,
			'step': step,
		}).text)

		if req['error']:
			return render_template('message.html', cont=req['message'])

		return render_template('study.html',
			title = 'Study',
			description = '',
			tags = ['study', 'ladder'],
			url = 'ladder/%d/study/%d' % (ladder, step),

			user = user,

			LINK = LINK,
			preview = get_preview,

			ladder = ladder,
			step = step,
			bot = req['bot'], # Markup(markdown.markdown(loads(post(LINK, json={'method': 'step.get', 'ladder': ladder, 'step': step}).text)['step']['theory'])),
			teachers = req['teachers'],
			users = req['users'],
			online = req['online'],
			error = request.args.get('error'),
		)
	else:
		return redirect(LINK + 'login?url=ladder/%d/study/%d' % (ladder, step))