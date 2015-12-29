simplenagios
============

Simple Nagios web client - Using bootstrap

Example screenshot:

![TAC](https://raw.github.com/daniellawrence/simplenagios/master/screenshots/tac.png "TAC")

![host_details](https://raw.github.com/daniellawrence/simplenagios/master/screenshots/localhost_host_detail.png "host_details")


Getting Starting
----------------

You will need to setup mklivestatus on your nagios server, so that simple nagios is able to communicate with your nagios instance.

Once setup you can either use unix file sockets or tcp sockets.

In ubuntu the following will get you started if your running this on your nagios server.


Get you nagios ready:

    $ sudo apt-get install check-mk-livestatus
    $ vi /etc/nagios3/nagios.cfg
    broker_module=/usr/lib/check_mk/livestatus.o /var/lib/nagios3/rw/live
    event_broker_options=-1

Setup and run simplenagios:

    $ sudo apt-get install xinetd python-pip git
    $ git clone https://github.com/daniellawrence/simplenagios.git
    $ cd simplenagios
    $ cp xinetd-livestatus /etc/xinetd.d/
    $ sudo service xinetd restart
    $ pip install -r requirements.txt
    $ ./simplenagios.py

Connect to http://localhost:5000 to see simple nagios.

settings
--------

__LIVESTATUS_SOCKET_PATH__

This tells simplenagios where the socket is for mk-livestatus, without this socket simple nagios will not able to do anything.

__WRITE_MODE__

This controls if the simple nagios system is allowed to write back to nagios or will only be a read-only copy.
