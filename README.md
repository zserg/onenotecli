# OneNote command line access tools
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
page = o.get_

```

## Command line client usage


```bash
# get all pages 
$ python onenotecli.py -p

```


