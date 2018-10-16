from flask import session, request, render_template, redirect
from app import app, LINK, CAPTCHA

from requests import post
import re, json, base64

@app.route('/sys_feedback', methods=['POST'])
def sys_feedback():
	ip = request.remote_addr

	x = request.form

	req = {
		'secret': CAPTCHA,
		'response': x['g-recaptcha-response'],
		'remoteip': request.remote_addr,
	}

	y = post('https://www.google.com/recaptcha/api/siteverify', params=req).text

	if not json.loads(y)['success']:
		return render_template('message.html', cont='Wrong captcha!')

	req = {
		'method': 'feedback.add',
		'ip': ip,
		'name': x['name'],
		'cont': x['cont'],
	}
	if 'token' in session:
		req['token'] = session['token']

	req = json.loads(post(LINK, json=req).text)

	if not req['error']:
		return redirect(LINK + '/' + request.args.get('url'))
	else:
		return render_template('message.html', cont=req['message'])