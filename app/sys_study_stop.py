from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import json

@app.route('/sys_study_stop/<int:id>')
@app.route('/sys_study_stop/<int:id>/')
def sys_study_stop(id):
	ip = request.remote_addr

	status = int(request.args.get('status'))

	req = {
		'method': 'study.stop',
		'token': session['token'],
		'ip': ip,
		'id': id,
		'status': status,
	}

	req = json.loads(post(LINK, json=req).text)

	if req['error']:
		return render_template('message.html', cont=req['message'])

	return redirect(LINK + 'ladder/' + str(req['ladder']) + '/question/' + str(req['step']))