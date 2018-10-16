from flask import session, request, render_template, redirect
from app import app, LINK

from requests import post
import json

@app.route('/sys_news_delete')
def sys_news_delete():
	ip = request.remote_addr

	id = request.args.get('id')

	req = json.loads(post(LINK, json={
		'method': 'news.delete',
		'token': session['token'],
		'ip': ip,
		'id': int(id),
	}).text)

	if not req['error']:
		return redirect(LINK)
	else:
		return render_template('message.html', cont=req['message'])