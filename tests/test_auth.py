import logging
import unittest
import json
import os
from unittest import mock

import onenote

#logging.basicConfig(level=logging.INFO)

TEST_SES_FILE = 'test.ses'
TEST_SAVE_FILE = 'test.save'

auth_url = 'https://login.live.com/oauth20_token.srf'


class OneNoteAuthTestCase(unittest.TestCase):
    # def setUp(self):
    #     with open(TEST_SES_FILE,'w') as f:
    #         json.dump({'1':'2'},f)

    def tearDown(self):
        os.remove(TEST_SES_FILE)


    @mock.patch('requests.post')
    @mock.patch('onenote.OneNote.auth_get_code')
    def test_create_instance_with_auth(self, mock_get_code, mock_post):
        """
        Authentication test
        """
        t_access_token = '123'
        t_refresh_token = '456'
        t_code = 'CODE'

        t_client_id = 't_id'
        t_client_secret = 't_secret'
        t_scope = 't_scope'
        t_redirect_url = 't_redir'


        # setup reques.post mock
        mock_post_responce = mock.Mock()
        post_resp_data =  {'access_token' : t_access_token,
                           'refresh_token' : t_refresh_token}
        mock_post_responce.json.return_value = post_resp_data
        mock_post_responce.status_code = 200
        mock_post.return_value = mock_post_responce

        #setup auth_get_code mock
        mock_get_code.return_value = t_code

        #run test
        o = onenote.OneNote(client_id = t_client_id,
                            client_secret = t_client_secret,
                            scope = t_scope,
                            redirect_url = t_redirect_url,
                            ses_file = TEST_SES_FILE,
                            save_file = TEST_SES_FILE
                            )
        result = o.authenticate()

        mock_get_code.assert_called_with()
        mock_post.assert_called_with(auth_url,  headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={'redirect_url': t_redirect_url,
                'client_id': t_client_id, 'client_secret': t_client_secret,
                'grant_type': 'authorization_code',
                'code': t_code})

        self.assertEqual(result,t_access_token)

        with open(TEST_SES_FILE,'r') as f:
            ses_data = json.load(f)

        self.assertEqual(ses_data['client_id'], t_client_id)
        self.assertEqual(ses_data['client_secret'], t_client_secret)
        self.assertEqual(ses_data['redirect_url'], t_redirect_url)
        self.assertEqual(ses_data['scope'], t_scope)
        self.assertEqual(ses_data['access_token'], t_access_token)
        self.assertEqual(ses_data['refresh_token'], t_refresh_token)


    @mock.patch('requests.post')
    @mock.patch('onenote.OneNote.auth_get_code')
    def test_create_instance_wo_auth(self, mock_get_code, mock_post):
        """
        Load saved session test
        """
        t_access_token = '123'
        t_refresh_token = '456'
        t_code = 'CODE'

        t_client_id = 't_id'
        t_client_secret = 't_secret'
        t_scope = 't_scope'
        t_redirect_url = 't_redir'

        #prepare session file
        ses_data = {'client_id' : t_client_id,
                    'client_secret' : t_client_secret,
                    'redirect_url' : t_redirect_url,
                    'scope' : t_scope,
                    'access_token' : t_access_token,
                    'refresh_token' : t_refresh_token}
        with open(TEST_SES_FILE,'w') as f:
           json.dump(ses_data,f)

        # setup reques.post mock
        mock_post_responce = mock.Mock()
        mock_post_responce.json.return_value = {}
        mock_post_responce.status_code = 401
        mock_post.return_value = mock_post_responce

        #setup auth_get_code mock
        mock_get_code.return_value = t_code

        #run test
        o = onenote.OneNote(ses_file = TEST_SES_FILE)
        result = o.get_token()

        # check results
        self.assertEqual(mock_get_code.called, False)
        self.assertEqual(mock_post.called, False)
        self.assertEqual(result,t_access_token)

        with open(TEST_SES_FILE,'r') as f:
            ses_data = json.load(f)

        self.assertEqual(ses_data['client_id'], t_client_id)
        self.assertEqual(ses_data['client_secret'], t_client_secret)
        self.assertEqual(ses_data['redirect_url'], t_redirect_url)
        self.assertEqual(ses_data['scope'], t_scope)
        self.assertEqual(ses_data['access_token'], t_access_token)
        self.assertEqual(ses_data['refresh_token'], t_refresh_token)







