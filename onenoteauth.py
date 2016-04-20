import webbrowser
import socket
import json
import re
import requests
import logging
import os
import stat

CODE_URL = 'https://login.live.com/oauth20_authorize.srf?\
response_type=code&client_id=%s&redirect_url=%s&scope=%s'

HOST = ''
PORT = 8085

RESP_200 = """\
HTTP/1.1 200 OK
Content-type: text/html

<script type="text/javascript">window.close()</script>
"""


class OneNoteAuth(object):
    SESSION_FILE = '.onenote.ses'
    SES_KEYS = ['client_id',
                'client_secret',
                'access_token',
                'refresh_token',
                'scope',
                'redirect_url']

    def __init__(self, ses_file=SESSION_FILE, client_id=None,
                 client_secret=None, scope=None, redirect_url=None):
        logging.info('OneNoteAuth __init__: client_id=%s,\
                     client_secret=%s, scope=%s,\
                     redirect_url=%s' % (client_id, client_secret,
                                         scope, redirect_url))
        self.ses_file = ses_file
        self.auth_cfg = {
                'client_id': None,
                'client_secret': None,
                'scope': None,
                'access_token': None,
                'refresh_token': None,
                'redirect_url': None}

        if client_id and client_secret and scope and redirect_url:
            self.auth_cfg['client_id'] = client_id
            self.auth_cfg['client_secret'] = client_secret
            self.auth_cfg['scope'] = scope
            self.auth_cfg['redirect_url'] = redirect_url
            self.auth_cfg['access_token'] = None
            self.auth_cfg['refresh_token'] = None
        else:
            data = self.load_session()
            if data:
                self.auth_cfg['client_id'] = data['client_id']
                self.auth_cfg['client_secret'] = data['client_secret']
                self.auth_cfg['scope'] = data['scope']
                self.auth_cfg['access_token'] = data['access_token']
                self.auth_cfg['refresh_token'] = data['refresh_token']
                self.auth_cfg['redirect_url'] = data['redirect_url']

    def load_session(self):
        logging.info('load_session')
        data = None
        try:
            with open(self.ses_file, 'r') as f:
                data = json.load(f)
        except:
            logging.warning("%s file is missign or hasn't JSON format" %
                            self.SESSION_FILE)
            return None

        if self.check_ses_data(data):
            return data

    def save_session(self):
        with open(self.ses_file, 'w') as f:
            json.dump(self.auth_cfg, f)
            os.chmod(self.ses_file, stat.S_IRUSR | stat.S_IWUSR)

    def check_ses_data(self, data):
        for k in self.SES_KEYS:
            if k not in data:
                return False

        return True

    def get_token(self):
        logging.info('get_token entry')
        if self.auth_cfg['access_token']:
            logging.info('get_token entry: cp0')
            return self.auth_cfg['access_token']

        if self.auth_cfg['refresh_token']:
            logging.info('get_token entry: cp1')
            return self.get_refresh_token()

        else:
            logging.info('get_token entry: authenticate')
            return self.authenticate()

    def authenticate(self):
        logging.info('authenticate')
        # get authorization code
        code = self.auth_get_code()
        if not code:
            return None

        # get access_token
        logging.info('get access_token')
        url = 'https://login.live.com/oauth20_token.srf'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.auth_cfg['client_id'],
            'client_secret': self.auth_cfg['client_secret'],
            'code': code,
            'redirect_url': self.auth_cfg['redirect_url']
            }
        r = requests.post(url, headers=headers, data=payload)
        response = r.json()
        logging.info('get_token: status_code=%d, response=%s' %
                     (r.status_code, response))
        if r.status_code != 200:
            return None
        if 'refresh_token' in response:
            self.auth_cfg['refresh_token'] = response['refresh_token']
        if 'access_token' in response:
            self.auth_cfg['access_token'] = response['access_token']
            self.save_session()
            return self.auth_cfg['access_token']

    def auth_get_code(self):
        logging.info('auth_get_code entry')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(1)

        webbrowser.open(CODE_URL % (self.auth_cfg['client_id'],
                                    self.auth_cfg['redirect_url'],
                                    self.auth_cfg['scope']))

        logging.info('Serving HTTP on port %s...' % PORT)
        conn, addr = s.accept()
        request = conn.recv(1024)
        http_response = RESP_200

        conn.sendall(bytes(http_response, encoding='utf-8'))
        conn.close()
        s.shutdown(socket.SHUT_RDWR)
        s.close()

        request_line, _ = request.decode().split('\r\n', 1)
        resp = re.search(r'GET /\?code=([^\s]+) ', request_line)
        logging.info('auth_get_code: resp=%s' % resp)
        if resp:
            logging.info('auth_get_code: code=%s' % resp.group(1))
            return resp.group(1)
        else:
            return None

    def handle_401(self):
        self.auth_cfg['access_token'] = None
        self.get_token()

    def get_refresh_token(self):
        # get access_token
        self.auth_cfg['access_token'] = None
        url = 'https://login.live.com/oauth20_token.srf'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'grant_type': 'refresh_token',
            'client_id': self.auth_cfg['client_id'],
            'client_secret': self.auth_cfg['client_secret'],
            'redirect_url': self.auth_cfg['redirect_url'],
            'refresh_token': self.auth_cfg['refresh_token']
            }
        r = requests.post(url, headers=headers, data=payload)
        response = r.json()
        if 'refresh_token' in response:
            self.auth_cfg['refresh_token'] = response['refresh_token']
        else:
            self.auth_cfg['refresh_token'] = None

        if 'access_token' in response:
            self.auth_cfg['access_token'] = response['access_token']
        else:
            self.auth_cfg['access_token'] = None

        return self.auth_cfg['access_token']
