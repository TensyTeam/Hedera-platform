from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import json

@app.route('/token')
@app.route('/token/')
def token():
	ip = request.remote_addr
	user = json.loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}
	url = 'token'

	if 'token' in session:
		return render_template('token.html',
			title = 'Authorization',
			description = '',
			tags = ['authorization', 'token'],
			url = url,

			user = user,

			LINK = LINK,
			
			without_menu = True,
			
			link = request.args.get('url')
		)
	else:
		return redirect(LINK + 'login?url=' + url)