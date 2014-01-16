import collections
import httpretty
import pytest

try:
    import json
except ImportError:
    import simplejson as json

from zabbix_media_hipchat import ParameterError
from zabbix_media_hipchat import PlainTextEpilogFormatter
from zabbix_media_hipchat import get_arguments
from zabbix_media_hipchat import get_request
from zabbix_media_hipchat import main
from zabbix_media_hipchat import parse_alert
from zabbix_media_hipchat import parse_destination
from zabbix_media_hipchat import parse_kv_string
from zabbix_media_hipchat import parse_metadata


class TestPlainTextEpilogFormatter(object):
    @classmethod
    def setup_class(cls):
        cls.ptef = PlainTextEpilogFormatter()

    def test_epilog_with_blank(self):
        test_input = ''
        test_output = ''
        assert test_output == self.ptef.format_epilog(test_input)

    def test_epilog_with_content(self):
        test_input = 'a'
        test_output = '\na\n'
        assert test_output == self.ptef.format_epilog(test_input)


class TestGetArguments(object):
    @classmethod
    def setup_class(cls):
        cls.arguments = collections.namedtuple(
            'arguments',
            [
                'alert',
                'auth_token',
                'color',
                'notify',
                'room',
            ],
        )

        cls.input_alert = 'Test Alert'
        cls.input_destination = 'room=123456,auth_token=' + 'a' * 40
        cls.input_dummy = ''
        cls.input_metadata = 'status=PROBLEM,nseverity=5,notify=true'

        cls.output = cls.arguments(
            alert='@all Test Alert',
            auth_token='a'*40,
            color='red',
            notify=True,
            room='123456',
        )

    def test_2_arguments(self):
        with pytest.raises(ParameterError):
            get_arguments([
                self.input_destination,
                self.input_metadata,
            ])

    def test_3_arguments(self):
        assert self.output == get_arguments([
            self.input_destination,
            self.input_metadata,
            self.input_alert,
        ])

    def test_4_arguments(self):
        assert self.output == get_arguments([
            self.input_destination,
            self.input_metadata,
            self.input_alert,
            self.input_dummy,
        ])


class TestGetRequest(object):
    @classmethod
    def setup_class(cls):
        arguments = collections.namedtuple(
            'arguments', ['alert', 'auth_token', 'color', 'notify', 'room'],
        )

        cls.args = arguments(
            alert='Alert!',
            auth_token='a'*40,
            color='red',
            notify=True,
            room='123456',
        )
        cls.endpoint = 'https://api.hipchat.com/v2/room/%s/notification'

    def test_get_request(self):
        result = get_request(self.args, self.endpoint)
        result_data_dict = json.loads(result.get_data().decode('utf-8'))

        assert result_data_dict['color'] == 'red'
        assert result_data_dict['message'] == 'Alert!'
        assert result_data_dict['notify']
        assert result_data_dict['message_format'] == 'text'
        assert result.get_full_url() == (
            'https://api.hipchat.com/v2/room/123456/notification'
        )
        assert result.get_header('Authorization') == 'Bearer %s' % ('a' * 40)
        assert result.get_header('Content-type') == 'application/json'
        assert result.get_method() == 'POST'


class TestMain(object):
    @classmethod
    def setup_class(cls):
        cls.argv0 = 'zabbix_media_hipchat.py'
        cls.input_alert = 'Test Alert'
        cls.input_destination = 'room=123456,auth_token=' + 'a' * 40
        cls.input_metadata = 'status=PROBLEM,nseverity=5,notify=true'
        cls.args = [
            cls.argv0,
            cls.input_destination,
            cls.input_metadata,
            cls.input_alert,
        ]

        cls.request_body = {
            'color': 'red',
            'message': '@all Test Alert',
            'message_format': 'text',
            'notify': True,
        }

    @httpretty.activate
    def test_main_with_success(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://api.hipchat.com/v2/room/123456/notification',
        )

        assert 0 == main(self.args)

        request = httpretty.last_request()

        assert 'POST' == request.method
        assert 'Bearer %s' % ('a' * 40) == request.headers['Authorization']
        assert 'application/json' == request.headers['Content-Type']
        assert self.request_body == json.loads(request.body.decode('utf-8'))

    @httpretty.activate
    def test_main_with_http_error(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://api.hipchat.com/v2/room/123456/notification',
            status=500,
        )

        assert 1 == main(self.args)

    def test_main_with_invalid_args(self):
        assert 2 == main(self.args[:2])


class TestParseAlert(object):
    @classmethod
    def setup_class(cls):
        cls.alert = collections.namedtuple('alert', ['alert'])

    def test_when_short(self):
        test_input = 'a'
        test_output = self.alert(alert='@all a')
        assert test_output == parse_alert(test_input)

    def test_when_below_limit(self):
        test_input = 'a' * 9993
        test_output = self.alert(alert='@all '+'a'*9993)
        assert test_output == parse_alert(test_input)

    def test_when_over_limit(self):
        test_input = 'a' * 9994
        test_output = self.alert(alert='@all '+'a'*9990+' ...')
        assert test_output == parse_alert(test_input)


class TestParsedestination(object):
    @classmethod
    def setup_class(cls):
        cls.destination = collections.namedtuple(
            'destination', ['room', 'auth_token']
        )

    def test_blank_string(self):
        test_input = ''
        with pytest.raises(AttributeError):
            parse_destination(test_input)

    def test_no_room(self):
        test_input = 'auth_token=' + 'a' * 40
        with pytest.raises(AttributeError):
            parse_destination(test_input)

    def test_room_too_short(self):
        test_input = 'room=,auth_token=' + 'a' * 40
        with pytest.raises(ValueError):
            parse_destination(test_input)

    def test_room_boundary_short(self):
        test_input = 'room=' + 'a' + ',auth_token=' + 'a' * 40
        test_output = self.destination(room='a', auth_token='a'*40)
        assert test_output == parse_destination(test_input)

    def test_room_boundary_long(self):
        test_input = 'room=' + 'a' * 100 + ',auth_token=' + 'a' * 40
        test_output = self.destination(room='a'*100, auth_token='a'*40)
        assert test_output == parse_destination(test_input)

    def test_room_too_long(self):
        test_input = 'room=' + 'a' * 101 + ',auth_token=' + 'a' * 40
        with pytest.raises(ValueError):
            parse_destination(test_input)

    def test_no_auth_key(self):
        test_input = 'room=123456'
        with pytest.raises(AttributeError):
            parse_destination(test_input)

    def test_auth_key_too_short(self):
        test_input = 'room=123456,auth_token='
        with pytest.raises(ValueError):
            parse_destination(test_input)

    def test_auth_key_boundary_short(self):
        test_input = 'room=123456,auth_token=a'
        test_output = self.destination(room='123456', auth_token='a')
        assert test_output == parse_destination(test_input)

    def test_undefined_key(self):
        test_input = 'room=123456,auth_token=' + 'a' * 40 + ',a=b'
        test_output = self.destination(room='123456', auth_token='a'*40)
        assert test_output == parse_destination(test_input)


class TestParseKVString(object):
    @classmethod
    def kv_tuple(cls, field_names):
        return collections.namedtuple('key_values', field_names)

    def test_blank(self):
        test_input = ''
        test_output = None
        assert test_output == parse_kv_string(test_input)

    def test_single(self):
        test_input = 'a=b'
        test_output = self.kv_tuple(['a'])(a='b')
        assert test_output == parse_kv_string(test_input)

    def test_double(self):
        test_input = 'a=b,c=d'
        test_output = self.kv_tuple(['a', 'c'])(a='b', c='d')
        assert test_output == parse_kv_string(test_input)

    def test_with_empty_keyvalue(self):
        test_input = 'a=b,'
        test_output = self.kv_tuple(['a'])(a='b')
        assert test_output == parse_kv_string(test_input)

    def test_key_without_value(self):
        test_input = 'a=b,c='
        test_output = self.kv_tuple(['a', 'c'])(a='b', c='')
        assert test_output == parse_kv_string(test_input)

    def test_value_without_key(self):
        test_input = 'a=b,=d'
        test_output = self.kv_tuple(['a'])(a='b')
        assert test_output == parse_kv_string(test_input)

    def test_value_with_whitespaces(self):
        test_input = ' a = b , c = d '
        test_output = self.kv_tuple(['a', 'c'])(a='b', c='d')
        assert test_output == parse_kv_string(test_input)

    def test_value_with_equal(self):
        test_input = 'a=b,c=d=e'
        test_output = self.kv_tuple(['a', 'c'])(a='b', c='d=e')
        assert test_output == parse_kv_string(test_input)

    def test_key_with_capital(self):
        test_input = 'A=b,C=d'
        test_output = self.kv_tuple(['a', 'c'])(a='b', c='d')
        assert test_output == parse_kv_string(test_input)


class TestParsemetadata(object):
    @classmethod
    def setup_class(cls):
        cls.metadata = collections.namedtuple('metadata', ['color', 'notify'])

    def test_blank_string(self):
        test_input = ''
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_status_with_empty_value(self):
        test_input = 'status='
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_status_with_capital_ok(self):
        test_input = 'status=OK'
        test_output = self.metadata(color='green', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_status_with_small_ok(self):
        test_input = 'status=ok'
        test_output = self.metadata(color='green', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_status_with_else(self):
        test_input = 'status=PROBLEM'
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_nseverity_with_empty_value(self):
        test_input = 'nseverity='
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_nseverity_0(self):
        test_input = 'nseverity=0'
        test_output = self.metadata(color='gray', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_nseverity_1(self):
        test_input = 'nseverity=1'
        test_output = self.metadata(color='purple', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_nseverity_2(self):
        test_input = 'nseverity=2'
        test_output = self.metadata(color='yellow', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_nseverity_3(self):
        test_input = 'nseverity=3'
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_nseverity_4(self):
        test_input = 'nseverity=4'
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_nseverity_5(self):
        test_input = 'nseverity=5'
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_nseverity_else(self):
        test_input = 'nseverity=a'
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_nseverity_with_status_ok(self):
        test_input = 'status=OK,nseverity=5'
        test_output = self.metadata(color='green', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_nseverity_with_status_else(self):
        test_input = 'status=PROBLEM,nseverity=5'
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_notify_with_empty_value(self):
        test_input = 'notify='
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_notify_false(self):
        test_input = 'notify=false'
        test_output = self.metadata(color='red', notify=False)
        assert test_output == parse_metadata(test_input)

    def test_notify_off(self):
        test_input = 'notify=off'
        test_output = self.metadata(color='red', notify=False)
        assert test_output == parse_metadata(test_input)

    def test_notify_no(self):
        test_input = 'notify=no'
        test_output = self.metadata(color='red', notify=False)
        assert test_output == parse_metadata(test_input)

    def test_notify_0(self):
        test_input = 'notify=0'
        test_output = self.metadata(color='red', notify=False)
        assert test_output == parse_metadata(test_input)

    def test_notify_else(self):
        test_input = 'notify=a'
        test_output = self.metadata(color='red', notify=True)
        assert test_output == parse_metadata(test_input)

    def test_undefined_key(self):
        test_input = 'status=OK,nseverity=5,notify=false,a=b'
        test_output = self.metadata(color='green', notify=False)
        assert test_output == parse_metadata(test_input)
