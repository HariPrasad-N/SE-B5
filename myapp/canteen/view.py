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
import json
import random
import string
from io import BytesIO
from .recommendation import recommend

@canteen.route('/loginhack')
def loginhack():
	owner=request.args.get('owner')
	session['Owner_id']=owner
	return 'Success'

@canteen.route('/userhack')
def userhack():
	session['User_id']=1
	return 'Success'

@canteen.route('/canteen_owner/owner_index')
def owner_index():
	return jsonify(get_owner_index('canteen',session['Owner_id']))

@canteen.route('/customer/customer_index')
def customer_index():
	print(session['User_id'])
	return jsonify(get_customer_index('canteen',session['User_id']))

#route to fetch menu for the day
@canteen.route('canteen_owner/menu_for_day')
@login_required
def menu_for_day():
	data=get_menu_for_day('Items', 'canteen',session['Owner_id'])
	return jsonify(data)

#route to update menu for the day
@canteen.route('canteen_owner/set_menu_for_day',methods=['POST'])
@login_required
@csrf.exempt
def set_menu_for_day():
	if request.method=="POST":
		data=request.get_json()
		return jsonify(update_menu_for_day("Items","canteen",session['Owner_id'],data))


@canteen.route('/customer_form')
def customer_form():
	return render_template('customer/customer.html.html')

@canteen.route('/owner_form')
def owner_form():
	return render_template('canteen_owner/canteen_owner.html.html')

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
	return redirect(url_for('canteen.customer_owner_index'))

@canteen.route('/owner_form_submit',methods=['POST'])
@csrf.exempt
def parse_owner_form():
	data = dict()
	data['Owner_name'] = session['username']
	data['Social_id'] = session['social_id'] #110058041200100630475
	data['Email'] = session['email_address']
	data['Canteen_name'] = request.form['canteen_name']
	session['Owner_id'] = insert_owner('canteen', data)
	return redirect(url_for('canteen.canteen_owner_owner_index'))

@canteen.route('/selectpayment/<cost>')
def selectpayment(cost):
	print(cost)
	return render_template('payment/payment.html', cost=cost)

@canteen.route('/payment/', methods=['POST','GET'])
@csrf.exempt
def payment():
	if request.method=='POST':
		MERCHANT_KEY = '@WL!6umDo4oZu%oU';
		data_dict = {
			'MID':'Instaf41556599010081',
			'ORDER_ID':''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
			'TXN_AMOUNT':request.form['TXN_AMOUNT'],
			'CUST_ID':'CUSTINSTAFOOD',
			'INDUSTRY_TYPE_ID':'Retail',
			'WEBSITE':'WEBSTAGING',
			'CHANNEL_ID':'WEB',
			'CALLBACK_URL':'http://localhost:5000/canteen/payment.status'
		}
		param_dict = data_dict  
		param_dict['CHECKSUMHASH'] =generate_checksum(data_dict, MERCHANT_KEY)
		return render_template('payment/redirect.html',data=param_dict)

@canteen.route('/payment.status',methods=['POST','GET'])
@csrf.exempt
def status():
	if request.method=='POST' or request.method=='GET':
		hash = get_hash('canteen', session['purchase_id'])
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		ip_addr = (s.getsockname()[0])
		qr_code = ("http://"+ip_addr+":5000/canteen/canteen_owner/qr/"+hash)
		# qr_code = ("http://"+ip_addr+":8000/customer/index.html")
		img = qrcode.make(qr_code).get_image()
		
		buffered = BytesIO()
		img.save(buffered, format="JPEG")
		img_str = base64.b64encode(buffered.getvalue()).decode()
		# print(img_str)
		return render_template('payment/qr.html', data={'base':img_str, 'id':session['purchase_id']})

@canteen.route('customer/process_order/',methods=['POST','GET'])
@csrf.exempt
def process_order():
	# Load request details
	# Assume request is:
	data = request.get_json()
	data['User_id'] = session['User_id']
	print(data)
	# data = {'item_ids':[214, 223, 250, 254, 261, 267, 268, 278, 279, 285, 291, 292],
	# 		'quantity':[27, 3, 25, 25, 13, 39, 28, 48, 19, 23, 42, 42],
	# 		'User_id':366}
	
	cost = get_cost('canteen', data['item_ids'], data['quantity'])
	hash = hashlib.sha512((str(data)+str(time.time())).encode('utf-8')).hexdigest()
	# hash = 'aba6a632901803216855a180d6221622481064b4'
	# Update Purchases, Transactions
	data['cost'] = cost
	data['hash'] = hash
	purchase_id = update_transaction('canteen', data)
	print(purchase_id)
	session['purchase_id'] = purchase_id
	return url_for('.selectpayment', cost = cost)

@canteen.route('/canteen_owner/qr/<hash>')
def canteen_owner_process_order_hash(hash):
	(data, status, transaction_id)=get_order('canteen', hash=hash)
	return render_template('canteen_owner/order.html', data = data, status=status, transaction_id=transaction_id)	

@canteen.route('/canteen_owner/id/<int:id>')
def canteen_owner_process_order_id(id):
	(data, status, transaction_id)=get_order('canteen', id=id)
	return render_template('canteen_owner/order.html', data = data, status=status, transaction_id=transaction_id)	

@canteen.route('/canteen_owner/complete_order', methods=["POST"])
@csrf.exempt
def complete_order():
	transaction_id = int(request.get_json())
	print('transaction_id', transaction_id)
	update_order_complete('canteen', transaction_id)
	return url_for('.canteen_owner_owner_index')


@canteen.route('/canteen_owner/typography.html')
def canteen_owner_typography():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/typography.html')

@canteen.route('/canteen_owner/icons.html')
def canteen_owner_icons():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/icons.html')

@canteen.route('/canteen_owner/tables.html')
def canteen_owner_tables():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/tables.html', data = get_canteen_details('canteen'))

@canteen.route('/canteen_owner/parent_template.html')
def canteen_owner_parent_template():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/parent_template.html')

@canteen.route('/canteen_owner/notifications.html')
def canteen_owner_notifications():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/notifications.html')

@canteen.route('/canteen_owner/charts.html')
def canteen_owner_charts():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/charts.html', gender_data = get_user_details('canteen', 'Users', 'Gender'), dept_data = get_user_details('canteen', 'Users', 'Department'), sem_data = get_user_details('canteen', 'Users', 'Semester'))

@canteen.route('/canteen_owner/page-lockscreen.html')
def canteen_owner_page_lockscreen():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/page-lockscreen.html')

@canteen.route('/canteen_owner/page-login.html')
def canteen_owner_page_login():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/page-login.html')

@canteen.route('/canteen_owner/page-profile.html')
def canteen_owner_page_profile():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/page-profile.html')

@canteen.route('/canteen_owner/panels.html')
def canteen_owner_panels():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/panels.html',data=get_orders_per_item('canteen',session['Owner_id']))

@canteen.route('/canteen_owner/elements.html')
def canteen_owner_elements():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/elements.html')

@canteen.route('/canteen_owner/index.html')
def canteen_owner_owner_index():
	if(session.get('user_type')!="owner"):
		return redirect(url_for('oauth2.signin_owner'))
	return render_template('canteen_owner/index.html',data=get_owner_index('canteen',session['Owner_id']))

"""@canteen.route('/customer/items')
def items_index():
	#table_name = 'Items'
	# cursor = get_conn('canteen')
	return render_template('customer/oldindex.html', data = get_items('Items', 'canteen'))
"""

#Changed 

@canteen.route('/customer/typography.html', methods=['GET'])
@login_required
def customer_typography():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	canteen_id = int(request.args.get('canteen'))
	return render_template('customer/typography.html', data = {'items':get_items_canteen('canteen', canteen_id),'fav':get_favorites('canteen',int(session['User_id']))})

"""@canteen.route('/customer/typography.html', methods=['GET'])
@login_required
def customer_typography():
	canteen_id = int(request.args.get('canteen'))
	return render_template('customer/typography.html', data = get_items_canteen('canteen', canteen_id))"""


@canteen.route('/customer/icons.html')
def customer_icons():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/icons.html', data = recommend('canteen',int(session['User_id']),n=4))

@canteen.route('/customer/tables.html')
def customer_tables():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/tables.html', data = get_items('Canteen', 'canteen'))

@canteen.route('/customer/parent_template.html')
def customer_parent_template():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/parent_template.html')

@canteen.route('/customer/notifications.html')
def customer_notifications():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/notifications.html')

@canteen.route('/customer/charts.html')
def customer_charts():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/charts.html')

@canteen.route('/customer/page-lockscreen.html')
def customer_page_lockscreen():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/page-lockscreen.html')

@canteen.route('/customer/page-login.html')
def customer_page_login():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/page-login.html')

@canteen.route('/customer/page-profile.html')
def customer_page_profile():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/page-profile.html')

@canteen.route('/customer/panels.html',methods=['GET'])
def customer_panels():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/panels.html',data={'items': get_favorites_item_list('canteen',int(session['User_id'])),'fav':get_favorites('canteen',int(session['User_id']))})

@canteen.route('/customer/elements.html')
def customer_elements():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/elements.html',data=get_user_orders('canteen',int(session['User_id'])))

@canteen.route('/customer/index.html')
def customer_owner_index():
	if(session.get('user_type')!="customer"):
		return redirect(url_for('oauth2.signin_customer'))
	return render_template('customer/index.html')

@canteen.route('/')
def index():
	#if(session.get('user_type')!="customer"):
	#	return redirect(url_for('oauth2.signin_customer'))
	return redirect(url_for('canteen.customer_owner_index'))


###End changed

##favs


@canteen.route('/customer/put_favorites',methods=['POST'])
@csrf.exempt
def put_favorites():
	if(request.method == "POST"):
		data = json.loads(request.data.decode("utf-8"))
		update_favorites('canteen',int(session['User_id']),data)
	return "{'status':200,'msg':'ok'}"


@canteen.route('/customer/get_recommendation',methods=['POST'])
@csrf.exempt
def get_user_recommendation():
	if(request.method == "POST"):
		data = json.loads(request.data.decode("utf-8"))
		results = recommend('canteen',-1,user_info = data)
	return jsonify(results)

if __name__ == "__main__":
	print(os.path.abspath(__file__))
	print(os.path.dirpath(__file__))
	canteen = create_canteen()
	canteen.jinja_env.cache = {}
	canteen.run(debug=True, port=5000)
