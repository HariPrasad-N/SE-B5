# Flask
export MYAPP_CONFIG='development'
export FLASK_APP=autoapp.py
export FLASK_DEBUG=True
# Please generate your own random keys (you can use os.urandom(24))
export SECRET_KEY='\xa6TQ5\xc9\xf942\x9cx\x9b\xed\xa4\xc7\x95\xcc\xfd\xb8Q\xa1\x80\x99Z%'
# Separate token for CSRF protection (by default it uses secret key)
export WTF_CSRF_SECRET_KEY='\xc9\xcc\x91{\xd9\x9a\x18\x92\xaa\xb4\x9e\x80\x07\x13\x92-\x1ciH\x86\xecz:['
# Prevent OAuth 2 MUST utilize https on Development / Test server
# Friendly reminder: DO NOT USE in production
export OAUTHLIB_INSECURE_TRANSPORT=1
export OAUTHLIB_RELAX_TOKEN_SCOPE=1
export DEBUG=1
export WTF_CSRF_ENABLED=False
echo 'Starting myapp'

# Python Virtual Environment using Pipenv
flask db-create
flask db-load-users
echo 'Starting web server'
flask run --host=0.0.0.0

# Python Virtual Environment using virtualenv
# source venv/bin/activate
