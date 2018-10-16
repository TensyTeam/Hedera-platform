from flask import session, request, render_template, redirect
from app import app, LINK, get_preview

from requests import post
from json import loads

@app.route('/search', methods=['POST'])
@app.route('/search/<cont>')
@app.route('/search/<cont>/')
def search(cont=''):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	if not cont:
		cont = request.form['search']
		return redirect(LINK + 'search/' + cont)

	if not cont:
		return render_template('message.html', cont='Здесь страница с поиском')

	req = {
		'method': 'search',
		'ip': ip,
		'cont': cont,
	}

	if 'token' in session:
		req['token'] = session['token']

	req = loads(post(LINK, json=req).text)

	if not req['error']:
		return render_template('search.html',
			title = 'Search',
			description = 'Search',
			tags = ['search'],
			url = 'search/' + cont,

			user = user,

			LINK = LINK,
			preview = get_preview,

			news = req['news'],
			users = req['users'],
			ladders = req['ladders'],
			steps = req['steps'],
			comments = req['comments'],
		)
	else:
		return render_template('message.html', cont=req['message'])