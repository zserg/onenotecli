# OneNote command-line access tools
----------
## Installation
## Authentication
```python
import onenote
o = onenote.OneNote(client_id="your_client_id", 
                    client_secret="your_client_secret", 
                    redirect_url="your_redirect_url",
                    scope= 'office.onenote wl.signin wl.offline_access')

o.authenticate() 
                  
```
On successfull completion authenticate() method stores all OAuth session data in file (by default .onenote.ses).

If you run OneNote constructor without any arguments then session data will be loaded from .onenote.ses

```python
import onenote
o = onenote.OneNote()

```
## Usage examples

```python
# get all notebooks
o.get_notebooks()
print(o.notebooks)

# get all sections
o.get_sections()
print(o.sections)

# get all pages
o.get_pages()
print(o.pages)

# get page content (HTML) 
o.get_pages()
n = 1 # page number in o.pages list
page = o.get_page_content(o.pages[n])

# get page content (Markdown) 
o.get_pages()
n = 1 # page number in o.pages list
page = o.get_page_content_md(o.pages[n])

```

## Command line client usage


```bash
# authentication 
$python onenotecli.py --auth --client_id=<your-client-id> --client_secret=<your-client-secret> --redirect_url=<your-redirect-url> --scope='office.onenote wl.signin wl.offline_access'

# get OneNote elemebts in tree-like view
$python onenotecli.py --tree

# print list of the all pages 
$ python onenotecli.py -p

# print list of the all pages in long format
$ python onenotecli.py -pl

# print list of the all notebooks
$ python onenotecli.py -n

# print list of the all sections
$ python onenotecli.py -s

# print content of the page 
$ python onenotecli.py -c <page_name>


```
## How to create new page

To create new page on OneNote Online you have to make an authentication with the scope "office.onenote_update"
```bash
$python onenotecli.py --auth --client_id=<your-client-id> --client_secret=<your-client-secret> --redirect_url=<your-redirect-url> --scope='office.onenote_update wl.signin wl.offline_access'

# create a page with the content from file (the content has markdown format)
$ python onenotecli.py  --create-page=<page_name> --in-section=<section_name> --from-file=<file_name>

# create a page with the content from sdtin (the content has markdown format)
$ python onenotecli.py  --create-page=<page_name> --in-section=<section_name>
Enter page content (press CTRL-D to complete):
# Hello, world!
* item1 
* item2
CTRL-D
Creating page...
Page <page_name> in section Work is created successfully (201)




```





