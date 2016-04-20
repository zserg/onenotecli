import onenote
import argparse
import sys
import html2text
import logging
import markdown2


def main(args):

    """
    Setup logging
    """
    if args.loglevel:
        loglevel = args.loglevel
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
                raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(level=numeric_level)

    """
    Create OneNote instance and provide authorization
    """
    if args.authorize:
        if not args.client_id:
            print('--client_id option is needed for authorization')
            exit(1)
        if not args.client_secret:
            print('--client_secret option is needed for authorization')
            exit(1)
        if not args.redirect_url:
            print('--redirect_url option is needed for authorization')
            exit(1)
        if not args.scope:
            print('--scope option is needed for authorization')
            exit(1)

        onote = onenote.OneNote(client_id=args.client_id,
                                client_secret=args.client_secret,
                                redirect_url=args.redirect_url,
                                scope=args.scope)
        onote.authenticate()

    else:
        onote = onenote.OneNote()

    """
    Get some flags from args
    """
    if args.update:
        loaded = False
    else:
        loaded = onote.load_structure()

    if args.by_time:
        to_sort = 'lastmod_time'
    else:
        to_sort = 'name'

    longformat = args.long
    is_html = args.html

    """
    Print list of pages
    """
    if args.pages:
        if not loaded:
            onote.get_structure()

        for i in sorted(onote.pages, key=lambda x: getattr(x, to_sort)):
            if longformat:
                print('%s %s \t[%s] (%s -> %s)' %
                      (i.lastmod_time.strftime('%Y %b %0d %H:%M'), i.id,
                       i.name, i.parent_entity.parent_name, i.parent_name))
            else:
                print(i.name)

    """
    Print list of sections
    """
    if args.sections:
        if not loaded:
            onote.get_structure()

        for i in sorted(onote.sections, key=lambda x: getattr(x, to_sort)):
            if longformat:
                print('%s %s \t[%s] (%s)' %
                      (i.lastmod_time.strftime('%Y %b %0d %H:%M'), i.id,
                       i.name, i.parent_name))
            else:
                print(i.name)

    """
    Print list of notebooks
    """
    if args.notebooks:
        if not loaded:
            onote.get_structure()

        for i in sorted(onote.notebooks, key=lambda x: getattr(x, to_sort)):
            if longformat:
                print('%s %s \t[%s]' %
                      (i.lastmod_time.strftime('%Y %b %0d %H:%M'),
                       i.id, i.name))
            else:
                print(i.name)

    """
    Print content of the page selected by name.
    Default output format is markdown.
    --html - output in html format
    """
    if args.content:
        if not loaded:
            onote.get_structure()
        page = onote.get_item(onote.pages, 'name', args.content)
        if page:
            if is_html:
                print(onote.get_page_content(page[0]))
            else:
                print(html2text.html2text(onote.get_page_content(page[0])))
        else:
            print("Error: page '%s' isn't found" % args.content)

    """
    Print the OneNote  structure in tree-like format
    """
    if args.tree:
        if not loaded:
            onote.get_structure()

        i_n = 0
        for n in onote.notebooks:
            i_n += 1
            if i_n == len(onote.notebooks):
                last_n = True
                isymb = chr(0x2514)
            else:
                last_n = False
                isymb = chr(0x251C)

            prefix = '%s ' % (isymb+2*chr(0x2500))
            line = prefix + n.name
            print(line)

            i_s = 0
            for s in n.children:
                i_s += 1
                if i_s == len(n.children):
                    last_s = True
                    isymb = chr(0x2514)
                else:
                    last_s = False
                    isymb = chr(0x251C)

                if last_n:
                    preprefix = 4*' '
                else:
                    preprefix = chr(0x2502) + 3*' '

                prefix = '%s ' % (preprefix + isymb+2*chr(0x2500))
                line = prefix + s.name
                print(line)

                i_p = 0
                for p in s.children:
                    i_p += 1
                    if i_p == len(s.children):
                        isymb = chr(0x2514)
                    else:
                        isymb = chr(0x251C)

                    if last_n and last_s:
                        preprefix = 8*' '
                    elif last_n and not last_s:
                        preprefix = 2*' ' + chr(0x2502) + 3*' '
                    elif not last_n and last_s:
                        preprefix = chr(0x2502) + 7*' '
                    else:
                        preprefix = chr(0x2502) + 3*' '+chr(0x2502) + 4*' '

                    prefix = '%s ' % (preprefix + isymb+2*chr(0x2500))
                    line = prefix + p.name
                    print(line)

    """
    Post page
    """
    if args.create:
        if not args.in_section:
            print('You should give a section name to create page in (--in-section=<sec_name>)')  # noqa
        else:
            if args.file:
                with open(args.file[0][0], 'r') as f:
                    data = f.read()
            else:
                data = sys.stdin.read()
            status = onote.create_page(args.create, args.in_section,
                                       markdown2.markdown(data))
            if status == 403:
                print('Error 403: You are not permitted to perform the reqiested operation')  # noqa
            elif status == 401:
                print('Error 401: Authorization failed')
            else:
                print('Page %s in section %s is created successfully (%d)' %
                      (args.create, args.in_section, status))

    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pages', action='store_true',
                        default=False, help='print the list of pages')

    parser.add_argument('-n', '--notebooks', action='store_true',
                        default=False, help='print the list of notebooks')

    parser.add_argument('-s', '--sections', action='store_true',
                        default=False, help='print the list of sections')

    parser.add_argument('-l', dest='long', action='store_true',
                        default=False, help='use a long listing format')

    parser.add_argument('-t', dest='by_time', action='store_true',
                        default=False,
                        help='sort by modification time, last first')

    parser.add_argument('-c', '--page-content', dest='content', action='store',
                        help='print content of the page')

    parser.add_argument('--html', dest='html', action='store_true',
                        help='print content of the page in HTML format')

    parser.add_argument('--tree', dest='tree', action='store_true',
                        help='print OneNote structure in tree-like format')

    parser.add_argument('-u', '--update', dest='update', action='store_true',
                        help='update OneNote structure from server')

    parser.add_argument('--log', dest='loglevel', action='store',
                        help='set loglevel (INFO, DEBUG etc')

    parser.add_argument('--create-page', dest='create', action='store',
                        help='create page in secion (--in-section=<sec_name>)')

    parser.add_argument('--in-section', dest='in_section', action='store',
                        help='section to create page in')

    parser.add_argument('--auth', dest='authorize', action='store_true',
                        help='run authorization in OneNote Online')

    parser.add_argument('--client_id', dest='client_id', action='store',
                        help='client_id for authorization')

    parser.add_argument('--client_secret', dest='client_secret',
                        action='store',
                        help='client_secret for authorization')

    parser.add_argument('--redirect_url', dest='redirect_url', action='store',
                        help='redirect_url for authorization')

    parser.add_argument('--scope', dest='scope', action='store',
                        help='scope for authorization')

    parser.add_argument(dest='file', action='append', nargs='*',
                        help='file to create page')

    args = parser.parse_args()
    main(args)
