#!/usr/bin/env python
# Sample program for accessing the Live status Module
# from a python program
import time
from contrib import livestatus
import settings

def command(command):
    """ Take a command and post it using live status over a single connection.
    """
    command = "[%d] %s" % ( time.time(), command )
    # Create the connection
    conn = livestatus.SingleSiteConnection(settings.LIVESTATUS_SOCKET_PATH)
    # Run the command the connection
    results = conn.command( command )
    # Return the results
    return results

def ack_host(host_name, message):
    """ Helper Function: Acknowledge a host problem with a comment. 
    This should be able to to pickup the user name from the session.
    """
    cmd = "ACKNOWLEDGE_HOST_PROBLEM;%(host_name)s;0;0;0;nagiosadmin;%(message)s\n" % locals()
    command( cmd )

def ack_hosts(host_list, message):
    """ Helper Function: Acknowledge a list of host problems with a comment.
    This should be able to pickup the user name from the session in a 
    later version. """
    cmd_t = "ACKNOWLEDGE_HOST_PROBLEM;%(host_name)s;0;0;0;nagiosadmin;%(message)s\n"
    for host_name in host_list:
        command( cmd_t % locals() )

def ack_service(service, message):
    """ Helper Function: Acknowledge a service problem with a comment. """
    command( "ACKNOWLEDGE_SVC_PROBLEM;%(service)s;0;0;0;nagiosadmin;%(message)s\n" % locals() )

def ack_services(service_list, message):
    """ Helper Function: Acknowledge a list service problems with a comment. """
    cmd_t = "ACKNOWLEDGE_SVC_PROBLEM;%(service)s;0;0;0;nagiosadmin;%(message)s\n"
    for service in service_list:
        command( cmd_t % locals() )


#-------------------------------------------------------------------------------
if __name__ == "__main__":
    # As a example set the localhost to be down
    ack_host( 'localhost' , "down" )
