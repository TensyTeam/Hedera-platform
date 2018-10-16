from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import re, json, base64

@app.route('/sys_ladder_edit', methods=['POST'])
def sys_ladder_edit():
	ip = request.remote_addr

	x = request.form
	id = request.args.get('id')

	req = {
		'method': 'ladders.edit',
		'token': session['token'],
		'ip': ip,
		'id': int(id),
		'name': x['name'],
		# 'category': int(x['category']),
		'tags': [i.strip() for i in re.compile(r'[a-zA-Zа-яА-Я ]+').findall(x['tags'])],
		'description': x['description'].replace('\r', '').replace('\n', '<br>'),
	}

	if 'preview' in request.files:
		y = request.files['preview'].stream.read()
		y = str(base64.b64encode(y))[2:-1]
		req['preview'] = y
		req['file'] = request.files['preview'].filename

	req = json.loads(post(LINK, json=req).text)

	if not req['error']:
		return redirect(LINK + 'ladder/' + id)
	else:
		return render_template('message.html', cont=req['message'])