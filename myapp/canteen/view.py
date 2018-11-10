from . import canteen
from ..extensions import csrf
from flask_wtf import FlaskForm
from wtforms import TextField
from flask import Flask, render_template, session, redirect, url_for
from flask_login import login_required
from flask import jsonify
from flask import request
from flask import Response
from flask import json
import os, sys
from .db_utils import *
from werkzeug.datastructures import ImmutableMultiDict
import sqlite3
from .checksum import *
import requests
import hashlib
import time
import qrcode
import socket
import base64
from io import BytesIO

@canteen.route('/customer_form')
def customer_form():
	return render_template('customer/customer_form.html')

@canteen.route('/owner_form')
def owner_form():
	return render_template('canteen_owner/owner_form.html')

@canteen.route('customer/customer_form_submit',methods=['POST'])
@csrf.exempt
def parse_customer_form():
	data = dict()
	data['Gender'] = request.form['gender']
	data['Semester'] = request.form['semester']
	data['Department'] = request.form['department']
	data['User_name'] = session['username']
	data['Social_id'] = session['social_id'] #110058041200100630475
	data['Email'] = session['email_address']
	session['User_id'] = insert_customer('canteen', data)
	return str(session)

@canteen.route('/owner_form_submit',methods=['POST'])
@csrf.exempt
def parse_owner_form():
	data = dict()
	data['Owner_name'] = session['username']
	data['Social_id'] = session['social_id'] #110058041200100630475
	data['Email'] = session['email_address']
	data['Canteen_name'] = request.form['canteen_name']
	session['Owner_id'] = insert_owner('canteen', data)
	return str(session)

@canteen.route('/selectpayment/')
def selectpayment():
	return render_template('payment/payment.html')

@canteen.route('/payment/', methods=['POST','GET'])
def payment():
	if request.method=='POST':
		MERCHANT_KEY = 'tG89dKDNQQWsrWjO';
		data_dict = {
			'MID':'SEB5St30591402404816',
			'ORDER_ID':'seb5336',
			'TXN_AMOUNT':request.form['TXN_AMOUNT'],
			'CUST_ID':request.form['CUST_ID'],
			'INDUSTRY_TYPE_ID':'Retail',
			'WEBSITE':'WEBSTAGING',
			'CHANNEL_ID':'WEB',
			'CALLBACK_URL':'http://localhost:5000/payment.status'
		}
		param_dict = data_dict  
		param_dict['CHECKSUMHASH'] =generate_checksum(data_dict, MERCHANT_KEY)
		return render_template('payment/redirect.html',data=param_dict)

@canteen.route('/payment.status/',methods=['POST','GET'])
def status():
	if request.method=='POST' or request.method=='GET':
		# Load request details
		# Assume request is:
		data = {'item_ids':[214, 223, 250, 254, 261, 267, 268, 278, 279, 285, 291, 292],
				'quantity':[27, 3, 25, 25, 13, 39, 28, 48, 19, 23, 42, 42],
				'User_id':366}
		
		cost = get_cost('canteen', data['item_ids'], data['quantity'])
		# hash = hashlib.sha512((str(data)+str(time.time())).encode('utf-8')).hexdigest()
		hash = 'aba6a632901803216855a180d6221622481064b4'
		# Update Purchases, Transactions
		
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		ip_addr = (s.getsockname()[0])
		qr_code = ("http://"+ip_addr+":8000/canteen_owner/qr/"+hash)
		# qr_code = ("http://"+ip_addr+":8000/customer/index.html")
		img = qrcode.make(qr_code).get_image()
		
		buffered = BytesIO()
		img.save(buffered, format="JPEG")
		img_str = base64.b64encode(buffered.getvalue()).decode()
		print(img_str)
		return render_template("payment/qr.html", img={'base':img_str})

@canteen.route('/canteen_owner/qr/<hash>')
def canteen_owner_process_order_hash(hash):
	return render_template('canteen_owner/order.html', data=get_order('canteen', hash=hash))	

@canteen.route('/canteen_owner/id/<int:id>')
def canteen_owner_process_order_id(id):
	return render_template('canteen_owner/order.html', data=get_order('canteen', id=id))	

@canteen.route('/canteen_owner/typography.html')
def canteen_owner_typography():
	return render_template('canteen_owner/typography.html')

@canteen.route('/canteen_owner/icons.html')
def canteen_owner_icons():
	return render_template('canteen_owner/icons.html')

@canteen.route('/canteen_owner/tables.html')
def canteen_owner_tables():
	return render_template('canteen_owner/tables.html', data = get_canteen_details('canteen'))

@canteen.route('/canteen_owner/parent_template.html')
def canteen_owner_parent_template():
	return render_template('canteen_owner/parent_template.html')

@canteen.route('/canteen_owner/notifications.html')
def canteen_owner_notifications():
	return render_template('canteen_owner/notifications.html')

@canteen.route('/canteen_owner/charts.html')
def canteen_owner_charts():
	return render_template('canteen_owner/charts.html', gender_data = get_user_details('canteen', 'Users', 'Gender'), dept_data = get_user_details('canteen', 'Users', 'Department'), sem_data = get_user_details('canteen', 'Users', 'Semester'))

@canteen.route('/canteen_owner/page-lockscreen.html')
def canteen_owner_page_lockscreen():
	return render_template('canteen_owner/page-lockscreen.html')

@canteen.route('/canteen_owner/page-login.html')
def canteen_owner_page_login():
	return render_template('canteen_owner/page-login.html')

@canteen.route('/canteen_owner/page-profile.html')
def canteen_owner_page_profile():
	return render_template('canteen_owner/page-profile.html')

@canteen.route('/canteen_owner/panels.html')
def canteen_owner_panels():
	return render_template('canteen_owner/panels.html')

@canteen.route('/canteen_owner/elements.html')
def canteen_owner_elements():
	return render_template('canteen_owner/elements.html', data = get_items('Items', 'canteen'))

@canteen.route('/canteen_owner/index.html')
def canteen_owner_owner_index():
	return render_template('canteen_owner/index.html')

@canteen.route('/customer/items')
def items_index():
	#table_name = 'Items'
	# cursor = get_conn('canteen')
	return render_template('customer/oldindex.html', data = get_items('Items', 'canteen'))


#Changed 
@canteen.route('/customer/typography.html')
def customer_typography():
	return render_template('customer/typography.html', data = get_items('Items', 'canteen'))

@canteen.route('/customer/icons.html')
def customer_icons():
	return render_template('customer/icons.html')

@canteen.route('/customer/tables.html')
def customer_tables():
	return render_template('customer/tables.html')

@canteen.route('/customer/parent_template.html')
def customer_parent_template():
	return render_template('customer/parent_template.html')

@canteen.route('/customer/notifications.html')
def customer_notifications():
	return render_template('customer/notifications.html')

@canteen.route('/customer/charts.html')
def customer_charts():
	return render_template('customer/charts.html')

@canteen.route('/customer/page-lockscreen.html')
def customer_page_lockscreen():
	return render_template('customer/page-lockscreen.html')

@canteen.route('/customer/page-login.html')
def customer_page_login():
	return render_template('customer/page-login.html')

@canteen.route('/customer/page-profile.html')
def customer_page_profile():
	return render_template('customer/page-profile.html')

@canteen.route('/customer/panels.html')
def customer_panels():
	return render_template('customer/panels.html')

@canteen.route('/customer/elements.html')
def customer_elements():
	return render_template('customer/elements.html')

@canteen.route('/customer/index.html')
@login_required
def customer_owner_index():
	# print(session['username'])
	print(session)
	return render_template('customer/index.html')

@canteen.route('/')
@login_required
def index():
	return redirect(url_for('canteen.customer_owner_index'))


###End changed

##test
@canteen.route('/customer/test',methods=['POST'])
def test():
	data = json.loads(request.data)
	print(data)
	return "{status: 200, msg:ok}"

if __name__ == "__main__":
	print(os.path.abspath(__file__))
	print(os.path.dirpath(__file__))
	canteen = create_canteen()
	canteen.jinja_env.cache = {}
	canteen.run(debug=True, port=5000)
