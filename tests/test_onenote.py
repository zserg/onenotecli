import unittest
import json
import os
import onenote
from datetime import datetime
from unittest import mock

TEST_SES_FILE = 'test.ses'

class TestPage(object):
    def __init__(self, name):
        self.data = {'id' : name + '_id',
                'title' : name + '_title',
                'parentSection' : {'id' : name + '_id',
                                   'name' : name + '_name'},
                'createdTime' : datetime(2016,1,1).isoformat(),
                'lastModifiedTime' : datetime(2016,2,1).isoformat()
                }



class OneNoteTestCase(unittest.TestCase):
    def setUp(self):
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


    def tearDown(self):
        os.remove(TEST_SES_FILE)


    @mock.patch('onenote.OneNote.onenote_request')
    def test_get_pages(self, mock_onenote_request):
        """
        get_pages test
        """

        p0 = TestPage('p0')
        p1 = TestPage('p1')
        p2 = TestPage('p2')

        t_pages = [p0.data, p1.data, p2.data]
        t_status = 200

        # setup reques.post mock
        response =  (t_status, {'value': t_pages})
        mock_onenote_request.return_value = response

        #run test
        o = onenote.OneNote(ses_file = TEST_SES_FILE)
        r_status = o.get_pages()

        # check results
        mock_onenote_request.assert_called_once_with('https://www.onenote.com/api/v1.0/me/notes/pages')
        self.assertEqual(r_status,t_status)
        self.assertEqual(o.pages[0].name,'p0_title')
        self.assertEqual(o.pages[1].name,'p1_title')
        self.assertEqual(o.pages[2].name,'p2_title')
