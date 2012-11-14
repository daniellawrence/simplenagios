#!/usr/bin/python
from flask import Flask
from flask import render_template
from flask import request, redirect, url_for
from werkzeug.contrib.cache import SimpleCache
from functools import wraps
from flask import Response, session, escape, jsonify

# Importing things from simplenagios
import query    # Used to make queries via livestatus.py
import action   # Used to do actions via livestatus.py
import settings # Used to read your settings

#------------------------------------------------------------------------------
cache = SimpleCache()
app = Flask(__name__)

#------------------------------------------------------------------------------
def cached(timeout=60, key='view/%s'):
    """ Use this decorator @cached to cache a view. Can be used to to speed up
    common views. """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % request.path
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator

#------------------------------------------------------------------------------
@app.template_filter('format_td')
def reverse_filter(td):
    """ Convert a timedelta into a min, hours or days """
    tm = td.total_seconds() / 60
    if tm < 180:
        return "%d min" % tm
    if tm < 2000:
        return "%d hours" % ( tm /60 )

    return "%d days" % ( tm /60/ 24 )
#------------------------------------------------------------------------------
@app.template_filter('host_status')
def reverse_filter(status):
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
@app.template_filter('service_status')
def reverse_filter(status):
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
    allowed_filters = ('state','acknowledged','plugin_output', 'groups')
    extra_filters = []
    for filter_column in allowed_filters:
        filter_data = request.args.get(filter_column, None)

        if not filter_data:
            continue

        if '~' in filter_data:
            extra_filters.append("%(filter_column)s %(filter_data)s" % locals())
            continue

        if '!' in filter_data:
            filter_date = filter_data.replace('!','!= ')
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
@app.route("/")
@app.route("/tac/")
def tac(exter_filter=None):
    """ The 'Tactical Monitoring Overview', this will show an overview of all 
    the services: up, down, warning, error, etc.
    """
    extra_filters = gather_filters(request)
    service_stats = query.service_stats(extra_filter=extra_filters)
    host_stats = query.hosts_stats(extra_filter=extra_filters)
    return render_template('tac.template', service_stats=service_stats, 
                           host_stats=host_stats )

#------------------------------------------------------------------------------
@cached
@app.route("/hosts/")
def hosts(hostname=None):
    extra_filters = gather_filters(request)
    host_list = query.get_hosts(
    columns='name state last_check last_state_change plugin_output acknowledged scheduled_downtime_depth notifications_enabled max_check_attempts current_attempt',
    extra_filter=extra_filters)
    host_stats = query.hosts_stats(extra_filter=extra_filters)
    return render_template('host_list.template',
    host_list=host_list, host_stats=host_stats )

#------------------------------------------------------------------------------
@cached
@app.route("/all_hosts.json")
def all_hosts_json(hostname=None):
    extra_filters = gather_filters(request)
    host_list = query.get_hosts( columns='name', extra_filter=extra_filters)
    hosts = []
    for h in host_list:
        hosts.append(h['name'])
    return jsonify(hosts=hosts)

#------------------------------------------------------------------------------
@app.route("/hosts-search/")
def hosts_search():
    #extra_filters = gather_filters(request)
    host_name = request.args.get('host_name', None)
    if not host_name:
        return redirect( "/hosts/" )
    return redirect( "/host/%(host_name)s/services/" % locals() )

#------------------------------------------------------------------------------
@cached
@app.route("/comment/")
def comment():
    extra_filters = gather_filters(request)
    comment_list = query.get_comments(extra_filter=extra_filters)
    return render_template('comment_list.template', comment_list=comment_list )

#------------------------------------------------------------------------------
@cached
@app.route("/comment/<comment_id>/")
def single_comment(comment_id):
    service_list = query.get_comment(comment_id)
    return render_template('comment.template', comment_list=comment_list )

#------------------------------------------------------------------------------
@cached
@app.route("/host/<host_name>/")
@app.route("/host/<host_name>/service/")
@app.route("/host/<host_name>/services/")
@app.route("/hosts/<host_name>/")
@app.route("/hosts/<host_name>/service/")
@app.route("/hosts/<host_name>/services/")
def host_services(host_name):
    extra_filters = gather_filters(request)
    service_list = query.get_host_services(host_name, 
    columns='host_name description state last_check last_state_change plugin_output acknowledged host_acknowledged max_check_attempts current_attempt',
    extra_filter=extra_filters)
    service_stats = query.service_stats(
    extra_filter="host_name = %(host_name)s" % locals())
    return render_template('service_list.template', service_list=service_list,
    service_stats=service_stats )

#------------------------------------------------------------------------------
@cached
@app.route("/host/<host_name>/detail")
def host_detail(host_name):
    try:
        host = query.get_host(host_name)[0]
    except IndexError:
        return bigsearch()
    return render_template('host_detail.template', host=host )

#------------------------------------------------------------------------------
@cached
@app.route("/host/<host_name>/graph")
def host_graph(host_name):
    host = query.get_host(host_name)[0]
    return render_template('host_graph.template', host=host )

#------------------------------------------------------------------------------
@cached
@app.route("/take_action/",  methods=['GET', 'POST'] )
def take_action():
    print request.environ['HTTP_REFERER']
    d = request.form.copy()
    services = d.getlist('services')
    hosts = d.getlist('hosts')
    message = d.get('action_message')
    action_type = d.get('action_type')
    if action_type == 'ack':
        action.ack_hosts( hosts, message )
        action.ack_services( services, message )

    return redirect( request.environ['HTTP_REFERER'] )


#------------------------------------------------------------------------------
@app.route("/host/<host_name>/service/<service_name>/")
def service_detail(host_name, service_name):
    extra_filters = gather_filters(request)
    extra_filters.append('host_name = %(host_name)s' % locals())
    cols = [ 'description','host_name','notification_period',
    'host_plugin_output','action_url','notes_url','state','acknowledged',
    'last_check','check_type','next_check','last_state_change',
    'last_notification', 'plugin_output','last_notification',
    'next_notification','host_num_services_ok' ]
    service = query.get_services(service_name, columns=None,
    extra_filter=extra_filters)
    service = service[0]

    return render_template('service_detail.template', service=service )

#------------------------------------------------------------------------------
@cached
@app.route("/hostgroup/<hostgroup>/")
def hostgroup_detail(hostgroup):
    hostgroup = query.get_hostgroup(hostgroup)[0]
    return render_template('hostgroup_detail.template', hostgroup=hostgroup )

#------------------------------------------------------------------------------
@cached
@app.route("/service/<service_name>/")
def services(service_name):
    """ list of services that match a service name, this will show the same
    service across a number of servers. """
    extra_filters = gather_filters(request)
    service_list = query.get_services(service_name, 
    columns='host_name description state last_check last_state_change plugin_output acknowledged host_acknowledged current_attempt max_check_attempts',
    extra_filter=extra_filters)
    service_stats = query.service_stats(
    extra_filter="description = %(service_name)s" % locals())
    return render_template('service_list.template', service_list=service_list,
    service_stats=service_stats )

#------------------------------------------------------------------------------
@cached
@app.route("/service/")
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
    service_stats=service_stats )

#------------------------------------------------------------------------------
# If this is running as __main__ thne start up the website
#------------------------------------------------------------------------------
if __name__ == "__main__":
    # Pull the settings from settings.py 
    app.secret_key = settings.SECRET_KEY
    app.run(
         settings.LISTEN_ADDRESS,
         settings.LISTEN_PORT,
         debug = settings.DEBUG
    )