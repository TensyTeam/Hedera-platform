from flask import render_template, session, redirect, request
from app import app, LINK

from requests import post
from json import loads

@app.route('/admin/edit/step/<int:ladder>/<int:step>')
@app.route('/admin/edit/step/<int:ladder>/<int:step>/')
def step_edit(ladder, step):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}
	url = 'admin/edit/step/%d/%d' % (ladder, step)

	type = request.args.get('type')
	type = type and type == 'add'
	href = request.args.get('href')

	if 'token' not in session:
		return redirect(LINK + 'login?url=' + url)

	req = {
		'method': 'step.get',
		'token': session['token'],
		'ip': ip,
		'ladder': ladder,
		'step': step,
	}

	res = loads(post(LINK, json=req).text)

	return render_template('step_more.html',
		title = 'Edit step',
		description = 'Admin panel: edit step',
		tags = ['admin panel', 'edit step'],
		url = url,

		user = user,

		LINK = LINK,
		enumerate = enumerate,

		ladder = ladder,
		id = step,
		type = type,
		href = href,
		step = res['step'],
		author = res['author'],
	)
