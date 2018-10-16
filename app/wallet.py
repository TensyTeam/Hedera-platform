from flask import render_template, session, request, redirect
from app import app, LINK, get_preview

from requests import post
from json import loads
from time import strftime, gmtime

def time(x):
	return strftime('%d.%m.%Y %H:%M:%S', gmtime(x))

@app.route('/wallet')
@app.route('/wallet/')
def wallet():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	if 'token' in session:
		return render_template('wallet.html',
			title = 'Wallet',
			description = 'Wallet, tokens, transaction history',
			tags = ['wallet', 'tokens', 'transaction history'],
			url = 'wallet',

			user = user,

			LINK = LINK,
			preview = get_preview,
			time = time,
		)

	else:
		return redirect(LINK + 'login?url=wallet')