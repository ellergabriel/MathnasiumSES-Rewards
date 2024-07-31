from urllib.request import urlopen
import re

url="https://radius.mathnasium.com"
page = urlopen(url)
html_bytes = page.read()
html = html_bytes.decode("utf-8")
print(html)
