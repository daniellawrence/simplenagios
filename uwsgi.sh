#!/bin/sh
# Running python by a uwsgi server, you will need to install uwsgi in order to 
# be able to run this.
# This will run the application on port 5000, enable threads and run 2 processes
uwsgi_python --http :5000 --module simplenagios --callable app --enable-threads \
--processes 2 --master
