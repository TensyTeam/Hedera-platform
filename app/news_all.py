from flask import render_template, session, request
from app import app, LINK, get_preview

from requests import post
from json import loads

@app.route('/news')
@app.route('/news/')
def news_all():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	return render_template('news_all.html',
		title = 'News',
		description = '',
		tags = ['news', 'tensegrity'],
		url = 'news',

		user = user,

		LINK = LINK,
		preview = get_preview,

		news = loads(post(LINK, json={'method': 'news.gets', 'ip': ip}).text)['news'],
	)