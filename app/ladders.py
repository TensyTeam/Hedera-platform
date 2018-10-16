from flask import render_template, session, request
from app import app, LINK, get_preview

from requests import post
from json import loads

@app.route('/ladder')
@app.route('/ladder/')
@app.route('/ladders')
@app.route('/ladders/')
@app.route('/ladders/<sub>')
def ladders(sub=''):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	title = 'Ladders' #change with category
	tags = ['ladders', 'courses']

	req = {
		'method': 'ladders.gets',
		'ip': ip,
		# 'category': subcategory if subcategory else category,
	}
	if 'token' in session:
		req['token'] = session['token']

	ladders = loads(post(LINK, json=req).text)['ladders']

	return render_template('ladders.html',
		title = title,
		description = '',
		tags = tags,
		url = 'ladders/' + sub,

		user = user,

		LINK = LINK,
		preview = get_preview,

		ladders = ladders,
	)