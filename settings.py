""" All the settings for simplenagios """
# Where your nagios is...
LIVESTATUS_SOCKET_PATH = "unix:/var/lib/nagios3/rw/live"
#LIVESTATUS_SOCKET_PATH = "tcp:nagios:6557"
LIVESTATUS_SOCKET_PATH = "tcp:192.168.1.7:6557"
#LIVESTATUS_SOCKET_PATH = "tcp:localhost:6557"

# Flask Web server
LISTEN_ADDRESS = '0.0.0.0'
LISTEN_PORT = 5000
DEBUG = True

# For setting up cookies and session varibles you need to have a secret_key
# You will want to use a random string here.
SECRET_KEY = '8b6fd7fc81255b9e51ba1ebb1ef75e9c'

# Write Mode: If WRITE_MODE is enabled (true), then simple nagios is configured
# To be able to make changes to the nagios instance.
# If WRITE_MODE is disabled ( False ), then simple nagios is not able to make
# any change to the nagios or request nagios to do anything other than
# display results via mk_livestatus
WRITE_MODE = False
