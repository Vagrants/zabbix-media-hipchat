#!/usr/bin/env python

"""
Send alert to HipChat room mentioning everyone.
"""

__version__ = '0.1.1'

import optparse
import sys
import textwrap
import urllib2

try:
    import json
except ImportError:
    import simplejson as json


def main():
    args = get_arguments()

    json_body_dict = {}
    json_body_dict['color'] = args['color']
    json_body_dict['message'] = args['alert']
    json_body_dict['notify'] = args['notify']
    json_body_dict['message_format'] = 'text'
    json_body_str = json.dumps(json_body_dict)

    handler = urllib2.HTTPSHandler()
    opener_director = urllib2.build_opener(handler)
    request = urllib2.Request(API_ENDPOINT_ROOM % args['room'])
    request.add_data(json_body_str)
    request.add_header('Authorization', 'Bearer %s' % args['auth_token'])
    request.add_header('Content-Type', 'application/json')

    try:
        opener_director.open(request)
    except urllib2.HTTPError, code:
        sys.stderr.write(str(code) + '\n')
        sys.exit(1)
    except urllib2.URLError, reason:
        sys.stderr.write(str(reason) + '\n')
        sys.exit(1)


API_ENDPOINT_ROOM = 'https://api.hipchat.com/v2/room/%s/notification'


class PlainTextEpilogFormatter(optparse.IndentedHelpFormatter):
    def format_epilog(self, epilog):
        if epilog:
            return "\n" + epilog + "\n"
        else:
            return ""


def get_arguments():
    usage = '%prog [options] "destination" "metadata" "alert"'
    version = '%%prog %s' % __version__
    description = 'Send zabbix alert to HipChat.'

    epilog = textwrap.dedent('''\
        Positional arguments:
            destination     string representing the destination of the alert
            metadata        string representing alert metadata
            alert           body of the alert

        Format of `destination` string:
            A list of key/value paris in the form `key1=value1,key2=value2`.
            key        value
            room       ID or name of the room which the alert is sent to
                       as an "@all" mentioning message. Required.
            auth_token Bearer token to authenticate API access against
                       HipChat API version 2. Required.

        Format of `metadata` string:
            A list of key/value paris in the form `key1=value1,key2=value2`.
            key        value
            status     Status of the alert. 'OK' will set the background color
                       of the message to 'green' irrespective of the severity
                       of the alert. If not specified, or anything other than
                       'OK' was specified, background color is determined by
                       `nseverity`.
            nseverity  Numerical severity of the alert (0 <= n <= 5).
                       Background color of the message sent to HipChat will be
                       set according to this value. If not specified, 'High'
                       is used as a default.
            notify     Wether or not to trigger notifications(both in-app
                       notification and offline / idle notifications).
                       To not trigger notifications, value has to be one of
                       'false', 'off', 'no', '0' (case insensitive). Any thing
                       other than these values will trigger the notification.
        ''')

    option_parser = optparse.OptionParser(
        usage=usage,
        version=version,
        description=description,
        formatter=PlainTextEpilogFormatter(),
        epilog=epilog,
    )

    (_, args) = option_parser.parse_args()

    dictionary = {}

    try:
        if len(args) == 3:
            dictionary.update(parse_destination(args[0]))
            dictionary.update(parse_metadata(args[1]))
            dictionary.update(parse_alert(args[2]))
        else:
            raise IndexError

    except (IndexError, KeyError, ValueError):
        option_parser.print_help()
        sys.exit(2)

    return dictionary


def parse_destination(string):
    dictionary = {}
    room = None
    auth_token = None

    for kv_pair in string.split(','):
        if kv_pair:
            key, value = kv_pair.split('=', 1)
            key = key.strip().lower()

            if key == 'room':
                room = value
            elif key == 'auth_token':
                auth_token = value
            else:
                pass

    if room:
        if 1 <= len(str(room)) <= 100:
            room = str(room)
        else:
            raise ValueError
    else:
        raise KeyError

    if auth_token:
        if 1 <= len(str(auth_token)):
            auth_token = str(auth_token)
        else:
            raise ValueError
    else:
        raise KeyError

    dictionary['room'] = room
    dictionary['auth_token'] = auth_token
    return dictionary


def parse_metadata(string):
    nseverity_color_map = {
        0: 'gray',
        1: 'purple',
        2: 'yellow',
        3: 'red',
        4: 'red',
        5: 'red',
    }

    dictionary = {}
    status = None
    nseverity = None
    notify = None

    for kv_pair in string.split(','):
        if kv_pair:
            key, value = kv_pair.split('=', 1)
            key = key.strip().lower()

            if key == 'status':
                status = value
            elif key == 'nseverity':
                nseverity = value
            elif key == 'notify':
                notify = value
            else:
                pass

    if str(status).upper() == 'OK':
        color = 'green'
    else:
        try:
            color = nseverity_color_map[int(nseverity)]
        except (KeyError, ValueError):
            color = 'red'

    if str(notify).lower() in ['false', 'off', 'no', '0']:
        notify = False
    else:
        notify = True

    dictionary['color'] = color
    dictionary['notify'] = notify
    return dictionary


def parse_alert(string):
    dictionary = {}

    alert = str(string)

    if len(alert) > 9993:
        alert = '@all %s ...' % alert[0:9990]
    else:
        alert = '@all %s' % alert

    dictionary['alert'] = alert
    return dictionary


if __name__ == '__main__':
    main()
