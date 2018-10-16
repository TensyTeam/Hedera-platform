from flask import render_template, session, request, Markup, redirect
from app import app, LINK, get_preview

from requests import post
from json import loads
import markdown
import re

@app.route('/ladder/<int:id>')
@app.route('/ladder/<int:id>/')
def ladder(id):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	edit = request.args.get('edit')

	url = 'ladder/%d' % id
	if edit: url += '?edit=1'

	if edit and 'token' not in session:
		return redirect(LINK + 'login?url=' + url)

	req = {
		'method': 'ladders.get',
		'ip': ip,
		'id': id,
	}
	if 'token' in session:
		req['token'] = session['token']

	req = loads(post(LINK, json=req).text)

	if req['error']:
		return render_template('message.html', cont=req['message'])

	ladder = req['ladder']

	if not edit:
		ladder['description'] = Markup(markdown.markdown(ladder['description']))
	else:
		ladder['description'] = ladder['description'].replace('<br>', '\r\n')

	req2 = {
		'method': 'step.gets',
		'ip': ip,
		'ladder': id,
	}
	if 'token' in session:
		req2['token'] = session['token']

	steps = loads(post(LINK, json=req2).text)

	return render_template('ladder_edit.html' if edit and user['admin'] >= 5 else 'ladder.html',
		title = ladder['name'],
		description = re.sub(r'\<[^>]*\>', '', ladder['description']),
		tags = ladder['tags'],
		url = url,

		user = user,

		LINK = LINK,
		preview = get_preview,
		enumerate = enumerate,
		str = str,

		ladder = ladder,
		step = req['step'],
		num = req['num'],
		experts = req['experts'],
		steps = steps['steps'],
		user_steps = req['steps'],
	)