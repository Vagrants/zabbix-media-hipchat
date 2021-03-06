#!/usr/bin/env python

"""
Send alert to HipChat room mentioning everyone.
"""

__version__ = '0.1.1'

import optparse
import sys
import textwrap

# pylint: disable=import-error, no-name-in-module
try:
    import json
except ImportError:
    import simplejson as json

try:
    from urllib2 import HTTPSHandler
except ImportError:
    from urllib.request import HTTPSHandler

try:
    from urllib2 import build_opener
except ImportError:
    from urllib.request import build_opener

try:
    from urllib2 import Request
except ImportError:
    from urllib.request import Request

try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.error import HTTPError

try:
    from urllib2 import URLError
except ImportError:
    from urllib.error import URLError
# pylint: enable=import-error, no-name-in-module


def main():
    """Main function.

    Generates an appropriate JSON and throws them to HipChat API.

    In case something happens(for example wrong token), prints error to stdout
    and exit with 1.
    """

    opener_director = build_opener(HTTPSHandler())

    args = get_arguments()
    request = get_request(args, API_ENDPOINT_ROOM)

    try:
        opener_director.open(request)
    except HTTPError:
        sys.stderr.write(str(sys.exc_info()[1]) + '\n')
        sys.exit(1)
    except URLError:
        sys.stderr.write(str(sys.exc_info()[1]) + '\n')
        sys.exit(1)


API_ENDPOINT_ROOM = 'https://api.hipchat.com/v2/room/%s/notification'


class PlainTextEpilogFormatter(optparse.IndentedHelpFormatter):
    """Format help.

    Format help with indented section body for heading and do virtually nothing
    for epilog.
    """

    def format_epilog(self, epilog):
        """Format epilog.

        Args:
            epilog (str): Body of epilog.

        Returns:
            str. Formatted body of epilog.
        """

        if epilog:
            return "\n" + epilog + "\n"
        else:
            return ""


def get_arguments():
    """Parse commandline arguments.

    Parse commandline arguments and returns a dict containing runtime
    parameters. Commandline arguments are (in order):

        ``destination``
            ``destination string``

        ``metadata``
            ``metadata string``

        ``alert``
            Body of the alert message.

    Every commandline arguments are required. A nice help message will be
    displayed when parsing of commandline arguments failed for some reason,
    or user supplied ``--help`` option.

    Returns:
        A dict containing the following:

        ================ ====================================================
        key              value
        room (str)       ID or name of the room which the message is sent to.
        auth_token (str) Bearer token to authenticate API access.
        color (str)      Background color of the message sent to HipChat.
        notify (bool)    Wether or not to trigger notifications.
        ================ ====================================================
    """

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
            A list of key/value paris in the form of `key1=value1,key2=value2`.
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
        dictionary.update(parse_destination(args[0]))
        dictionary.update(parse_metadata(args[1]))
        dictionary.update(parse_alert(args[2]))
    except (IndexError, KeyError, ValueError):
        option_parser.print_help()
        sys.exit(2)

    return dictionary


def parse_destination(string):
    """Parse ``destination string``.

    ``destination string`` is a list of key/value paris in the form of
    ``key1=value1,key2=value2``. Accepted keys and values are:

        ``room``
            ID or name of the room which the alert is sent to as an "@all"
            mentioning message. Required.
        ``auth_token``
            Bearer token to authenticate API access against HipChat API version
            2. Required.

    Args:
        string (str): ``destination string``.

    Returns:
        A dict containing the following:

        ================ ====================================================
        key              value
        room (str)       ID or name of the room which the message is sent to.
        auth_token (str) Bearer token to authenticate API access.
        ================ ====================================================

    Raises:
        * KeyError: Raised when required keys are not proveded.
        * ValueError: Raised when values are not acceptable.
    """

    dictionary = {}
    room = None
    auth_token = None

    for kv_pair in string.split(','):
        if kv_pair:
            key, value = kv_pair.split('=', 1)
            key = key.strip().lower()
            value = value.strip()

            if key == 'room':
                room = value
            elif key == 'auth_token':
                auth_token = value
            else:
                pass

    if not room:
        raise KeyError

    if not len(str(room)) <= 100:
        raise ValueError

    if not auth_token:
        raise KeyError

    dictionary['room'] = str(room)
    dictionary['auth_token'] = str(auth_token)
    return dictionary


def parse_metadata(string):
    """Parse ``metadata string``.

    ``metadata string`` is a list of key/value paris in the form of
    ``key1=value1,key2=value2``. Accepted keys and values are:

        ``status``
            Status of the alert. ``OK`` will set the background color of the
            message to green irrespective of the severity of the alert. If not
            specified, or anything other than ``OK`` was specified, background
            color is determined by ``nseverity``.

        ``nseverity``
            Numerical severity of the alert (0 <= n <= 5).  Background color of
            the message sent to HipChat will be determined according to this
            value. If not specified, ``High`` is used as a default.

        ``notify``
            Wether or not to trigger notifications(both in-app notification and
            offline / idle notifications). To not trigger notifications, value
            has to be one of ``false``, ``off``, ``no``, ``0`` (case
            insensitive). Any thing other than these values will trigger the
            notification.

    Args:
        string (str): ``metadata string``.

    Returns:
        A dict containing the following:

        ============= ================================================
        key           value
        color (str)   Background color of the message sent to HipChat.
        notify (bool) Wether or not to trigger notifications.
        ============= ================================================
    """

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
            value = value.strip()

            if key == 'status':
                status = value
            elif key == 'nseverity':
                nseverity = value
            elif key == 'notify':
                notify = value
            else:
                pass

    try:
        if str(status).upper() == 'OK':
            color = 'green'
        else:
            color = nseverity_color_map[int(nseverity)]
    except (KeyError, TypeError, ValueError):
        color = 'red'

    if str(notify).lower() in ['false', 'off', 'no', '0']:
        notify = False
    else:
        notify = True

    dictionary['color'] = color
    dictionary['notify'] = notify
    return dictionary


def parse_alert(string):
    """Format alert message before sending it to HipChat.

    Does 2 thins:
        * Prefix message with "@all" mention for messages to trigger
          notifications.
        * Truncate long messages so that they fits within the 10000 character
          limit of HipChat.

    Args:
        string (str): Body of the alert message.

    Returns:
        A dict containing the following:

        ===== =========================================
        key   value
        alert Formatted message.
        ===== =========================================
    """

    dictionary = {}

    alert = str(string)

    if len(alert) > 9993:
        alert = '@all %s ...' % alert[0:9990]
    else:
        alert = '@all %s' % alert

    dictionary['alert'] = alert
    return dictionary


def get_request(args, endpoint):
    request = Request(endpoint % args['room'])

    json_body_dict = {}
    json_body_dict['color'] = args['color']
    json_body_dict['message'] = args['alert']
    json_body_dict['notify'] = args['notify']
    json_body_dict['message_format'] = 'text'
    json_body_str = json.dumps(json_body_dict)
    request.add_data(json_body_str)

    request.add_header('Authorization', 'Bearer %s' % args['auth_token'])
    request.add_header('Content-type', 'application/json')

    return request


if __name__ == '__main__':
    main()
