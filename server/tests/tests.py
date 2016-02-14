import unittest
import webtest
from google.appengine.ext import testbed
from webapp2_extras import json
from server.main import app

USER_PATH = '/users'
USER = {'username': 'jideobs', 'password': 'mychora', 'confirm_password': 'mychora'}


class TestCasesBase(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def executeReq(self, path, method='post', data=None, cont_type='json', expected_status=200):
        if cont_type == 'form':
            content_type = 'application/x-www-form-urlencoded'
        else:
            content_type = 'application/json;charset=utf-8'

        json_data = json.encode(data) if 'json' in content_type else data
        if method == 'post':
            return self.testapp.post(path, params=json_data, content_type=content_type, status=expected_status)
        elif method == 'put':
            return self.testapp.put(path, params=json_data, content_type=content_type, status=expected_status)
        elif method == 'delete':
            return self.testapp.delete(path, status=expected_status)
        elif method == 'head':
            return self.testapp.head(path, status=expected_status)
        elif method == 'get':
            return self.testapp.get(path, status=expected_status)


class RegisterLoginTestCases(TestCasesBase):
    def testUserRegister(self):
        res = self.executeReq('/register', data=USER, cont_type='form', expected_status=302)
        self.assertEqual(res.status_int, 302)

    def testAlreadyRegisteredUser(self):
        self.executeReq('/register', data=USER, cont_type='form', expected_status=302)
        res = self.executeReq('/register', data=USER, cont_type='form')
        self.assertEqual(res.status_int, 200)

    def testUserLogin(self):
        self.executeReq('/register', data=USER, cont_type='form', expected_status=302)
        user_data = {'username': USER['username'], 'password': USER['password']}
        res = self.executeReq('/login', data=user_data, cont_type='form', expected_status=302)
        self.assertEqual(res.status_int, 302)

    def testInvalidUserLogin(self):
        user_data = {'username': 'invalid_username', 'password': 'newlife'}
        res = self.executeReq('/login', data=user_data, cont_type='form')
        self.assertEqual(res.status_int, 200)

    def testInvalidPasswordLogin(self):
        self.executeReq('/register', data=USER, cont_type='form', expected_status=302)
        user_data = {'username': USER['username'], 'password': 'invalid_pass'}
        res = self.executeReq('/login', data=user_data, cont_type='form')
        self.assertEqual(res.status_int, 200)

    def testLogout(self):
        self.executeReq('/register', data=USER, cont_type='form', expected_status=302)
        login_data = {'username': USER['username'], 'password': USER['password']}
        self.executeReq('/login', data=login_data, cont_type='form', expected_status=302)
        self.executeReq('/logout', method='get', expected_status=302)
