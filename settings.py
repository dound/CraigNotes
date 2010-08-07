import os

DEBUG = True
ON_LOCALHOST = ('Development' == os.environ.get('SERVER_SOFTWARE','')[:11])
if ON_LOCALHOST:
    DOMAIN = 'localhost:8080'
else:
    DOMAIN = 'dound.appspot.com'
USE_APP_STATS = True

ADMINS = ['972aa3d715ab0d50dc5d']
