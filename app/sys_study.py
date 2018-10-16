from flask import render_template, session, request, Markup, redirect
from app import app, LINK

from requests import post
from json import loads

@app.route('/sys_study')
@app.route('/sys_study/')
def sys_study():
	ip = request.remote_addr

	if 'token' in session:
		req = loads(post(LINK, json={
			'method': 'study.start',
			'token': session['token'],
			'ip': ip,
			'ladder': int(request.args.get('ladder')),
			'step': int(request.args.get('step')),
			'teacher': int(request.args.get('user')),
		}).text)

		if req['error']:
			return render_template('message.html', cont=req['message'])

		src = LINK + 'space/' + str(req['id'])
		return redirect(src)
	else:
		return redirect(LINK + 'login?url=' + url)