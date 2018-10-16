from flask import session, request
from app import app, LINK

from requests import post
import json

@app.route('/sys_space', methods=['POST'])
def sys_space():
	ip = request.remote_addr

	x = request.form
	id = request.args.get('id')

	req = {
		'method': 'space.add',
		'token': session['token'],
		'ip': ip,
		'id': int(id),
		'cont': x['cont'],
	}

	json.loads(post(LINK, json=req).text)

	return ''