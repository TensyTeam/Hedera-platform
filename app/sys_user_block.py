from flask import session, request, redirect, render_template
from app import app, LINK

from requests import post
import json

@app.route('/sys_user_block/<int:id>')
@app.route('/sys_user_block/<int:id>/')
def sys_user_block(id):
	ip = request.remote_addr

	if 'token' not in session:
		return redirect(LINK + 'login?url=user/' + str(id))

	req = json.loads(post(LINK, json={
		'method': 'users.block',
		'token': session['token'],
		'ip': ip,
		'id': id,
	}).text)

	if req['error']:
		return render_template('message.html', cont=req['message'])
	
	return redirect(LINK + 'members')