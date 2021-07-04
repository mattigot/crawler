import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse
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

