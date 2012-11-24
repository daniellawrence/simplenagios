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

def schedule_host_check(host_name):
    """ Helper Function: schedule check of a host.
    """
    execution_time = int(time.time())
    cmd = "SCHEDULE_FORCED_HOST_CHECK;%(host_name)s;%(execution_time)s\n" \
    % locals()
    command( cmd )

def schedule_host_services_check(host_name):
    """ Helper Function: schedule services check for all services on a single 
    host.
    """
    execution_time = int(time.time())
    cmd = "SCHEDULE_FORCED_HOST_SVC_CHECKS;%(host_name)s;%(execution_time)s\n" \
    % locals()
    command( cmd )

def schedule_service_check(host_name, service_name):
    """ Helper Function: schedule service check for a single server on a single
    host.
    """
    execution_time = int(time.time())
    cmd = "SCHEDULE_FORCED_SVC_CHECK;%(host_name)s;%(service_name)s;%(execution_time)s\n" \
    % locals()
    command( cmd )

def delete_comment(comment_id):
    """ Helper_Function: delete a comment based on the comment id.
    """
    cmd = "DEL_HOST_COMMENT;%(comment_id)d\n" % locals()
    command( cmd )

def remove_host_acknowledgement(host_name):
    """ Helper_Function: Remove a hosts Acknowledgment. """
    cmd = "REMOVE_HOST_ACKNOWLEDGEMENT;%(host_name)s\n" % locals()
    command( cmd )


#-------------------------------------------------------------------------------
if __name__ == "__main__":
    # As a example set the localhost to be down
    ack_host( 'localhost' , "down" )
