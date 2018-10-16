from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import json

@app.route('/sys_feedback_delete')
def sys_feedback_delete():
	ip = request.remote_addr

	id = int(request.args.get('id'))

	req = json.loads(post(LINK, json={
		'method': 'feedback.delete',
		'token': session['token'],
		'ip': ip,
		'id': id,
	}).text)

	id -= id != 0

	if not req['error']:
		return redirect(LINK + 'admin') ## + str(id)
	else:
		return render_template('message.html', cont=req['message'])