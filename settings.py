import os

DEBUG = True
ON_LOCALHOST = ('Development' == os.environ.get('SERVER_SOFTWARE','')[:11])
if ON_LOCALHOST:
    DOMAIN = 'localhost:8080'
else:
    DOMAIN = 'www.craignotes.org'
USE_APP_STATS = True
