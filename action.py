#!/usr/bin/python
# Sample program for accessing the Livestatus Module
# from a python program
import time
from contrib import livestatus
import settings

def command(command):
     command = "[%d] %s" % ( time.time(), command )
     conn = livestatus.SingleSiteConnection(settings.LIVESTATUS_SOCKET_PATH).command( command )

def ack_host(host_name, message):
     cmd = "ACKNOWLEDGE_HOST_PROBLEM;%(host_name)s;0;0;0;nagiosadmin;%(message)s\n" % locals()
     command( cmd )

def ack_hosts(host_list, message):
    cmd_t = "ACKNOWLEDGE_HOST_PROBLEM;%(host_name)s;0;0;0;nagiosadmin;%(message)s\n"
    cmd = []
    for host_name in host_list:
        command( cmd_t % locals() )

def ack_service(service, message):
    command( "ACKNOWLEDGE_SVC_PROBLEM;%(service)s;0;0;0;nagiosadmin;%(message)s\n" % locals() )

def ack_services(service_list, message):
    cmd_t = "ACKNOWLEDGE_SVC_PROBLEM;%(service)s;0;0;0;nagiosadmin;%(message)s\n"
    for service in service_list:
        command( cmd_t % locals() )

if __name__ == "__main__":
    ack_host( 'localhost' , "down" )
