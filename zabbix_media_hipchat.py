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
    json_body_dict['color'] = get_color(args['status'], args['nseverity'])
    json_body_dict['message'] = get_message(args['alert'])
    json_body_dict['notify'] = True
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
            keys       values
            room       ID or name of the room which the alert is sent to
                       as an "@all" mentioning message. Required.
            auth_token Bearer token to authenticate API access against
                       HipChat API version 2. Required.

        Format of `metadata` string:
            A list of key/value paris in the form `key1=value1,key2=value2`.
            keys       values
            status     Status of the alert. 'OK' will set the background color
                       of the message to 'green' irrespective of the severity
                       of the alert. If not specified, or anything other than
                       'OK' was specified, background color is determined by
                       `nseverity`.
            nseverity  Numerical severity of the alert (0 <= n <= 5).
                       Background color of the message sent to HipChat will be
                       set according to this value. If not specified, 'High'
                       is used as a default.
        ''')

    option_parser = optparse.OptionParser(
        usage=usage,
        version=version,
        description=description,
        formatter=PlainTextEpilogFormatter(),
        epilog=epilog,
    )

    (_, parsed_arguments) = option_parser.parse_args()

    returned_arguments = {}

    try:
        if len(parsed_arguments) != 3:
            raise IndexError
        else:
            destination = parsed_arguments[0]
            metadata = parsed_arguments[1]
            returned_arguments['alert'] = parsed_arguments[2]

        for key_value in destination.split(','):
            if key_value:
                key, value = key_value.split('=', 1)

                if key in ['room', 'auth_token']:
                    returned_arguments[key] = str(value)
                else:
                    raise KeyError

        for key_value in metadata.split(','):
            if key_value:
                key, value = key_value.split('=', 1)

                if key == 'status':
                    returned_arguments[key] = str(value)
                elif key == 'nseverity':
                    returned_arguments[key] = int(value)
                else:
                    raise KeyError

        if not 'room' in returned_arguments:
            raise KeyError

        if not 'auth_token' in returned_arguments:
            raise KeyError

    except (IndexError, KeyError, ValueError):
        option_parser.print_help()
        sys.exit(2)

    return returned_arguments


def get_color(status, nseverity):
    numerical_severity_color_map = {
        0: 'gray',
        1: 'purple',
        2: 'yellow',
        3: 'red',
        4: 'red',
        5: 'red',
    }

    if status == 'OK':
        color = 'green'
    else:
        try:
            color = numerical_severity_color_map[nseverity]
        except KeyError:
            color = 'red'

    return color


def get_message(message):
    return textwrap.dedent('''\
        @all %s
    ''' % message)


if __name__ == '__main__':
    main()
