from flask import render_template, session, redirect, request
from app import app, LINK

from requests import post
from json import loads

@app.route('/admin/add/step/<int:ladder>/<int:step>')
@app.route('/admin/add/step/<int:ladder>/<int:step>/')
@app.route('/admin/add/step/<int:ladder>')
@app.route('/admin/add/step/<int:ladder>/')
def step_add(ladder, step=None):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	url = 'admin/add/step/%d%s' % (ladder, '' if step == None else ('/' + str(step)))
	after = True if request.args.get('after') else False

	if 'token' in session:
		steps = loads(post(LINK, json={
			'method': 'step.gets',
			'token': session['token'],
			'ip': ip,
			'ladder': ladder,
		}).text)

		return render_template('step_add.html',
			title = 'Add step',
			description = 'Admin panel: add step',
			tags = ['admin panel', 'add step'],
			url = url,

			user = user,

			LINK = LINK,

			ladder = ladder,
			step = step,
			after = after,
			steps = steps['steps'],
		)
	else:
		return redirect(LINK + 'login?url=' + url)