from flask import render_template, session, request, Markup, redirect
from app import app, LINK, get_preview

from requests import post
from json import loads
import markdown
import re

@app.route('/ladder/<int:ladder>/question/<int:step>')
@app.route('/ladder/<int:ladder>/question/<int:step>/')
def step(ladder, step):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	if 'token' not in session:
		return redirect(LINK + 'login?url=ladder/' + str(ladder))

	edit = request.args.get('edit')

	url = 'ladder/%d/question/%d' % (ladder, step)
	if edit: url += '?edit=1'

	req = loads(post(LINK, json={
		'method': 'step.get',
		'token': session['token'],
		'ip': ip,
		'ladder': ladder,
		'step': step,
	}).text)

	print(req)

	if req['error'] in (8,):
		return redirect(LINK + 'ladder/' + str(ladder))

	if edit and user['admin'] < 5 and user['id'] != req['step']['user']:
		return redirect(LINK + url)

	if 'step' not in req:
		return render_template('message.html', cont='Страница не существует!')

	if not edit:
		req['step']['cont'] = Markup(req['step']['cont'])
		req['step']['theory'] = Markup(req['step']['theory'])
		for i in range(len(req['step']['options'])):
			req['step']['options'][i] = Markup(markdown.markdown(req['step']['options'][i]))
	else:
		for i in range(len(req['step']['options'])):
			req['step']['options'][i] = req['step']['options'][i].replace('<br>', '\r\n')

	steps = loads(post(LINK, json={
		'method': 'step.gets',
		'token': session['token'],
		'ip': ip,
		'ladder': ladder,
	}).text)

	return render_template('step_edit.html' if edit and (user['id'] == req['step']['user'] or user['admin'] >= 5) else 'step.html',
		title = req['step']['name'],
		description = re.sub(r'\<[^>]*\>', '', req['step']['cont']) + '\n' + '; '.join([re.sub(r'\<[^>]*\>', '', i) for i in req['step']['options']]),
		tags = req['tags'],
		url = url,

		user = user,

		LINK = LINK,
		preview = get_preview,
		enumerate = enumerate,
		str = str,

		step = req['step'],
		steps = steps['steps'],
		ladder = ladder,
		id = step,
		author = req['author'],
		complete = req['complete'],
		spaces = req['spaces'],
	)