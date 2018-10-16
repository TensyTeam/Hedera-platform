from flask import render_template, session, redirect, request
from app import app, LINK

from requests import post
from json import loads

@app.route('/admin/news/add')
@app.route('/admin/news/add/')
def news_add():
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}
	url = 'admin/news/add'

	if user['admin'] < 6:
		return render_template('message.html', cont='No access rights')

	return render_template('news_add.html',
		title = 'Add news',
		description = 'Add news',
		tags = ['admin', 'add news'],
		url = url,

		user = user,

		LINK = LINK,
	)