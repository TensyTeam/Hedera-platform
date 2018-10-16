from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import json

@app.route('/sys_step_add', methods=['POST'])
def sys_step_add():
	ip = request.remote_addr

	x = request.form
	ladder = request.args.get('ladder')

	req = {
		'method': 'step.add',
		'token': session['token'],
		'ip': ip,
		'ladder': int(ladder),
		'name': x['name'],
		'cont': x['cont'],
		'options': [i.replace('\r', '').replace('\n', '<br>') for i in x['options'].split(';') if i],
		'theory': '',
	}

	if 'after' in x:
		if x['after'] != '-1':
			req['id'] = int(x['after'])
			req['after'] = True
		else:
			req['id'] = json.loads(post(LINK, json={
				'method': 'step.gets',
				'token': session['token'],
				'ip': ip,
				'ladder': int(ladder),
			}).text)['steps'][0][0]
			req['after'] = False
	elif 'before' in x and x['before'] != '-1':
		req['id'] = int(x['before'])
		req['after'] = False

	req = json.loads(post(LINK, json=req).text)

	if not req['error']:
		href = request.args.get('href')
		return redirect(LINK + 'admin/edit/step/' + ladder + '/' + str(req['id']) + '?type=add' + ('&href=1' if href else ''))
	else:
		return render_template('message.html', cont=req['message'])