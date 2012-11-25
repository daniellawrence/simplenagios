#!/usr/bin/env python 
"""
A simple library that has common queries into nagios via the mk_livestatus
module.
"""
import datetime
from contrib import livestatus
import settings

def query(query, limit = None, columns = None, extra_filter = None, 
          return_type = 'table_assoc', item_type = None):
    """
    * Take a query in lsl
    * run the query
    * return the query in the requested format
    """

    query = build_query(query, columns = columns,
                         extra_filter = extra_filter)
    
    # Get the current datetime
    now_dt = datetime.datetime.now()

    conn = livestatus.SingleSiteConnection(settings.LIVESTATUS_SOCKET_PATH)
    conn.limit = limit

    if return_type == "value":
        return conn.query_value(query)

    if return_type == "row":
        return conn.query_row(query)

    if return_type == "row_assoc":
        return conn.query_row_assoc(query)

    if return_type == "row_column":
        return conn.query_row_assoc(query)

    if return_type == "table":
        return conn.query_table(query)

    if return_type == "table_assoc":
        data = conn.query_table_assoc(query)
        for row in data:
            for col in row.keys():

                # If the colname dosn't starts with the name last or _time then
                # it will not be a timestamp that will need to be converted.
                if 'last_' not in col \
                and '_time' not in col \
                and 'next_' not in col:
                    continue
                # If the data is not an int(), then dont try and convert it to 
                # a timestamp( datetime )
                if type(row[col]).__name__ != "int":
                    continue
                # Convert all timestamps into dateime() objects and timedetal()
                # objects, where the delta is from the current time.
                row["%s_dt" % col] = datetime.datetime.fromtimestamp( row[col] )
                row["%s_td" % col] = now_dt - datetime.datetime.fromtimestamp( row[col] )
        return data

    if return_type == "summed_stats":
        return conn.query_summed_stats(query)

    raise Exception("Unknown return_type='%s'" % return_type)

def query_table(lsl_query, limit=None, columns=None, extra_filter=None):
    """ take a query and force it to be returned in a dict ( table ) format.
    """
    lsl_query = build_query(lsl_query, columns = columns, 
                         extra_filter = extra_filter, return_type="table")
    return lsl_query

def query_table_assoc(lsl_query, columns=None, extra_filter=None):
    """ take a query and force it to be an assoced table format. """
    lsl_query = build_query(lsl_query, columns = columns, 
                         extra_filter = extra_filter, return_type="table_assoc")
    return lsl_query
    
def build_query(lsl_query, columns=None, extra_filter=None):
    """ take the complex parts of a query, that have been diveded up into 
    kwargs and join them all back together in to an lsl_query. """
    if columns:
        if type(columns).__name__ in ('str','unicode'):
            lsl_query += "Columns: %s\n" % columns
        if type(columns).__name__ in ('list',):
            lsl_query += "Columns: %s\n" % " ".join(columns)

    if extra_filter:

        if ',' in extra_filter:
            extra_filter = extra_filter.split(',')

        if type(extra_filter).__name__ == "list":
            lsl_query += "Filter: " + "\nFilter: ".join( extra_filter )
        else:
            lsl_query += "Filter: %(extra_filter)s\n" % locals()

    return lsl_query

def get(lsl_query, limit=None, columns=None, extra_filter=None):
    """ using the lsl_query to grab a type of objects that match that query.
    columns and filters can be applied. """
    return query("GET %s\n" % lsl_query, limit=limit, columns=columns, 
    item_type=query, extra_filter=extra_filter)

def get_hosts(limit=None, columns=None, extra_filter=None):
    """ grab a list of hosts that match a columns and extra_filters. """
    return query("GET hosts\n", limit=limit, columns=columns,
    item_type="hosts" , extra_filter=extra_filter)

def get_host(host_name, columns = None, extra_filter = None):
    """ return a list of hosts and columns that match a given filter if any. 
    """
    if '~' not in host_name:
        host_name = "= %(host_name)s" % locals()
    else:
        host_name = "~ ".join( host_name.split('~') )
       
    return query("GET hosts\nFilter: host_name %s\n" % host_name, limit=1,
    columns=columns , item_type="hosts", extra_filter=extra_filter)

# Removed duplicate function
#def get_host(host_name, columns=None, extra_filter=None):
#    """ Given a single host it will return all the requested columns. """ 
#    return query("GET hosts\nFilter: host_name = %s\n" % host_name, limit=3, 
#    columns=columns , item_type="hosts", extra_filter=extra_filter)

#------------------------------------------------------------------------------
def get_host_services(host_name, limit=None, columns=None,extra_filter=None):
    if '~' not in host_name:
        host_name = "= %(host_name)s" % locals()
    else:
        host_name = "~ ".join( host_name.split('~') )

    return query("GET services\nFilter: host_name %s\n" % host_name, 
                  limit=limit, columns=columns , item_type="services",
                  extra_filter=extra_filter)

#------------------------------------------------------------------------------
def get_services(service_name, limit = None, columns = None, extra_filter = None):
     return query("GET services\nFilter: description = %s\n" % service_name,
                  limit=limit, columns=columns,  item_type="services",
                  extra_filter=extra_filter)

#------------------------------------------------------------------------------
def get_hostgroup(hostgroup, limit = None, columns = None, extra_filter = None):
    """ Given a hostgroup the system will return all columns that are 
    requested. """
    return query("GET hostgroups\nFilter: name = %s\n" % hostgroup,
                  limit=limit, columns=columns,  item_type="hostgroup",
                  extra_filter=extra_filter)

#------------------------------------------------------------------------------
def get_all_services(limit=None, columns=None, extra_filter=None):
    """ This will return all the services that match the filter, columns can
    be selected via columns. """
    return query("GET services\n", limit=limit, columns=columns, 
    item_type="services" , extra_filter=extra_filter)

#------------------------------------------------------------------------------
def get_columns(lsl_query):
    """ Given any query it will only fetch one result and return the columns
    of that result. """
    return query("%s\n" % lsl_query, limit=1).columns

#------------------------------------------------------------------------------
def get_comments(extra_filter=None):
    """ Run the passed query and only return the columns of the results. """
    return query("GET comments\n", 
    #columns="host_name service_description author comment entry_type entry_time",
    extra_filter=extra_filter)

#------------------------------------------------------------------------------
def get_comment(comment_id):
    """ Run the passed query and only return the columns of the results. """
    extra_filter="id = %(comment_id)s" % locals()
    return query("GET comments\n")[0]
    #columns="comment_id host_name service_description author comment entry_type entry_time",
    #extra_filter=extra_filter)

def get_downtimes(extra_filter=None):
    return query("GET get_downtimes", extra_filter=extra_filter)

def get_downtime(downtime_id):
    return query("GET get_downtimes", extra_filter="id = %(downtime_id)d" % locals())


def service_stats(extra_filter=None):
    """ Get all the stats for all the services that extra_filters: ok, warn, etc
    """
    for single_filter in extra_filter:
        if 'state ' in single_filter:
            extra_filter.remove(single_filter)

    s = query(
"""GET services
Stats: state = 0
Stats: state = 0
Stats: acknowledged = 0
StatsAnd: 2
Stats: state = 0
Stats: acknowledged = 1
StatsAnd: 2
Stats: state = 1
Stats: state = 1
Stats: acknowledged = 0
StatsAnd: 2
Stats: state = 1
Stats: acknowledged = 1
StatsAnd: 2
Stats: state = 2
Stats: state = 2
Stats: acknowledged = 0
StatsAnd: 2
Stats: state = 2
Stats: acknowledged = 1
StatsAnd: 2
Stats: state = 3
Stats: state = 3
Stats: acknowledged = 0
StatsAnd: 2
Stats: state = 3
Stats: acknowledged = 1
StatsAnd: 2
""", return_type='row', extra_filter=extra_filter  )
    z = query(
"""GET services
Stats: state != 9999
Columns: state acknowledged scheduled_downtime_depth checks_enabled
""", return_type='table', extra_filter=extra_filter  )
    total_state = {}
    total_acknowledged = {}
    total_not_acknowledged = {}
    total_in_downtime = {}
    total_not_in_downtime = {}
    total_enabled = {}
    total_disabled = {}

    for group in z:
        (state, acknowledged, scheduled_downtime_depth, checks_enabled, count ) = group
        acknowledged = int( acknowledged )
        scheduled_downtime_depth = int( scheduled_downtime_depth )
        checks_enabled = int( checks_enabled)
        if state == '0':
            state = 'ok'
        if state == '1':
            state = 'warning'
        if state == '2':
            state = 'error'
        if state == '3':
            state = 'unknown'
        if state not in total_state:
            total_state[ state ] = 0
            total_acknowledged[ state ] = 0
            total_not_acknowledged[ state ] = 0
            total_in_downtime[ state ] = 0
            total_not_in_downtime[ state ] = 0
            total_enabled[ state ] = 0
            total_disabled[ state ] = 0


        if acknowledged == 1:
            total_acknowledged[ state ] += count
        else:
            total_not_acknowledged[ state ] += count

        if scheduled_downtime_depth == 1:
            total_in_downtime[ state ] += count
        else:
            total_not_in_downtime[ state ] += count

        if checks_enabled == 1:
            total_enabled[ state ] += count
        else:
            total_disabled[ state ] += count


        total_state[ state ] += count

    j = {
	# OK status
	'ok': int(s[0]),
	'ok_not_ack': int(s[1]),
	'ok_ack': int(s[2]),
	# Warnings
	'warn': int(s[3]),
	'warn_not_ack': int(s[4]),
	'warn_ack': int(s[5]),
	# Warnings
	'error': int(s[6]),
	'error_not_ack': int(s[7]),
	'error_ack': int(s[8]),
	# Unknown
	'unknown': int(s[9]),
	'unknown_not_ack': int(s[10]),
	'unknown_ack': int(s[11])
    }
    # do math after we have some nicer names
    total = j['ok'] + j['warn'] + j['error'] + j['unknown']
    if total == 0:
        raise Exception('No services found')
    extra_stats = {
        # total
        'total': total,
	    'ok_percent':  ( j['ok'] / float( total ) * 100 ),
	    'warn_percent':  ( j['warn'] / float( total ) * 100 ),
	    'error_percent':  ( j['error'] / float( total ) * 100 ),
	    'unknown_percent':  ( j['unknown'] / float( total ) * 100 )
    }
    j.update(extra_stats)
    j['total_state'] = total
    j["total_no_ack"] = total_not_acknowledged 
    j["total_ack"] = total_acknowledged
    j["total_downtime"] = total_in_downtime
    j["total_no_downtime"] = total_not_in_downtime
    j["total_enabled"] = total_enabled
    j["total_disabled"] = total_disabled

    print j

    return j

#------------------------------------------------------------------------------
def host_service_stats(host_name):
    """ Gather all the services stats for a certain hosts. """
    return service_stats(extra_filter="host_name = %s" % host_name)

#------------------------------------------------------------------------------
def hosts_stats(extra_filter=None):
    for single_filter in extra_filter:
        if 'state ' in single_filter:
            extra_filter.remove(single_filter)
 
    s = query(
"""GET hosts
Stats: state = 0
Stats: state = 0
Stats: acknowledged = 0
StatsAnd: 2
Stats: state = 0
Stats: acknowledged = 1
StatsAnd: 2
Stats: state = 1
Stats: state = 1
Stats: acknowledged = 0
StatsAnd: 2
Stats: state = 1
Stats: acknowledged = 1
StatsAnd: 2
Stats: state = 2
Stats: state = 2
Stats: acknowledged = 0
StatsAnd: 2
Stats: state = 2
Stats: acknowledged = 1
StatsAnd: 2
Stats: state = 3
Stats: state = 3
Stats: acknowledged = 0
StatsAnd: 2
Stats: state = 3
Stats: acknowledged = 1
StatsAnd: 2
""", return_type='row', extra_filter=extra_filter  )

    total_state = {}
    total_acknowledged = {}
    total_not_acknowledged = {}
    total_in_downtime = {}
    total_not_in_downtime = {}
    total_enabled = {}
    total_disabled = {}

    z = query(
"""GET hosts
Stats: state != 9999
Columns: state acknowledged scheduled_downtime_depth checks_enabled
""", return_type='table', extra_filter=extra_filter  )

    for group in z:
        (state, acknowledged, scheduled_downtime_depth, checks_enabled, count ) = group
        acknowledged = int( acknowledged )
        scheduled_downtime_depth = int( scheduled_downtime_depth )
        checks_enabled = int( checks_enabled)
        if state == '0':
            state = 'ok'
        if state == '1':
            state = 'warning'
        if state == '2':
            state = 'error'
        if state == '3':
            state = 'unknown'
        if state not in total_state:
            total_state[ state ] = 0
            total_acknowledged[ state ] = 0
            total_not_acknowledged[ state ] = 0
            total_in_downtime[ state ] = 0
            total_not_in_downtime[ state ] = 0
            total_enabled[ state ] = 0
            total_disabled[ state ] = 0


        if acknowledged == 1:
            total_acknowledged[ state ] += count
        else:
            total_not_acknowledged[ state ] += count

        if scheduled_downtime_depth == 1:
            total_in_downtime[ state ] += count
        else:
            total_not_in_downtime[ state ] += count

        if checks_enabled == 1:
            total_enabled[ state ] += count
        else:
            total_disabled[ state ] += count


        total_state[ state ] += count

    j = {
	# OK status
	'ok': int(s[0]),
	'ok_not_ack': int(s[1]),
	'ok_ack': int(s[2]),
	# Warnings
	'warn': int(s[3]),
	'warn_not_ack': int(s[4]),
	'warn_ack': int(s[5]),
	# Warnings
	'error': int(s[6]),
	'error_not_ack': int(s[7]),
	'error_ack': int(s[8]),
	# Unknown
	'unknown': int(s[9]),
	'unknown_not_ack': int(s[10]),
	'unknown_ack': int(s[11])
   }
   # do math after we have some nicer names
    total = j['ok'] + j['warn'] + j['error'] + j['unknown']
    extra_stats = {
        # total
        'total': total,
        # total_percent
	'ok_percent':  ( j['ok'] / float( total ) * 100 ),
	'warn_percent':  ( j['warn'] / float( total ) * 100 ),
	'error_percent':  ( j['error'] / float( total ) * 100 ),
	'unknown_percent':  ( j['unknown'] / float( total ) * 100 ),
        # ack_percent
	'ok_ack_percent':  ( j['ok_ack'] / float( total ) * 100 ),
	'warn_ack_percent':  ( j['warn_ack'] / float( total ) * 100 ),
	'error_ack_percent':  ( j['error_ack'] / float( total ) * 100 ),
	'unknown_ack_percent':  ( j['unknown_ack'] / float( total ) * 100 ),
        # not_ack_percent
	'ok_not_ack_percent':  ( j['ok_not_ack'] / float( total ) * 100 ),
	'warn_not_ack_percent':  ( j['warn_not_ack'] / float( total ) * 100 ),
	'error_not_ack_percent':  ( j['error_not_ack'] / float( total ) * 100 ),
	'unknown_not_ack_percent':  ( j['unknown_not_ack'] / float( total ) * 100 )
   }
    j.update(extra_stats)
    j['total_state'] = total
    j["total_no_ack"] = total_not_acknowledged 
    j["total_ack"] = total_acknowledged
    j["total_downtime"] = total_in_downtime
    j["total_no_downtime"] = total_not_in_downtime
    j["total_enabled"] = total_enabled
    j["total_disabled"] = total_disabled
    return j


#------------------------------------------------------------------------------
if __name__ == "__main__":
    print get_host("localhost")
