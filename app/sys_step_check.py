from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import json

@app.route('/sys_step_check', methods=['POST'])
def sys_step_check():
	ip = request.remote_addr

	x = request.form
	ladder = request.args.get('ladder')
	id = request.args.get('step')

	if 'token' not in session:
		return redirect(LINK + 'login?url=ladder/' + ladder + '/question/' + id)

	req = {
		'method': 'step.check',
		'token': session['token'],
		'ip': ip,
		'ladder': int(ladder),
		'step': int(id),
		'answers': [int(i) for i in x if x[i] == '1'],
	}

	correct = json.loads(post(LINK, json=req).text)

	if correct['error']:
		return render_template('message.html', cont=correct['message'])

	if correct['correct']:
		return redirect(LINK + 'ladder/' + ladder + '/question/' + str(correct['step']))
	else:
		return redirect(LINK + 'ladder/' + ladder + '/study/' + id + '/?error=1')