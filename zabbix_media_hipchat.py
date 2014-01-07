#!/usr/bin/env python

"""
Send alert to HipChat room mentioning everyone.
"""

__version__ = '0.1.0'

import json
import optparse
import sys
import textwrap
import urllib2


def main():
    arguments = return_options_and_arguments()
    (room, params, message) = arguments

    json_body_dict = {}
    json_body_dict['color'] = return_color(params[1], params[2])
    json_body_dict['message'] = return_message_body(message)
    json_body_dict['notify'] = True
    json_body_dict['message_format'] = 'text'
    json_body_str = json.dumps(json_body_dict)

    handler = urllib2.HTTPSHandler()
    opener_director = urllib2.build_opener(handler)
    request = urllib2.Request(API_ENDPOINT_ROOM.format(room))
    request.add_data(json_body_str)
    request.add_header('Authorization', 'Bearer {0}'.format(params[0]))
    request.add_header('Content-Type', 'application/json')

    try:
        opener_director.open(request)
    except urllib2.HTTPError, code:
        print('{0}'.format(code))
        sys.exit(1)
    except urllib2.URLError, reason:
        print('{0}'.format(reason))
        sys.exit(1)


API_ENDPOINT_ROOM = 'https://api.hipchat.com/v2/room/{0}/notification'


class PlainTextEpilogFormatter(optparse.IndentedHelpFormatter):
    def format_epilog(self, epilog):
        if epilog:
            return "\n" + epilog + "\n"
        else:
            return ""


def return_options_and_arguments():
    optparse_usage = '%prog [options] "auth_token" "to" "subject" "message"'

    optparse_version = '%prog {0}'.format(__version__)

    optparse_description = textwrap.dedent('''\
        Send alert to HipChat room mentioning everyone.
    ''')

    optparse_epilog = textwrap.dedent('''\
        positional arguments:
            room            ID of the room which message will be sent to.
            params          Comma separated values of following(in order):
                auth_token      Bearer token to authenticate API access against
                                HipChat API version 2.
                status          Severity of the alert. Either one of default
                                verbal severities defined by zabbix ('Average',
                                'High', ...) or numerical severity defined by
                                zabbix (0 <= n <= 5). Background color of the
                                message sent to HipChat will be set according
                                to this option.  If not specified, 'High' is
                                used as a default.
                severity        Status of the alert. 'OK' will set the
                                background color to 'green' irrespective of
                                the severity of the alert. If not specified, or
                                anything else than 'OK' was specified,
                                'PROBLEM' is used as a default.
                            Latter one or two values can be omitted.
                            Example: 'token123:PROBLEM:Disaster'
            message        Rest of the body of the message.
    ''')

    option_parser = optparse.OptionParser(
        usage=optparse_usage,
        version=optparse_version,
        description=optparse_description,
        formatter=PlainTextEpilogFormatter(),
        epilog=optparse_epilog,
    )

    (_, arguments) = option_parser.parse_args()

    if len(arguments) != 3:
        option_parser.print_help()
        sys.exit(2)
    else:
        (room, params, message) = arguments

    params = params.split(',')

    if len(params) == 1:
        params.append(None)
        params.append(None)
    elif len(params) == 2:
        params.append(None)
    elif len(params) == 3:
        pass
    else:
        option_parser.print_help()
        sys.exit(2)

    return (room, params, message)


def return_color(status, severity):
    msg_color_map_verbal = {
        'Not classified': 'gray',
        'Information': 'purple',
        'Warning': 'yellow',
        'Average': 'red',
        'High': 'red',
        'Disaster': 'red',
    }

    msg_color_map_numerical = {
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
            color_from_verbal = msg_color_map_verbal[severity]
        except KeyError:
            color_from_verbal = None

        try:
            color_from_numerical = msg_color_map_numerical[severity]
        except KeyError:
            color_from_numerical = None

        if color_from_verbal:
            color = color_from_verbal
        elif color_from_numerical:
            color = color_from_numerical
        else:
            color = 'red'

    return color


def return_message_body(message):
    return textwrap.dedent('''\
        @all
        {0}
    ''').format(message)


if __name__ == '__main__':
    main()
