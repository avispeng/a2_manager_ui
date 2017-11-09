#!venv/bin/python
from app import webapp
webapp.run(host='localhost', port=5003, debug=True)
#webapp.run(host='0.0.0.0')