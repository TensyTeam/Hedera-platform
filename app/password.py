from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import json

@app.route('/password')
@app.route('/password/')
def password():
	ip = request.remote_addr
	user = json.loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}
	url = 'token'

	if 'token' in session:
		return render_template('password.html',
			title = 'Authorization',
			description = '',
			tags = ['authorization', 'password'],
			url = url,

			user = user,

			LINK = LINK,
			
			without_menu = True,

			link = request.args.get('url')
		)
	else:
		return redirect(LINK + 'login?url=' + request.args.get('url'))