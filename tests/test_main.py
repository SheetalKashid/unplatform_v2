# pylint: disable=unused-argument

import glob
import json
import shutil
import sqlite3

from copy import deepcopy

import os
import mock

from requests.exceptions import ConnectionError

import settings
from testing_utilities import BaseTestCase

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
ABS_PATH = '{0}'.format(os.path.abspath(os.path.join(PROJECT_PATH, os.pardir)))

SAMPLE_LOG = {
    "recordTypeIds": [],
    "id": "logging.Log%3A57b9547bed849b7a4208596b%40ODL.MIT.EDU",
    "displayName": {
        "text": "Default CLIx log",
        "languageTypeId": "639-2%3AENG%40ISO",
        "formatTypeId": "TextFormats%3APLAIN%40okapia.net",
        "scriptTypeId": "15924%3ALATN%40ISO"
    },
    "description": {
        "text": "For logging info from unplatform and tools, which do not know about catalog IDs",
        "languageTypeId": "639-2%3AENG%40ISO",
        "formatTypeId": "TextFormats%3APLAIN%40okapia.net",
        "scriptTypeId": "15924%3ALATN%40ISO"
    },
    "genusTypeId": "log-genus-type%3Adefault-clix%40ODL.MIT.EDU"
}

SAMPLE_ENTRY = {
    "id": "logging.LogEntry%3A57bfcc5ced849b11f52fc82a%40ODL.MIT.EDU",
    "displayName": {
        "text": "",
        "languageTypeId": "639-2%3AENG%40ISO",
        "scriptTypeId": "15924%3ALATN%40ISO",
        "formatTypeId": "TextFormats%3APLAIN%40okapia.net"
    },
    "description": {
        "text": "",
        "languageTypeId": "639-2%3AENG%40ISO",
        "scriptTypeId": "15924%3ALATN%40ISO",
        "formatTypeId": "TextFormats%3APLAIN%40okapia.net"
    },
    "recordTypeIds": [
        "logging.LogEntry%3Atext-blob%40ODL.MIT.EDU"
    ],
    "text": {
        "text": """{\"action\": \"pause audio\",
            \"questionId\": \"assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU\",
            \"assessmentOfferedId\": \"assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU\",
            \"mediaId\": \"\",
            \"mediaTime\": 9.142857}""",
        "languageTypeId": "639-2%3AENG%40ISO",
        "formatTypeId": "TextFormats%3APLAIN%40okapia.net",
        "scriptTypeId": "15924%3ALATN%40ISO"
    },
    "priorityId": "NoneType%3ANONE%40dlkit.mit.edu",
    "genusTypeId": "GenusType%3ADEFAULT%40DLKIT.MIT.EDU",
    "timestamp": {
        "hour": 4,
        "month": 8,
        "second": 4,
        "microsecond": 157476,
        "year": 2016,
        "tzinfo": None,
        "day": 26,
        "minute": 58
    },
    "assignedLogIds": [
        "logging.Log%3A57b9547bed849b7a4208596b%40ODL.MIT.EDU"
    ],
    "agentId": "osid.agent.Agent%3Aexternal_identifier%40MIT-ODL"
}


def osid_agent(name):
    return 'osid.agent.Agent%3A{0}%40MIT-ODL'.format(name)


# http://stackoverflow.com/questions/15753390/python-mock-requests-and-the-response#28507806
# This method will be used by the mock to replace requests.POST
def mocked_logging_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    response = deepcopy(SAMPLE_ENTRY)
    if 'headers' in kwargs:
        response['agentId'] = osid_agent(kwargs['headers']['x-api-proxy'])
    if 'json' in kwargs:
        blob = json.loads(response['text']['text'])
        if 'session_id' in kwargs['json']['data']:
            blob['session_id'] = kwargs['json']['data']['session_id']
        elif 'sessionId' in kwargs['json']['data']:
            blob['sessionId'] = kwargs['json']['data']['sessionId']
        elif 'user_id' in kwargs['json']['data']:
            blob['user_id'] = kwargs['json']['data']['user_id']
        elif 'userId' in kwargs['json']['data']:
            blob['userId'] = kwargs['json']['data']['userId']
        response['text']['text'] = json.dumps(blob)
    return MockResponse(response, 200)


# This method will be used by the mock to replace requests.get
def mocked_logging_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data
    if args[0] == "https://localhost:8080/api/v1/logging/logs":
        return MockResponse([SAMPLE_LOG], 200)
    return MockResponse([SAMPLE_ENTRY], 200)


class BaseMainTestCase(BaseTestCase):
    def setUp(self):
        super(BaseMainTestCase, self).setUp()
        self.db = sqlite3.connect('unplatform.sqlite3')

    def tearDown(self):
        super(BaseMainTestCase, self).tearDown()
        self.db.close()


class BasicServiceTests(BaseMainTestCase):
    """Test the views for getting the basic service calls

    """
    def num_sessions(self):
        cursor = self.db.execute('SELECT Count(*) FROM sessions')
        num_sessions = 0
        for row in cursor:
            num_sessions = row[0]  # returns a tuple with count in position 0, like (0,)
        return num_sessions

    def setUp(self):
        # pylint: disable=useless-super-delegation
        super(BasicServiceTests, self).setUp()
        # self.data_dir = '{0}/webapps/unplatform/sessions'.format(ABS_PATH)
        # if os.path.isdir(self.data_dir):
        #     shutil.rmtree(self.data_dir)
        # os.mkdir(self.data_dir)

    def tearDown(self):
        # pylint: disable=useless-super-delegation
        super(BasicServiceTests, self).tearDown()
        # if os.path.isdir(self.data_dir):
        #     shutil.rmtree(self.data_dir)

    def test_users_can_get_index_page(self):
        url = '/'
        req = self.app.get(url)
        self.ok(req)
        self.message(req, 'CLIx')

    def test_session_id_does_not_reset_on_index_get(self):
        self.assertEqual(self.num_sessions(), 0)
        req = self.app.get('/version')
        self.ok(req)

        self.assertEqual(self.num_sessions(), 1)

        req = self.app.get('/')
        self.ok(req)

        self.assertEqual(self.num_sessions(), 1)

    def test_can_get_storage_path(self):
        req = self.app.get('/datastore_path')
        self.ok(req)


class OEATests(BaseMainTestCase):
    """Test the views for getting the OEA player

    """
    def setUp(self):
        super(OEATests, self).setUp()
        self.oea_dir = '{0}/static/oea'.format(ABS_PATH)
        self.oea_index = '{0}/index.html'.format(self.oea_dir)
        if not os.path.exists(self.oea_dir):
            os.makedirs(self.oea_dir)
        if not os.path.isfile(self.oea_index):
            shutil.copyfile(
                '{0}/tests/fixtures/oea/index.html'.format(ABS_PATH),
                self.oea_index)

    def tearDown(self):
        super(OEATests, self).tearDown()
        if os.path.exists(self.oea_dir):
            shutil.rmtree(self.oea_dir)

    def test_user_without_active_session_cannot_get_oea_index(self):
        url = '/oea'
        req = self.app.get(url, expect_errors=True)
        self.code(req, 403)

        url = '/oea/'
        req = self.app.get(url, expect_errors=True)
        self.code(req, 403)

    def test_active_users_can_get_oea_index(self):
        self.login()
        url = '/oea'
        req = self.app.get(url)
        self.ok(req)
        self.message(req, 'Clix assessment activity')

    def test_users_can_get_oea_index_with_trailing_slash(self):
        self.login()
        url = '/oea/'
        req = self.app.get(url)
        self.ok(req)
        self.message(req, 'Clix assessment activity')


class ContentTests(BaseMainTestCase):
    """Test the views for getting the Content player

    """
    def setUp(self):
        super(ContentTests, self).setUp()
        self.logout()
        self.content_dir = '{0}/static/content_player'.format(ABS_PATH)
        self.content_index = '{0}/index.html'.format(self.content_dir)
        if not os.path.exists(self.content_dir):
            os.makedirs(self.content_dir)
        if not os.path.isfile(self.content_index):
            shutil.copyfile(
                '{0}/tests/fixtures/content/index.html'.format(ABS_PATH),
                self.content_index)

    def tearDown(self):
        super(ContentTests, self).tearDown()
        if os.path.exists(self.content_dir):
            shutil.rmtree(self.content_dir)

    # deprecate this test for performance reasons
    # def test_user_without_active_session_cannot_get_content_index(self):
    #     url = '/content/'
    #     req = self.app.get(url, expect_errors=True)
    #     self.code(req, 403)

    def test_users_can_get_content_index_with_trailing_slash(self):
        self.login()
        url = '/content/'
        req = self.app.get(url, expect_errors=True)
        self.code(req, 404)  # because there are no modules loaded


class ToolTests(BaseMainTestCase):
    """Test the views for getting the Tools

    """
    def setUp(self):
        super(ToolTests, self).setUp()
        self.logout()
        self.tool_dir = '{0}/modules/Tools/test_tool'.format(ABS_PATH)
        self.tool_index = '{0}/index.html'.format(self.tool_dir)
        if not os.path.exists(self.tool_dir):
            os.makedirs(self.tool_dir)
        if not os.path.isfile(self.tool_index):
            shutil.copyfile(
                '{0}/tests/fixtures/tool/index.html'.format(ABS_PATH),
                self.tool_index)

    def tearDown(self):
        super(ToolTests, self).tearDown()
        if os.path.exists(self.tool_dir):
            shutil.rmtree(self.tool_dir)

    def test_user_without_active_session_cannot_get_content_index(self):
        url = '/common/Open Story/'
        req = self.app.get(url, expect_errors=True)
        self.code(req, 403)

    def test_users_can_get_content_index_with_trailing_slash(self):
        self.login()
        url = '/common/Open Story/'
        req = self.app.get(url, expect_errors=True)
        self.ok(req)

    def test_passing_locale_to_tool_iframe_renders_the_language_param(self):
        self.login()
        url = '/common/test_tool?lang=hi'
        req = self.app.get(url)
        self.ok(req)
        self.assertEqual(req.body, 'hi\n')

    def test_not_passing_locale_to_tool_iframe_just_returns_raw_text(self):
        self.login()
        url = '/common/test_tool/'
        req = self.app.get(url)
        self.ok(req)
        self.assertEqual(req.body, '${lang}\n')

    def test_tool_not_found(self):
        self.login()
        url = '/common/fake_tool/'
        req = self.app.get(url,
                           status=404)
        self.code(req, 404)


class ModuleDirectoryListingTests(BaseMainTestCase):
    """Test the views for the GET modules endpoint

    """
    def setUp(self):
        super(ModuleDirectoryListingTests, self).setUp()
        self.url = '/modules_list'

    def tearDown(self):
        # pylint: disable=useless-super-delegation
        super(ModuleDirectoryListingTests, self).tearDown()

    def test_can_get_modules_listing(self):
        req = self.app.get(self.url)
        self.ok(req)
        # data = self.json(req)
        # self.assertTrue(len(data) > 0)


class ConfigurationTests(BaseMainTestCase):
    """Test the school configuration endpoints

    """
    def setUp(self):
        super(ConfigurationTests, self).setUp()
        self.url = '/api/v1/configuration'
        self.config_file = '{0}/webapps/unplatform/configuration/config.json'.format(ABS_PATH)
        if os.path.isfile(self.config_file):
            os.remove(self.config_file)

    def tearDown(self):
        super(ConfigurationTests, self).tearDown()
        if os.path.isfile(self.config_file):
            os.remove(self.config_file)

    def test_can_get_null_config(self):
        req = self.app.get(self.url)
        self.ok(req)
        data = self.json(req)
        self.assertEqual(data, {})

    def test_can_set_config(self):
        payload = {
            'state': 'FOO',
            'district': 'BAR',
            'schoolId': '123',
            'terminalId': '1',
            'locale': 'hi'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'})
        self.ok(req)
        data = self.json(req)
        for key in payload:
            self.assertEqual(data[key], payload[key])
        self.assertIn('timestamp', data.keys())

        self.assertTrue(os.path.isfile(self.config_file))
        with open(self.config_file, 'rb') as config:
            conf = json.load(config)
            for key in data:
                self.assertEqual(conf[key], data[key])

    def test_can_get_config(self):
        payload = {
            'state': 'FOO',
            'district': 'BAR',
            'schoolId': '123',
            'terminalId': '1',
            'locale': 'hi'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'})
        self.ok(req)
        data = self.json(req)
        for key in payload:
            self.assertEqual(data[key], payload[key])
        self.assertIn('timestamp', data.keys())

        req = self.app.get(self.url)
        self.ok(req)
        get_data = self.json(req)
        for key in payload:
            self.assertEqual(get_data[key], payload[key])
        self.assertIn('timestamp', get_data.keys())


class UserSurveyTests(BaseMainTestCase):
    """Test the user survey

    """
    def setUp(self):
        super(UserSurveyTests, self).setUp()
        self.url = '/api/v1/session'
        self.data_dir = '{0}/webapps/unplatform/user_data'.format(ABS_PATH)
        if os.path.isdir(self.data_dir):
            shutil.rmtree(self.data_dir)

    def tearDown(self):
        super(UserSurveyTests, self).tearDown()
        if os.path.isdir(self.data_dir):
            shutil.rmtree(self.data_dir)

    def test_can_set_survey_data(self):
        payload = {
            'userType': 'teacher',
            'userCount': '3+',
            'sessionId': 'foo'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'})
        self.ok(req)
        self.assertTrue(os.path.isdir(self.data_dir))
        for user_file in glob.iglob('{0}/*.json'.format(self.data_dir)):
            self.assertEqual(os.path.basename(user_file), 'foo.json')
            with open(user_file, 'rb') as user_data:
                data = json.load(user_data)
                self.assertIn('timestamp', data.keys())
                for key in payload:
                    self.assertEqual(payload[key], data[key])

    def test_can_get_session_id(self):
        self.login()
        req = self.app.get('/api/v1/session')
        self.ok(req)


class LoggingTests(BaseMainTestCase):
    """Test the logging endpoints with default log

    """
    def setUp(self):
        super(LoggingTests, self).setUp()
        self.url = '/api/appdata'
        # self.data_dir = '{0}/webapps/CLIx/datastore/logging'.format(ABS_PATH)
        # if os.path.isdir(self.data_dir):
        #     shutil.rmtree(self.data_dir)

    def tearDown(self):
        # pylint: disable=useless-super-delegation
        super(LoggingTests, self).tearDown()
        # if os.path.isdir(self.data_dir):
        #     shutil.rmtree(self.data_dir)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    def test_cannot_get_log_entries_with_inactive_session(self, mock_get):
        req = self.app.get(self.url, expect_errors=True)
        self.code(req, 403)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    def test_can_get_log_entries_if_active_session(self, mock_get):
        self.login()
        req = self.app.get(self.url)
        self.ok(req)
        data = self.json(req)
        self.assertEqual(len(data), 1)
        self.assertEqual(data, [SAMPLE_ENTRY])

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    @mock.patch('main.requests.post', side_effect=mocked_logging_post)
    def test_cannot_create_log_entry_with_inactive_session(self, mock_post, mock_get):
        payload = {
            'action': 'pause audio',
            'questionId': 'assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU',
            'assessmentOfferedId': 'assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU',
            'mediaId': '',
            'mediaTime': 9.142857
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'},
                            expect_errors=True)
        self.code(req, 403)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    @mock.patch('main.requests.post', side_effect=mocked_logging_post)
    def test_can_create_log_entry_with_active_session(self, mock_post, mock_get):
        self.login()
        payload = {
            'action': 'pause audio',
            'questionId': 'assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU',
            'assessmentOfferedId': 'assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU',
            'mediaId': '',
            'mediaTime': 9.142857
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'})
        self.ok(req)
        entry = self.json(req)
        self.assertTrue(
            json.loads(entry['text']['text']) == payload)
        self.assertEqual(
            entry['agentId'],
            osid_agent('none_provided')
        )

        call_params = mock_post.call_args_list[0][1]
        self.assertEqual(call_params['headers']['x-api-proxy'],
                         'none_provided')
        self.assertEqual(call_params['json']['data'], payload)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    @mock.patch('main.requests.post', side_effect=mocked_logging_post)
    def test_session_id_does_not_pass_through_to_header_if_provided_with_inactive_session(self, mock_post, mock_get):
        payload = {
            'action': 'pause audio',
            'questionId': 'assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU',
            'assessmentOfferedId': 'assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU',
            'mediaId': '',
            'mediaTime': 9.142857,
            'session_id': 'foo'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'},
                            expect_errors=True)
        self.code(req, 403)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    @mock.patch('main.requests.post', side_effect=mocked_logging_post)
    def test_session_id_passes_through_to_header_if_provided_with_active_session(self, mock_post, mock_get):
        self.login()
        payload = {
            'action': 'pause audio',
            'questionId': 'assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU',
            'assessmentOfferedId': 'assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU',
            'mediaId': '',
            'mediaTime': 9.142857,
            'session_id': 'foo'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'})
        self.ok(req)
        entry = self.json(req)
        self.assertTrue(
            json.loads(entry['text']['text']) == payload)
        self.assertEqual(
            entry['agentId'],
            osid_agent('foo')
        )

        call_params = mock_post.call_args_list[0][1]
        self.assertEqual(call_params['headers']['x-api-proxy'], 'foo')
        self.assertEqual(call_params['json']['data'], payload)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    @mock.patch('main.requests.post', side_effect=mocked_logging_post)
    def test_sessionId_does_not_pass_through_to_header_if_provided_with_inactive_session(self, mock_post, mock_get):
        payload = {
            'action': 'pause audio',
            'questionId': 'assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU',
            'assessmentOfferedId': 'assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU',
            'mediaId': '',
            'mediaTime': 9.142857,
            'sessionId': 'bar'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'},
                            expect_errors=True)
        self.code(req, 403)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    @mock.patch('main.requests.post', side_effect=mocked_logging_post)
    def test_sessionId_passes_through_to_header_if_provided_with_active_session(self, mock_post, mock_get):
        self.login()
        payload = {
            'action': 'pause audio',
            'questionId': 'assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU',
            'assessmentOfferedId': 'assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU',
            'mediaId': '',
            'mediaTime': 9.142857,
            'sessionId': 'bar'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'})
        self.ok(req)
        entry = self.json(req)
        self.assertTrue(
            json.loads(entry['text']['text']) == payload)
        self.assertEqual(
            entry['agentId'],
            osid_agent('bar')
        )

        call_params = mock_post.call_args_list[0][1]
        self.assertEqual(call_params['headers']['x-api-proxy'], 'bar')
        self.assertEqual(call_params['json']['data'], payload)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    @mock.patch('main.requests.post', side_effect=mocked_logging_post)
    def test_user_id_does_not_pass_through_to_header_if_provided_with_inactive_session(self, mock_post, mock_get):
        payload = {
            'action': 'pause audio',
            'questionId': 'assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU',
            'assessmentOfferedId': 'assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU',
            'mediaId': '',
            'mediaTime': 9.142857,
            'user_id': 'bar'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'},
                            expect_errors=True)
        self.code(req, 403)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    @mock.patch('main.requests.post', side_effect=mocked_logging_post)
    def test_user_id_passes_through_to_header_if_provided_with_active_session(self, mock_post, mock_get):
        self.login()
        payload = {
            'action': 'pause audio',
            'questionId': 'assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU',
            'assessmentOfferedId': 'assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU',
            'mediaId': '',
            'mediaTime': 9.142857,
            'user_id': 'bar'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'})
        self.ok(req)
        entry = self.json(req)
        self.assertTrue(
            json.loads(entry['text']['text']) == payload)
        self.assertEqual(
            entry['agentId'],
            osid_agent('bar')
        )

        call_params = mock_post.call_args_list[0][1]
        self.assertEqual(call_params['headers']['x-api-proxy'], 'bar')
        self.assertEqual(call_params['json']['data'], payload)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    @mock.patch('main.requests.post', side_effect=mocked_logging_post)
    def test_userId_does_not_pass_through_to_header_if_provided_with_inactive_session(self, mock_post, mock_get):
        payload = {
            'action': 'pause audio',
            'questionId': 'assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU',
            'assessmentOfferedId': 'assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU',
            'mediaId': '',
            'mediaTime': 9.142857,
            'userId': 'bar'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'},
                            expect_errors=True)
        self.code(req, 403)

    @mock.patch('main.requests.get', side_effect=mocked_logging_get)
    @mock.patch('main.requests.post', side_effect=mocked_logging_post)
    def test_userId_passes_through_to_header_if_provided_with_active_session(self, mock_post, mock_get):
        self.login()
        payload = {
            'action': 'pause audio',
            'questionId': 'assessment.Item%3A57b954e0ed849b7a420859dc%40ODL.MIT.EDU',
            'assessmentOfferedId': 'assessment.AssessmentOffered:57bfcc21ed849b11f52fc80a@ODL.MIT.EDU',
            'mediaId': '',
            'mediaTime': 9.142857,
            'userId': 'bar'
        }

        req = self.app.post(self.url,
                            params=json.dumps(payload),
                            headers={'content-type': 'application/json'})
        self.ok(req)
        entry = self.json(req)
        self.assertTrue(
            json.loads(entry['text']['text']) == payload)
        self.assertEqual(
            entry['agentId'],
            osid_agent('bar')
        )

        call_params = mock_post.call_args_list[0][1]
        self.assertEqual(call_params['headers']['x-api-proxy'], 'bar')
        self.assertEqual(call_params['json']['data'], payload)

    @mock.patch('requests.get')
    def test_get_log_with_default_log_present(self,
                                              MockGet):
        class FakeGet:
            @staticmethod
            def json():
                return [{
                    'genusTypeId': settings.DEFAULT_LOG_GENUS_TYPE,
                    'id': 'foo'
                }]

        MockGet.return_value = FakeGet

        self.login()
        req = self.app.get(self.url)
        self.ok(req)
        data = self.json(req)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], 'foo')

    @mock.patch('requests.post')
    @mock.patch('requests.get')
    def test_get_log_with_no_default_log(self,
                                         MockGet,
                                         MockPost):
        class FakeGet:
            @staticmethod
            def json():
                return []

        class FakePost:
            @staticmethod
            def json():
                return {
                    'id': 'foo2'
                }

        MockGet.return_value = FakeGet
        MockPost.return_value = FakePost

        self.login()
        req = self.app.get(self.url)
        self.ok(req)
        data = self.json(req)
        self.assertEqual(len(data), 0)  # from FakeGet

    @mock.patch('main.generic_logging._get_log')
    def test_get_with_connection_error(self, MockGet):
        def side_effect():
            raise ConnectionError()

        MockGet.side_effect = side_effect
        self.login()
        req = self.app.get(self.url)
        self.ok(req)
        data = self.json(req)
        self.assertEqual(data, [])

    @mock.patch('main.generic_logging._get_log')
    def test_post_with_connection_error(self, MockGet):
        def side_effect():
            raise ConnectionError()

        MockGet.side_effect = side_effect
        self.login()
        req = self.app.post(self.url,
                            params={})
        self.ok(req)
        data = self.json(req)
        self.assertIn('msg', data)


class ContentStreamingTests(BaseMainTestCase):
    def setUp(self):
        super(ContentStreamingTests, self).setUp()
        self.url_path = '{0}/tests/fixtures/modules'.format(
            ABS_PATH)

    @mock.patch('os.path.join')
    def test_can_stream_content(self, MockJoin):
        MockJoin.return_value = '{0}/fake-styles.css'.format(
            self.url_path)
        req = self.app.get('/content/fake-styles.css',
                           status=206)
        self.code(req, 206)
        text = req.body
        self.assertIn('body', text)

    @mock.patch('os.path.join')
    def test_404_when_file_not_found(self, MockJoin):
        MockJoin.return_value = '{0}/fake-file.css'.format(
            self.url_path)
        req = self.app.get('/content/fake-file.css',
                           status=404)
        self.code(req, 404)

    @mock.patch('os.path.join')
    def test_byte_range_specified(self, MockJoin):
        MockJoin.return_value = '{0}/fake-styles.css'.format(
            self.url_path)
        req = self.app.get('/content/fake-styles.css',
                           headers={'byte-range': 'bytes=0-'},
                           status=206)
        self.code(req, 206)
        text = req.body
        self.assertIn('body', text)
