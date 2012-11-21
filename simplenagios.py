#!/usr/bin/env python
""" SimpleNagios:

This is a nagios readonly* (mostly)

"""
from flask import Flask
from flask import render_template
from flask import request, redirect
from werkzeug.contrib.cache import SimpleCache
from functools import wraps
from flask import url_for
from flask import jsonify
# Importing things from simplenagios
import query    # Used to make queries via livestatus.py
import action   # Used to do actions via livestatus.py
import settings # Used to read your settings

#------------------------------------------------------------------------------
AppCache = SimpleCache()
App = Flask(__name__)

#------------------------------------------------------------------------------
def cached(timeout=60, key='view/%s'):
    """ 
    Use this decorator @cached to cache a view. Can be used to to speed up
    common views.
    """
    def decorator(func):
        """ Wrapping decorator """
        @wraps(func)
        def decorated_function(*args, **kwargs):
            """ Grabs the args and kwargs for the function used to build the
            cache_key for the caching system. """
            cache_key = key % request.path
            return_value = AppCache.get(cache_key)
            if return_value is not None:
                return return_value
            return_value = func(*args, **kwargs)
            AppCache.set(cache_key, return_value, timeout=timeout)
            return return_value
        return decorated_function
    return decorator

#------------------------------------------------------------------------------
@App.template_filter('format_td')
def reverse_filter(time_delta):
    """ Convert a timedelta into a min, hours or days """
    time_in_minutes = time_delta.total_seconds() / 60
    if time_in_minutes < 180:
        return "%d min" % time_in_minutes
    if time_in_minutes < 2000:
        return "%d hours" % ( time_in_minutes /60 )

    return "%d days" % ( time_in_minutes /60/ 24 )

#------------------------------------------------------------------------------
@App.template_filter('host_status')
def tag_host_status(status):
    """ Convert a host_status into an english word. 
    For example:
    'up' is stored as 0. 
    """
    if status == 0:
        return "up"
    if status == 1:
        return "down"
    return "unknown"

#------------------------------------------------------------------------------
@App.template_filter('service_status')
def tag_service_status(status):
    """ Convert a service_status into an english word.
    For example:
    'ok' is stored as 0.
    """
    if status == 0:
        return "ok"
    if status == 1:
        return "warning"
    if status == 2:
        return "crit"
    return "unknown"

#------------------------------------------------------------------------------
def gather_filters(request):
    """ Generic filter processer to be used with query """
    request_args = request.args
    allowed_filters = ('state', 'acknowledged', 'plugin_output', 'groups')
    extra_filters = []
    for filter_column in allowed_filters:
        filter_data = request_args.get(filter_column, None)

        if not filter_data:
            continue

        if '~' in filter_data:
            extra_filters.append("%(filter_column)s %(filter_data)s" % locals())
            continue

        if '!' in filter_data:
            filter_data = filter_data.replace('!','!= ')
            extra_filters.append("%(filter_column)s %(filter_data)s" % locals())
            continue

        if '>' in filter_data:
            extra_filters.append("%(filter_column)s %(filter_data)s" % locals())
            continue

        if '<' in filter_data:
            extra_filters.append("%(filter_column)s %(filter_data)s" % locals())
            continue

        extra_filters.append("%(filter_column)s = %(filter_data)s" % locals())

    return extra_filters

#------------------------------------------------------------------------------
@App.route("/")
@App.route("/tac/")
def tac():
    """ The 'Tactical Monitoring Overview', this will show an overview of all 
    the services: up, down, warning, error, etc.
    """
    extra_filters = gather_filters(request)
    try:
        service_stats = query.service_stats(extra_filter=extra_filters)
        host_stats = query.hosts_stats(extra_filter=extra_filters)
    except query.livestatus.MKLivestatusSocketError as error:
        error_message = """
        SimpleNagios received an error trying to connect to the nagios broker.
        <Br />
        You might want to check you'r settings.py file and make sure that nagios
        is currently running as expected.
        <Br />
        The error message was:
        <Br />
        %(error)s""" % locals()
        return render_template('error.template', error_message=error_message,
            error_tepe="connection error")

    return render_template('tac.template', service_stats=service_stats, 
    host_stats=host_stats )

#------------------------------------------------------------------------------
@cached
@App.route("/hosts/")
def show_hosts():
    """ From a filter or no filter display a list of hosts. """
    extra_filters = gather_filters(request)
    host_list = query.get_hosts(
    columns='name state last_check last_state_change plugin_output acknowledged scheduled_downtime_depth notifications_enabled max_check_attempts current_attempt',
    extra_filter=extra_filters)
    host_stats = query.hosts_stats(extra_filter=extra_filters)
    return render_template('host_list.template',
    host_list=host_list, host_stats=host_stats, settings=settings )

#------------------------------------------------------------------------------
#@cached
#@app.route("/all_hosts.json")
#def all_hosts_json(hostname = None):
#    extra_filters = gather_filters(request)
#    host_list = query.get_hosts( columns='name', extra_filter=extra_filters)
#    hosts = []
#    for h in host_list:
#        hosts.append(h['name'])
#    return jsonify(hosts=hosts)

#------------------------------------------------------------------------------
@App.route("/hosts-search/")
def hosts_search():
    """ Take a GET argument of host_name and redirect to a nice url. """
    host_name = request.args.get('host_name', None)
    if not host_name:
        return redirect( "/hosts/" )
    return redirect( "/host/%(host_name)s/services/" % locals() )

#------------------------------------------------------------------------------
@cached
@App.route("/comment/")
def comment():
    """ List of comments that have been made."""
    extra_filters = gather_filters(request)
    comment_list = query.get_comments(extra_filter=extra_filters)
    return render_template('comment_list.template', comment_list=comment_list,
    settings=settings )

#------------------------------------------------------------------------------
@cached
@App.route("/comment/<comment_id>/")
def single_comment(comment_id):
    """ Display a comment that matches a comment_id. """
    comment_list = query.get_comment(comment_id)
    return render_template('comment.template', comment_list=comment_list,
    settings=settings )

#------------------------------------------------------------------------------
@cached
@App.route("/host/<host_name>/service/")
@App.route("/host/<host_name>/services/")
def host_services(host_name):
    """ Given a host_name display all of its services. """
    extra_filters = gather_filters(request)
    service_list = query.get_host_services(host_name, 
    columns='host_name description state last_check last_state_change plugin_output acknowledged host_acknowledged max_check_attempts current_attempt',
    extra_filter=extra_filters)

    try:
        service_stats = query.service_stats(
        extra_filter="host_name = %(host_name)s" % locals())
    except Exception as error:
        return redirect("/tac")

    return render_template('service_list.template', service_list=service_list,
    service_stats=service_stats,settings=settings )

#------------------------------------------------------------------------------
@cached
@App.route("/host/<host_name>/")
def host_detail(host_name):
    """ Given a hostname, show the extended detail of the host. """

    # Grab a single host from the query.get_host()
    results = query.get_host(host_name)

    # If we have got no results then fail to the tac
    if len(results) == 0:
        return tac()

    # If we have more than 1 result, then show a list of services not a single
    # host.
    if len(results) > 1:
        return redirect( "/host/%(host_name)s/services/" % locals() )

    # Grab the only result into host
    host = results[0]

    # Return the results
    return render_template('host_detail.template', host=host, 
    settings=settings )

#------------------------------------------------------------------------------
@App.route("/take_action/",  methods=['GET', 'POST'] )
def take_action():
    """ Take a POST and turn it on to an action, that will be used by action.py
    """
    request_copy = request.form.copy()
    services = request_copy.getlist('services')
    hosts = request_copy.getlist('hosts')
    message = request_copy.get('action_message')
    action_type = request_copy.get('action_type')

    if action_type == 'ack':
        action.ack_hosts( hosts, message )
        action.ack_services( services, message )

    return redirect( request.environ['HTTP_REFERER'] )

#------------------------------------------------------------------------------
@App.route("/host/<host_name>/service/<service_name>/schedule_recheck")
def schedule_recheck_service(host_name, service_name):
    """ Given a host_name and service_name schedule a recheck of the sevice.
    """
    action.schedule_service_check(host_name, service_name)
    return jsonify( {'host_name': host_name, 'service_name': service_name,
        'message': 'Check has been scheduled for a recheck as soon as possible'})


#------------------------------------------------------------------------------
@App.route("/host/<host_name>/schedule_recheck")
def schedule_recheck_host(host_name):
    """ Given a host_name and service_name schedule a recheck of the sevice.
    """
    action.schedule_host_check(host_name)
    return jsonify( {'host_name': host_name,
        'message': 'Check for host has been scheduled for a recheck as soon as possible'})

@App.route("/host/<host_name>/schedule_recheck")
def schedule_recheck_host_services(host_name):
    """ Given a host_name schedule a recheck of all of the services.
    """
    action.schedule_service_check(host_name, service_name)
    return jsonify( {'host_name': host_name,
        'message': 'All services on this host have been scheduled for a recheck as soon as possible'})


#------------------------------------------------------------------------------
@App.route("/host/<host_name>/service/<service_name>/")
def service_detail(host_name, service_name):
    """ Find details of a service for a host and a service_name """
    extra_filters = gather_filters(request)
    extra_filters.append('host_name = %(host_name)s' % locals())
    #cols = [ 'description','host_name','notification_period',
    #'host_plugin_output','action_url','notes_url','state','acknowledged',
    #'last_check','check_type','next_check','last_state_change',
    #'last_notification', 'plugin_output','last_notification',
    #next_notification','host_num_services_ok' ]
    service = query.get_services(service_name, columns=None,
    extra_filter=extra_filters)
    service = service[0]

    return render_template('service_detail.template', service=service, 
    settings=settings )

#------------------------------------------------------------------------------
@cached
@App.route("/hostgroup/<hostgroup>/")
def hostgroup_detail(hostgroup):
    """ Given a hostgroup, display a list of hosts that are in the group. """
    hostgroup = query.get_hostgroup(hostgroup)[0]
    return render_template('hostgroup_detail.template', hostgroup=hostgroup,
    settings=settings )

#------------------------------------------------------------------------------
@cached
@App.route("/service/<service_name>/")
def show_services(service_name):
    """ list of services that match a service name, this will show the same
    service across a number of servers. """
    extra_filters = gather_filters(request)

    service_list = query.get_services(service_name, 
    columns='host_name description state last_check last_state_change plugin_output acknowledged host_acknowledged current_attempt max_check_attempts',
    extra_filter=extra_filters)

    service_stats = query.service_stats(
    extra_filter="description = %(service_name)s" % locals())
    return render_template('service_list.template', service_list=service_list,
    service_stats=service_stats, settings=settings )

#------------------------------------------------------------------------------
@cached
@App.route("/service/")
def all_services():
    """
    This of every single service that we know about, this is very slow if 
    no filter is in play.
    """
    extra_filters = gather_filters(request)
    service_list = query.get_all_services(
    columns='host_name description state last_check last_state_change plugin_output acknowledged host_acknowledged max_check_attempts current_attempt',
    extra_filter=extra_filters)
    service_stats = query.service_stats(extra_filter=extra_filters)
    return render_template('service_list.template', service_list=service_list,
    service_stats=service_stats, settings=settings )

#------------------------------------------------------------------------------
# If this is running as __main__ thne start up the website
#------------------------------------------------------------------------------
if __name__ == "__main__":
    # Pull the settings from settings.py 
    App.secret_key = settings.SECRET_KEY
    App.run(
         settings.LISTEN_ADDRESS,
         settings.LISTEN_PORT,
         debug = settings.DEBUG
    )
