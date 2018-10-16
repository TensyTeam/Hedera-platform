from flask import render_template, session, request
from app import app, LINK, get_preview

from requests import post
from json import loads

@app.route('/', methods=['GET'])
@app.route('/index')
@app.route('/index/')
def index():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	return render_template('index.html',
		title = 'Main',
		description = '',
		tags = ['main page', 'tensegrity'],
		url = 'index',

		# categories = loads(post(LINK, json={'method': 'categories.gets'}).text),
		user = user,

		LINK = LINK,
		
		without_menu = True,
	)