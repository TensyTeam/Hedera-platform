from flask import Flask, redirect
import os
import re
from params import *

app = Flask(__name__)
app.config.from_object('config')

def get_url(url, rep='competions'):
	if not url: url = rep
	if url == 'index': url = ''
	return redirect(LINK + url)

def get_preview(url, num=0):
	url = '/static/load/' + url + '/'
	for i in os.listdir('app' + url):
		if re.search(r'^' + str(num) + '\.', i):
			return url + i
	return url + '0.png'

from app import api

from app import index
from app import admin
from app import news
from app import news_add
from app import search

from app import login
from app import cabinet
from app import wallet
from app import password
from app import token

from app import codex
from app import feedback
from app import about
from app import news_all

from app import errors

from app import sys_sign_up
from app import sys_sign_in
from app import sys_sign_out
from app import sys_profile_edit
from app import sys_ladder_add
from app import sys_ladder_edit
from app import sys_step_add
from app import sys_step_edit
from app import sys_step_more
from app import sys_step_delete
from app import sys_step_check
from app import sys_feedback
from app import sys_feedback_delete
from app import sys_news_add
from app import sys_news_edit
from app import sys_news_delete
from app import sys_study
from app import sys_space
from app import sys_study_stop
from app import sys_user_block

from app import user
from app import members

from app import ladder
from app import ladders
from app import ladder_add
from app import step
from app import step_add
from app import step_edit
from app import study
from app import step_end

from app import teach
from app import wait
from app import space