from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import json

@app.route('/sys_step_more', methods=['POST'])
def sys_step_more():
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
		'theory': x['theory'],
		'answers': [int(i) for i in x if x[i] == '1'],
	}

	req = json.loads(post(LINK, json=req).text)

	if not req['error']:
		href = request.args.get('href')
		if href:
			return redirect(LINK + 'ladder/' + ladder + '/?edit=1#' + step)
		else:
			return redirect(LINK + 'ladder/' + ladder + '/question/' + step)
	else:
		return render_template('message.html', cont=req['message'])