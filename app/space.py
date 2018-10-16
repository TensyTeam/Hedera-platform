from flask import render_template, session, request, Markup, redirect
from app import app, LINK, get_preview, PLATFORM_WALLET

from requests import post
from json import loads
import re

@app.route('/space/<int:id>')
@app.route('/space/<int:id>/')
def space(id):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	url = 'space/%d' % id

	if 'token' in session:
		req = loads(post(LINK, json={
			'method': 'study.get',
			'token': session['token'],
			'ip': ip,
			'id': id,
		}).text)

		if req['error']:
			return render_template('message.html', cont=req['message'])

		finished = req['finished']

		req = req['study']

		req['theory'] = Markup(req['theory'])

		if req['teacher']:
			for i in range(len(req['messages'])):
				req['messages'][i]['cont'] = Markup(req['messages'][i]['cont'])

		return render_template('space.html',
			title = 'Theory',
			description = re.sub(r'\<[^>]*\>', '', req['ladder_name'] + '\n' + req['step_name'] + '\n' + req['step_cont']),
			tags = ['theory'] + req['tags'],
			url = url,

			user = user,

			LINK = LINK,
			preview = get_preview,
			PLATFORM_WALLET = PLATFORM_WALLET,

			id = id,
			student = req['student'],
			teacher = req['teacher'],
			ladder = req['ladder_name'],
			step = req['step_name'],
			ladder_id = req['ladder'],
			step_id = req['step'],
			theory = req['theory'],
			cont = Markup(req['step_cont']),
			messages = req['messages'] if req['teacher'] else [],
			status = req['status'],
			price = req['price'],
			wallet = req['wallet'],
			finished = finished,
		)
	else:
		return redirect(LINK + 'login?url=' + url)