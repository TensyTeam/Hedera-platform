from flask import render_template, session, request, Markup, redirect
from app import app, LINK, get_preview

from requests import post
from json import loads
import markdown
import re
from time import strftime, gmtime

def time(x):
	return strftime('%d.%m.%Y %H:%M:%S', gmtime(x))

@app.route('/news/<int:id>')
@app.route('/news/<int:id>/')
def news(id):
	ip = request.remote_addr
	user = loads(post(LINK, json={'method': 'users.get', 'ip': ip, 'id': session['id']}).text)['user'] if 'id' in session else {'id': 0, 'admin': 2}

	edit = request.args.get('edit')

	url = 'news/%d' % id
	if edit: url += '?edit=1'

	if edit and 'token' not in session:
		return redirect(LINK + 'login?url=' + url)

	req = {
		'method': 'news.get',
		'ip': ip,
		'id': id,
	}
	if 'token' in session:
		req['token'] = session['token']

	new = loads(post(LINK, json=req).text)['news']

	if not edit:
		new = dict(new)
		new['description'] = Markup(markdown.markdown(new['description']))
		new['cont'] = Markup(new['cont'])
	else:
		new['description'] = new['description'].replace('<br>', '\r\n')

	return render_template('news_edit.html' if edit else 'news.html',
		title = new['name'],
		description = re.sub(r'\<[^>]*\>', '', new['description']),
		tags = ['news'],
		url = url,

		user = user,

		LINK = LINK,
		preview = get_preview,
		time = time,

		news = new,
	)