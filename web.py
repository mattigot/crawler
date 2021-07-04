import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import urljoin
import logging

logger = logging.getLogger("web_crawler")
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Url:
    '''
        Url class - provides basic functionality on the urls
    '''

    WWW_PREFIX='www.'

    @staticmethod
    def get_hostname(url, strip_www=True):
        '''
            Returns the hostname from the url.
            for example: https://www.test.com will return 'test'.
        '''
        parsed_url = urlparse(url)

        hostname = '{parsed.netloc}'.format(parsed=parsed_url)

        # If the url start with WWW and the user wants to Ignore it - strip it.
        if strip_www and hostname.startswith(Url.WWW_PREFIX):
            hostname = hostname[len(Url.WWW_PREFIX):]

        return hostname

    @staticmethod
    def download(url):
        '''
            Downlod a given url

            If the download succeeds return the html page, else return None
        '''
        html = None
        try:
            html = requests.get(url, timeout=5, verify=False)
        except requests.exceptions.HTTPError as errh:
            logger.error("URL: Http Error: %s" % errh)
        except requests.exceptions.ConnectionError as errc:
            logger.error("URL: Error Connecting: %s" % errc)
        except requests.exceptions.Timeout as errt:
            logger.error("URL: Timeout Error: %s" % errt)
        except requests.exceptions.RequestException as err:
            logger.error("URL: OOps Something else %s", err)

        return html

class WebPage:
    '''
        WebPage Class

        This class represents a web page, and provides all of the logic needed for crawling this
        page.
    '''
    DEFAULT_RANK = -1

    def __init__(self, url, webpages_dir):
        '''
            url: The url of the page
            webpages_dir: the directory were to cache the page

            hostname: The hostname of this url (used for ranking)
            links: The list of the static links in this url's web page.
            downloaded: Was this url downloaded and cached.
            filtered_links: Links that are not going to be currently processed (save them for the future)
            page_rank: The rank of the page calculated by the rank function or the initial default value
        '''
        self.url = url
        self.webpages_dir = webpages_dir

        self.hostname = Url.get_hostname(self.url)
        self.downloaded = False
        self.links = []
        self.filtered_links = []
        self.page_rank = self.DEFAULT_RANK

        # Build the name of the html file that will be stored on the disk.
        # The name is not the url (too long, and has weird chars) - but rather the objects
        # unique ID.
        self.html_file_name = os.path.join(self.webpages_dir, "".join((str(id(self)), ".html")))


    def download(self):
        '''
            Download the web page's url and store the content on the Disk
        '''
        logger.debug("WEBPAGE: Attempting to download url: %s" % (self.url))

        # Download
        html = Url.download(self.url)

        # Download failed
        if html is None:
            logger.warning("WEBPAGE: Could not download url %s" % self.url)
            self.download = False

            return False

        # Download was a success
        self.downloaded = True

        # Store the html on the Disk for future use.
        with open(self.html_file_name, 'w') as f:
            f.write(html.text)

        return True


    def parse(self):
        '''
            Prase this url if we already downloaded it.

            Currently we only get the static links inside the web page and save them.
        '''
        html = None

        if not self.downloaded:
            logger.warning("WEBPAGE: skipping page parse for %s - need to download it first" % self.url)
            return

        with open(self.html_file_name, 'r') as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")

        self.links = [urljoin(self.url, a.get('href')) for a in soup.find_all('a', href=True)]


    def __should_filter_link(self, link):
        '''
            Check if this link should be filtered and not processed

            Currently we only filter dynamic javascript links.
        '''
        filter_strs = ["javascript:"]

        for filter_str in filter_strs:
            if link.startswith(filter_str):
                return True

        return False

    def filter_links(self):
        '''
            Filter links that should not be processed.
            Save them for future use.
        '''
        tmp = []
        tmp_len = len(self.links)

        # Iterate of the link found in the webpage
        for link in self.links:
            # This link should be filtered
            if self.__should_filter_link(link):
                self.filtered_links.append(link)
            else:
                tmp.append(link)

        # Update links with the updated list
        self.links = tmp

        assert tmp_len == len(self.links) + len(self.filtered_links)


    def rank(self):
        '''
            Calculate the web pages rank (the ratio of the static links that share the same hostname
            as the page.
        '''
        same_hostname = [link for link in self.links if self.is_same_hostname(link)]

        self.page_rank = 0 if len(self.links) == 0 else  len(same_hostname)/len(self.links)


    ''' Checker functions '''
    def is_same_url(self, url):
        '''
            Is this url the same as this web page's url
        '''
        return self.url == url


    def isdownloaded(self):
        '''
            Was this page already downloaded
        '''
        return self.html is not None


    def is_same_hostname(self, hostname, parse_hostname=True):
        '''
            Is this hostname the same as the web page's hostname
        '''
        hostname = Url.get_hostname(hostname) if parse_hostname else hostname

        return self.hostname == hostname


    '''' Getter functions '''
    def get_url(self):
        '''
            Get the web page's url
        '''
        return self.url


    def get_filtered_links(self):
        '''
            Get the web page's filtered link list
        '''
        return self.filtered_links


    def get_rank(self, calculate_rank=False):
        '''
            Get this pages rank

            Add an option to calculate the rank, if not already calculate
        '''
        if calculate_rank or self.rank == self.DEFAULT_RANK:
            self.rank()

        return self.page_rank


    def get_links(self):
        '''
            Get the web page's static links
        '''

        return self.links

