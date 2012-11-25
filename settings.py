""" All the settings for simplenagios """
# Where your nagios is...
#LIVESTATUS_SOCKET_PATH = "unix:/var/lib/nagios3/rw/live"
#LIVESTATUS_SOCKET_PATH = "tcp:nagios:6557"
#LIVESTATUS_SOCKET_PATH = "tcp:192.168.1.7:6557"
LIVESTATUS_SOCKET_PATH = "tcp:localhost:6557"

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
WRITE_MODE = True


# If simple nagios should pull historical information in the form of graphs from
# you graphite instance based on check names.
# A URL will be constructed based on the host_name and service_name along with the
# GRAPHITE_HOST from this file (settings.py).
# Once setup the service_detail page will show information about that service from 
# graphs setup in graphite.
USE_GRAPHITE = True

# Host and Port for your graphite instance. 
# The URL builder will then use this information to generate the http://graphite/render
# path.
GRAPHITE_HOST = "localhost:8080"

# Maps a service name to a graphite location, this is then used to display a graphite
# graph on the service details page.
GRAPHITE_MAP = {
    # Grab all filesystems
	'opsunix__filesystem': {'target': 'systems.%(hostname)s.filesystem.*.capacity'},
	# Should the load average 1,5 and 15m
	'opsunix__loadavg': {'target': 'systems.%(hostname)s.loadavg.*'},
	# Count the number of ssh sessions
	'opsunix__ssh': {'target': 'systems.%(hostname)s.process.sshd'},
	# Count the number of syslog processes
	'opsunix__syslog': {'target': 'systems.%(hostname)s.process.syslog'},
	# Count the number of samba useres
	'opsunix__samba': {'target': 'systems.%(hostname)s.samba.users'},
	# Display the mail connection time
	'opsunix__smtpin': {'target': 'systems.%(hostname)s.smtpin'},
	# Display all the hardware temps for the system
	'opsunix__temp': {'target': 'aliasByNode(systems.%(hostname)s.hardware.temp.*,-1)'}

}