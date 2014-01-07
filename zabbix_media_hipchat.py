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
    arguments = get_arguments()
    room = arguments['room']
    auth_token = arguments['auth_token']
    status = arguments['status']
    severity = arguments['severity']
    message = arguments['message']

    json_body_dict = {}
    json_body_dict['color'] = return_color(status, severity)
    json_body_dict['message'] = return_message_body(message)
    json_body_dict['notify'] = True
    json_body_dict['message_format'] = 'text'
    json_body_str = json.dumps(json_body_dict)

    handler = urllib2.HTTPSHandler()
    opener_director = urllib2.build_opener(handler)
    request = urllib2.Request(API_ENDPOINT_ROOM.format(room))
    request.add_data(json_body_str)
    request.add_header('Authorization', 'Bearer {0}'.format(auth_token))
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


def get_arguments():
    usage = '%prog [options] "room" "params" "message"'

    version = '%prog {0}'.format(__version__)

    description = textwrap.dedent('''\
        Send alert to HipChat room mentioning everyone.
    ''')

    epilog = textwrap.dedent('''\
        positional arguments:
            room            ID of the room which the message is sent to.
            params          Comma separated values of following(in order):
                auth_token      Bearer token to authenticate API access against
                                HipChat API version 2. Required.
                status          Status of the alert. 'OK' will set the
                                background color to 'green' irrespective of
                                the severity of the alert. If not specified, or
                                anything else than 'OK' was specified, nothing
                                will happen.
                severity        Severity of the alert. Either one of default
                                verbal severities defined by zabbix ('Average',
                                'High', ...) or numerical severity defined by
                                zabbix (0 <= n <= 5). Background color of the
                                message sent to HipChat will be set according
                                to this value.  If not specified, 'High' is
                                used as a default.
                            Latter two values can be omitted.
                            Example: 'token123:PROBLEM:Disaster'
            message         Rest of the body of the message.
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

    if len(parsed_arguments) != 3:
        option_parser.print_help()
        sys.exit(2)
    else:
        returned_arguments['room'] = parsed_arguments[0]
        params = parsed_arguments[1].split(',')
        returned_arguments['message'] = parsed_arguments[2]

    if not 1 <= len(params) <= 3:
        option_parser.print_help()
        sys.exit(2)

    returned_arguments['auth_token'] = params[0]

    try:
        returned_arguments['status'] = params[1]
    except IndexError:
        returned_arguments['status'] = None

    try:
        returned_arguments['severity'] = params[2]
    except IndexError:
        returned_arguments['severity'] = None

    return returned_arguments


def return_color(status, severity):
    verbal_severity_color_map = {
        'Not classified': 'gray',
        'Information': 'purple',
        'Warning': 'yellow',
        'Average': 'red',
        'High': 'red',
        'Disaster': 'red',
    }

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
            color_from_verbal = verbal_severity_color_map[severity]
        except KeyError:
            color_from_verbal = None

        try:
            color_from_numerical = numerical_severity_color_map[severity]
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
