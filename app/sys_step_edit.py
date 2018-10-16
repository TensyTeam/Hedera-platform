from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import json

@app.route('/sys_step_edit', methods=['POST'])
def sys_step_edit():
	ip = request.remote_addr

	x = request.form
	ladder = request.args.get('ladder')
	step = request.args.get('step')

	req = {
		'method': 'step.edit',
		'token': session['token'],
		'ip': ip,
		'ladder': int(ladder),
		'step': int(step),
		'name': x['name'],
		'cont': x['cont'],
		'options': [i.replace('\r', '').replace('\n', '<br>') for i in x['options'].split(';') if i],
	}

	step_list = json.loads(post(LINK, json={
				'method': 'step.gets',
				'token': session['token'],
				'ip': ip,
				'ladder': int(ladder),
			}).text)['steps']

	if 'after' in x:
		if x['after'] != '-1':
			req['id'] = int(x['after'])
			req['after'] = True
		else:
			req['id'] = step_list[0][0]
			req['after'] = False
	elif 'before' in x:
		if x['before'] != '-1':
			req['id'] = int(x['before'])
			req['after'] = False
		else:
			req['id'] = step_list[-1][0]
			req['after'] = True

	req = json.loads(post(LINK, json=req).text)

	if not req['error']:
		return redirect(LINK + 'admin/edit/step/' + ladder + '/' + step)
	else:
		return render_template('message.html', cont=req['message'])