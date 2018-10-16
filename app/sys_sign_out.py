from flask import session, request #redirect
from app import app, LINK

from requests import post

@app.route('/sys_sign_out')
def out():
	ip = request.remote_addr

	if 'token' in session:
		req ={
			'cm': 'profile.exit',
			'token': session['token'],
			'ip': ip,
		}

		post(LINK, json=req)

		session.pop('token', None)
		session.pop('id', None)

	return '<script>document.location.href = document.referrer</script>' #redirect(request.url, code=302)