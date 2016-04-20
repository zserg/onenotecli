import requests
import dateutil.parser
import logging
import json
import os
import stat
import datetime
from html2text import html2text
from onenoteauth import OneNoteAuth


BASE_URL = 'https://www.onenote.com/api/v1.0/me/notes/'
SAVE_FILE_DEFAULT = '.onenote.save'

PAGE_TEMPLATE = """<!DOCTYPE html>\
<html>
  <head>
      <title>%s</title>
          <meta name="created" content="%s" />
  </head>
  <body>%s</body>
</html>
"""


class OEntity(object):

    def __init__(self, type, id, name, parent_id, parent_name,
                 created_time, lastmod_time, children,
                 parent_entity):
        self.type = type
        self.id = id
        self.name = name
        self.parent_id = parent_id
        self.parent_name = parent_name
        self.created_time = created_time
        self.lastmod_time = lastmod_time
        self.children = children
        self.parent_entity = parent_entity

    def __repr__(self):
        return self.name

    def decode(self):
        return {'type': self.type,
                'id': self.id,
                'name': self.name,
                'parent_id': self.parent_id,
                'parent_name': self.parent_name,
                'created_time': self.created_time.isoformat(),
                'lastmod_time': self.lastmod_time.isoformat(),
                'parent_entity': self.parent_entity.id if
                self.parent_entity is not None else None,
                'children': []}


class OneNote(OneNoteAuth):
    def __init__(self, save_file=SAVE_FILE_DEFAULT, *args, **kwargs):
        OneNoteAuth.__init__(self, *args, **kwargs)
        self.notebooks = []
        self.sections = []
        self.pages = []
        self.save_file = save_file

    def onenote_request(self, url, post=False, body=''):
        logging.info('onenote_request: url=%s' % url)
        token = self.get_token()
        if not token:
            logging.warn('get_token failed')
            return None

        if post:
            headers = {'Authorization': 'Bearer %s' % self.get_token(),
                       'Content-Type': 'application/xhtml+xml'}
        else:
            headers = {'Authorization': 'Bearer %s' % self.get_token()}

        logging.info('onenote_request: headers=%s' % headers)
        if post:
            r = requests.post(url, headers=headers, data=body.encode('utf-8'))
        else:
            r = requests.get(url, headers=headers)
        if r.status_code == 401:
            self.handle_401()
            headers = {'Authorization': 'Bearer %s' % self.get_token()}
            if post:
                r = requests.post(url, headers=headers,
                                  data=body.encode('utf-8'))
            else:
                r = requests.get(url, headers=headers)
        logging.info('response=%s' % r)
        try:
            data = r.json()
        except ValueError:
            data = r.text

        return r.status_code, data

    def get_url(self, url):
        logging.info("get url")
        url = BASE_URL + url
        status_code, text = self.onenote_request(url)
        return status_code, text

    def get_notebooks(self):
        logging.info("get notebooks")
        self.notebooks = []
        url = BASE_URL + 'notebooks'
        while url:
            status_code, text = self.onenote_request(url)
            logging.info("get_notebooks: response=%s" % text)
            if status_code == 200:
                for i in range(len(text['value'])):
                    entity = text['value'][i]
                    oe = OEntity(
                        type='notebook',
                        id=entity['id'],
                        name=entity['name'],
                        parent_id=None,
                        parent_name=None,
                        created_time=dateutil.parser.parse(entity['createdTime']),  # noqa
                        lastmod_time=dateutil.parser.parse(entity['lastModifiedTime']),  # noqa
                        children=[],
                        parent_entity=None
                        )
                    self.notebooks.append(oe)

            if '@odata.nextLink' in text:
                url = text['@odata.nextLink']
            else:
                url = None

        return status_code

    def get_sections(self):
        logging.info("get sections")
        self.sections = []
        url = BASE_URL + 'sections'
        while url:
            status_code, text = self.onenote_request(url)
            logging.info("get_sections: response=%s" % text)
            if status_code == 200:
                for i in range(len(text['value'])):
                    entity = text['value'][i]
                    oe = OEntity(
                        type='section',
                        id=entity['id'],
                        name=entity['name'],
                        parent_id=entity['parentNotebook']['id'],
                        parent_name=entity['parentNotebook']['name'],
                        created_time=dateutil.parser.parse(entity['createdTime']),  # noqa
                        lastmod_time=dateutil.parser.parse(entity['lastModifiedTime']),  # noqa
                        children=[],
                        parent_entity=None
                        )
                    self.sections.append(oe)

            if '@odata.nextLink' in text:
                url = text['@odata.nextLink']
            else:
                url = None

        return status_code

    def get_pages(self):
        logging.info("get pages")
        self.pages = []
        url = BASE_URL + 'pages'
        while url:
            status_code, text = self.onenote_request(url)
            logging.info("get_pages", text)
            logging.info("get_pages: response=%s" % text)
            if status_code == 200:
                for i in range(len(text['value'])):
                    entity = text['value'][i]
                    logging.info("entity %s" % entity)
                    oe = OEntity(
                        type='page',
                        id=entity['id'],
                        name=entity['title'],
                        parent_id=entity['parentSection']['id'],
                        parent_name=entity['parentSection']['name'],
                        created_time=dateutil.parser.parse(entity['createdTime']),  # noqa
                        lastmod_time=dateutil.parser.parse(entity['lastModifiedTime']),  # noqa
                        children=[],
                        parent_entity=None
                        )
                    self.pages.append(oe)

            if '@odata.nextLink' in text:
                url = text['@odata.nextLink']
            else:
                url = None

        return status_code

    def create_tree(self):
        # for each notebook create list of sections
        for n in self.notebooks:
            n.children = []
            for s in self.sections:
                if s.parent_id == n.id:
                    n.children.append(s)
                    s.parent_entity = n

        # for each section create list of pages
        for n in self.sections:
            n.children = []
            for s in self.pages:
                if s.parent_id == n.id:
                    n.children.append(s)
                    s.parent_entity = n

    def get_structure(self):
        self.get_notebooks()
        self.get_sections()
        self.get_pages()
        self.create_tree()
        self.save_structure()

    def get_item(self, items, attr, value):
        return [i for i in items if getattr(i, attr) == value]

    def get_page_content(self, page):
        '''
        Get page content in HTML
        '''
        logging.info("get page content")
        url = BASE_URL + 'pages/' + page.id + '/content'
        status_code, text = self.onenote_request(url)
        if status_code == 200:
            return text

    def get_page_content_md(self, page):
        '''
        Get page content in Markdown
        '''
        logging.info("get page content")
        url = BASE_URL + 'pages/' + page.id + '/content'
        status_code, text = self.onenote_request(url)
        if status_code == 200:
            return html2text(text)

    def save_structure(self):
        with open(self.save_file, 'w') as f:
            data = {'notebooks': [i.decode() for i in self.notebooks],
                    'sections': [i.decode() for i in self.sections],
                    'pages': [i.decode() for i in self.pages]}

            json.dump(data, f)
            os.chmod(self.ses_file, stat.S_IRUSR | stat.S_IWUSR)

    def load_structure(self):
        data = None
        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)
        except:
            logging.warning("%s file is missign or hasn't JSON format" %
                            self.save_file)
            return None

        self.notebooks = []
        self.sections = []
        self.pages = []

        for n in data['notebooks']:
            oe = OEntity(
                type='notebook',
                id=n['id'],
                name=n['name'],
                parent_id=None,
                parent_name=None,
                created_time=dateutil.parser.parse(n['created_time']),
                lastmod_time=dateutil.parser.parse(n['lastmod_time']),
                children=[],
                parent_entity=None
                )
            self.notebooks.append(oe)

        for s in data['sections']:
            oe = OEntity(
                type='section',
                id=s['id'],
                name=s['name'],
                parent_id=s['parent_id'],
                parent_name=s['parent_name'],
                created_time=dateutil.parser.parse(s['created_time']),
                lastmod_time=dateutil.parser.parse(s['lastmod_time']),
                children=[],
                parent_entity=None
                )
            self.sections.append(oe)

        for p in data['pages']:
            oe = OEntity(
                type='page',
                id=p['id'],
                name=p['name'],
                parent_id=p['parent_id'],
                parent_name=p['parent_name'],
                created_time=dateutil.parser.parse(p['created_time']),
                lastmod_time=dateutil.parser.parse(p['lastmod_time']),
                children=[],
                parent_entity=None
                )
            self.pages.append(oe)

        self.create_tree()
        return True

    def create_page(self, title, section, text):
        logging.info("create_page")
        # get section id
        sec = self.get_item(self.sections, 'name', section)
        if not sec:
            logging.info("create_page: section %s isn't found" % section)
            return None

        url = BASE_URL + 'sections/' + sec[0].id + '/pages'

        body = PAGE_TEMPLATE % (title,
                                datetime.datetime.now().isoformat(),
                                text)

        status_code, text = self.onenote_request(url, post=True, body=body)

        return status_code
