from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_child_urls(url):
    urls = set()
    domain_name = urlparse(url).netloc
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    webpage = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href): continue
        if domain_name not in href: continue
        urls.add(href)
    return urls

def get_url_data(url):
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    webpage = urllib.request.urlopen(req).read()
    df = pd.read_html(webpage)[0]
    # pd.set_option('display.width', 1000)
    # print(df)
    return df