from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import re, json, base64

@app.route('/sys_news_add', methods=['POST'])
def sys_news_add():
	ip = request.remote_addr

	x = request.form

	req = {
		'method': 'news.add',
		'token': session['token'],
		'ip': ip,
		'name': x['name'],
		'description': x['description'].replace('\r', '').replace('\n', '<br>'),
		'cont': x['cont'],
	}

	if 'preview' in request.files:
		y = request.files['preview'].stream.read()
		y = str(base64.b64encode(y))[2:-1]
		req['preview'] = y
		req['file'] = request.files['preview'].filename

	req = json.loads(post(LINK, json=req).text)

	if not req['error']:
		return redirect(LINK + 'news/' + str(req['id']))
	else:
		return render_template('message.html', cont=req['message'])