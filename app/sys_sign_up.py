from flask import session, request, render_template, redirect
from app import app, LINK, CAPTCHA

from requests import post
import json

@app.route('/sys_sign_up', methods=['POST'])
def signup():
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

	if not all([i in x for i in ('login', 'pass', 'name', 'surname', 'mail')]):
		return render_template('message.html', cont='3')

	req = {
		'method': 'profile.reg',
		'ip': ip,
		'login': x['login'],
		'pass': x['pass'],
		'mail': x['mail'],
		'name': x['name'],
		'surname': x['surname'],
	}

	req = json.loads(post(LINK, json=req).text)

	if not req['error']:
		session['token'] = req['token']
		session['id'] = req['id']
		return redirect(LINK + 'cabinet?url=' + request.args.get('url'))
	else:
		return render_template('message.html', cont=req['message'])