from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import json

@app.route('/sys_step_delete')
def sys_step_delete():
	ip = request.remote_addr

	id = request.args.get('ladder')
	step = int(request.args.get('step'))
	num = request.args.get('num')

	req = {
		'method': 'step.delete',
		'token': session['token'],
		'ip': ip,
		'ladder': int(id),
		'step': step,
	}

	req = json.loads(post(LINK, json=req).text)

	if not req['error']:
		if num:
			return redirect(LINK + 'ladder/' + id + '/?edit=1#' + str(req['num']))
		else:
			return redirect(LINK + 'ladder/' + id + '/question/' + str(req['step']))
	else:
		return render_template('message.html', cont=req['message'])