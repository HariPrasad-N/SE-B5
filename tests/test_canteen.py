import pytest
import pytest_flask
from flask import url_for

class TestApp:

	# Canteen View Start
	def test_index(self, client):
		res = client.get(url_for('canteen.canteen_owner_owner_index'))
		assert res.status_code == 302
	
	def test_elements(self, client):
		res = client.get(url_for('canteen.canteen_owner_elements'))
		assert res.status_code == 302

	def test_menu_for_day(self,client):
		res = client.get(url_for('canteen.menu_for_day'))
		assert res.status_code == 302
	
	def test_panels(self, client):
		res = client.get(url_for('canteen.canteen_owner_panels'))
		assert res.status_code == 302
		
	def test_page_profile(self, client):
		res = client.get(url_for('canteen.canteen_owner_page_profile'))
		assert res.status_code == 302
		
	def test_page_login(self, client):
		res = client.get(url_for('canteen.canteen_owner_page_login'))
		assert res.status_code == 302
		
	def test_page_lockscreen(self, client):
		res = client.get(url_for('canteen.canteen_owner_page_lockscreen'))
		assert res.status_code == 302
		
	def test_charts(self, client):
		res = client.get(url_for('canteen.canteen_owner_charts'))
		assert res.status_code == 302
		
	def test_notifications(self, client):
		res = client.get(url_for('canteen.canteen_owner_notifications'))
		assert res.status_code == 302
		
	def test_tables(self, client):
		res = client.get(url_for('canteen.canteen_owner_tables'))
		assert res.status_code == 302
		
	def test_icons(self, client):
		res = client.get(url_for('canteen.canteen_owner_icons'))
		assert res.status_code == 302
	
	def test_typography(self, client):
		res = client.get(url_for('canteen.canteen_owner_typography'))
		assert res.status_code == 302
	# Canteen View Start
	