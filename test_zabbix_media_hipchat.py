import optparse
import pytest

from zabbix_media_hipchat import PlainTextEpilogFormatter
from zabbix_media_hipchat import get_arguments
from zabbix_media_hipchat import main
from zabbix_media_hipchat import parse_alert
from zabbix_media_hipchat import parse_destination
from zabbix_media_hipchat import parse_metadata


class TestPlainTextEpilogFormatter(object):
    def test_epilog_with_blank(self):
        test_input = ''
        test_output = ''
        ptef = PlainTextEpilogFormatter()
        assert test_output == ptef.format_epilog(test_input)

    def test_epilog_with_content(self):
        test_input = 'a'
        test_output = '\na\n'
        ptef = PlainTextEpilogFormatter()
        assert test_output == ptef.format_epilog(test_input)


class TestGetArguments(object):
    def test_success(self, monkeypatch):
        input_destination = 'room=123456,auth_token=' + 'a' * 40
        input_metadata = 'status=PROBLEM,nseverity=5,notify=true'
        input_alert = 'Test Alert'
        output = {
            'room': '123456',
            'auth_token': 'a' * 40,
            'color': 'red',
            'notify': True,
            'alert': '@all Test Alert',
        }

        def mock_get_args(self, args):
            return [input_destination, input_metadata, input_alert]
        monkeypatch.setattr(optparse.OptionParser, '_get_args', mock_get_args)
        assert output == get_arguments()

    def test_failure(self, monkeypatch):
        input_destination = 'room=123456,auth_token=' + 'a' * 40
        input_metadata = 'status=PROBLEM,nseverity=5,notify=true'

        def mock_get_args(self, args):
            return [input_destination, input_metadata]
        monkeypatch.setattr(optparse.OptionParser, '_get_args', mock_get_args)
        with pytest.raises(SystemExit):
            get_arguments()


class TestParseAlert(object):
    def test_when_short(self):
        test_input = 'a'
        test_output = {'alert': '@all a'}
        assert test_output == parse_alert(test_input)

    def test_when_below_limit(self):
        test_input = 'a' * 9993
        test_output = {'alert': '@all ' + 'a' * 9993}
        assert test_output == parse_alert(test_input)

    def test_when_over_limit(self):
        test_input = 'a' * 9994
        test_output = {'alert': '@all ' + 'a' * 9990 + ' ...'}
        assert test_output == parse_alert(test_input)


class TestParseDestination(object):
    def test_blank_string(self):
        test_input = ''
        with pytest.raises(KeyError):
            parse_destination(test_input)

    def test_no_room(self):
        test_input = 'auth_token=' + 'a' * 40
        with pytest.raises(KeyError):
            parse_destination(test_input)

    def test_room_too_short(self):
        test_input = 'room=,auth_token=' + 'a' * 40
        with pytest.raises(KeyError):
            parse_destination(test_input)

    def test_room_boundary_short(self):
        test_input = 'room=' + 'a' + ',auth_token=' + 'a' * 40
        test_output = {'room': 'a', 'auth_token': 'a' * 40}
        assert test_output == parse_destination(test_input)

    def test_room_boundary_long(self):
        test_input = 'room=' + 'a' * 100 + ',auth_token=' + 'a' * 40
        test_output = {'room': 'a' * 100, 'auth_token': 'a' * 40}
        assert test_output == parse_destination(test_input)

    def test_room_too_long(self):
        test_input = 'room=' + 'a' * 101 + ',auth_token=' + 'a' * 40
        with pytest.raises(ValueError):
            parse_destination(test_input)

    def test_no_auth_key(self):
        test_input = 'room=123456'
        with pytest.raises(KeyError):
            parse_destination(test_input)

    def test_auth_key_too_short(self):
        test_input = 'room=123456,auth_token='
        with pytest.raises(KeyError):
            parse_destination(test_input)

    def test_auth_key_boundary_short(self):
        test_input = 'room=123456,auth_token=a'
        test_output = {'room': '123456', 'auth_token': 'a'}
        assert test_output == parse_destination(test_input)

    def test_undefined_key(self):
        test_input = 'room=123456,auth_token=' + 'a' * 40 + ',a=b'
        test_output = {'room': '123456', 'auth_token': 'a' * 40}
        assert test_output == parse_destination(test_input)

    def test_blank_around_delimiters(self):
        test_input = ' room = 123456 , auth_token = ' + 'a' * 40 + ' '
        test_output = {'room': '123456', 'auth_token': 'a' * 40}
        assert test_output == parse_destination(test_input)


class TestParseMetadata(object):
    def test_blank_string(self):
        test_input = ''
        test_output = {'color': 'red', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_status_with_empty_value(self):
        test_input = 'status='
        test_output = {'color': 'red', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_status_with_capital_key(self):
        test_input = 'STATUS=OK'
        test_output = {'color': 'green', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_status_with_capital_ok(self):
        test_input = 'status=OK'
        test_output = {'color': 'green', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_status_with_small_ok(self):
        test_input = 'status=ok'
        test_output = {'color': 'green', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_status_with_else(self):
        test_input = 'status=PROBLEM'
        test_output = {'color': 'red', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_nseverity_with_empty_value(self):
        test_input = 'nseverity='
        test_output = {'color': 'red', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_nseverity_0(self):
        test_input = 'nseverity=0'
        test_output = {'color': 'gray', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_nseverity_1(self):
        test_input = 'nseverity=1'
        test_output = {'color': 'purple', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_nseverity_2(self):
        test_input = 'nseverity=2'
        test_output = {'color': 'yellow', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_nseverity_3(self):
        test_input = 'nseverity=3'
        test_output = {'color': 'red', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_nseverity_4(self):
        test_input = 'nseverity=4'
        test_output = {'color': 'red', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_nseverity_5(self):
        test_input = 'nseverity=5'
        test_output = {'color': 'red', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_nseverity_else(self):
        test_input = 'nseverity=a'
        test_output = {'color': 'red', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_nseverity_with_status_OK(self):
        test_input = 'status=OK,nseverity=5'
        test_output = {'color': 'green', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_nseverity_with_status_else(self):
        test_input = 'status=PROBLEM,nseverity=5'
        test_output = {'color': 'red', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_notify_false(self):
        test_input = 'notify=false'
        test_output = {'color': 'red', 'notify': False}
        assert test_output == parse_metadata(test_input)

    def test_notify_off(self):
        test_input = 'notify=off'
        test_output = {'color': 'red', 'notify': False}
        assert test_output == parse_metadata(test_input)

    def test_notify_no(self):
        test_input = 'notify=no'
        test_output = {'color': 'red', 'notify': False}
        assert test_output == parse_metadata(test_input)

    def test_notify_0(self):
        test_input = 'notify=0'
        test_output = {'color': 'red', 'notify': False}
        assert test_output == parse_metadata(test_input)

    def test_notify_else(self):
        test_input = 'notify=a'
        test_output = {'color': 'red', 'notify': True}
        assert test_output == parse_metadata(test_input)

    def test_blank_around_delimiters(self):
        test_input = ' status = OK , nseverity = 5 , notify = false , a = b '
        test_output = {'color': 'green', 'notify': False}
        assert test_output == parse_metadata(test_input)

    def test_undefined_key(self):
        test_input = 'status=OK,nseverity=5,notify=false,a=b'
        test_output = {'color': 'green', 'notify': False}
        assert test_output == parse_metadata(test_input)
