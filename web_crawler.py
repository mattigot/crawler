import sys
import os
import glob
import json
import re
import logging, coloredlogs
from web import Url
from crawler import Crawler

coloredlogs.install()
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("web_crawler")

# Name of the configuration file used (optional see config.json.example for the options).
CONFIG_FILE = "cfg.json"
# If user's url does not have a protocol, add this one by default.
DEFAULT_PROTOCL = "https://"
# List of parameters that are used for this script
params = [
    {"name": "url", "type": "str", "description": "The url to start crawling from"},
    {"name": "depth", "type": "int", "description": "The crawling depth"},
]

# The name of the directory to use for storing all the downloaded pages.
webpages_dir = os.path.join(os.getcwd(), "webpages")


def usage():
    '''
        The usage of the script
    '''
    def param_to_string(param):
        return "\t{name}: {description} (type {type})".format(name=param["name"], description=param["description"], type=param["type"])


    usage = "\n" + "=" * 7 + "\n" + "Usage:\n" + "=" * 7 +"\n"
    usage += "Description:\n"
    usage += "\tThis script, crawls the web for a given URL and given depth, and returns a TSF with the  rank results\n"
    usage += "Params:\n"
    usage += "\n".join([param_to_string(param) for param in params]) + "\n"
    usage += "Run:\n"
    usage += "\tpython web_crawler.py <url> <depth>\n"

    logger.critical(usage)


def parse_and_validate_args():
    '''
        Parse and validate the users arguments for the script
    '''
    if len(sys.argv) -1  != len(params):
        logger.error("Supplied {supplied} of args instead of {should_of_supplied}".format(supplied=str(len(sys.argv)), should_of_supplied=str(len(params))))
        usage()
        exit(-1)

    url = sys.argv[1]
    depth = sys.argv[2]

    # Make sure there is a protocol on the url
    if not url.startswith("https://") and not url.startswith("http://"):
        url = DEFAULT_PROTOCL + url

    # Make sure the first link is valid
    if Url.download(url) is None:
        logger.error("provided url is not valid - {url}".format(url=url))
        usage()
        exit(-1)

    # Make sure the depth is positive
    if int(depth) < 0:
        logger.error("provided depth ({depth}) must be positive (0 and up)".format(depth=depth))
        usage()
        exit(-1)

    return {"url": url, "depth": depth}


def setup_env():
    '''
        Check the user configuration file and setup the environment
        Currently the configuration file contains the following options:

        webpage_dir: This is the webpage directory where the script will store all html pages downloaded
    '''
    global webpages_dir

    # Open the user config file
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = json.loads(f.read())

            # Set the configuration for the directory were all the webpages will be stored
            # If user did configure a directory, and only if it exists, use it. If not use the default.
            if "webpages_dir" in cfg and os.path.isdir(cfg["webpages_dir"]):
                    webpages_dir = cfg["webpages_dir"]
            else:
                if "webpages_dir" in cfg:
                    logger.warning("Custom path for webpages_dir (%s) does not exist - using default (%s)" % (cfg["webpages_dir"], webpages_dir))

    os.makedirs(webpages_dir, exist_ok=True)

    # Clean the webpage directory of old files
    files = glob.glob(os.path.join(webpages_dir, "*"))
    for f in files:
        os.remove(f)

    logger.debug("Config:\n" + "=" * 10)
    logger.debug("WebPage Dir: " + webpages_dir)
    logger.debug("=" * 10)


def main(args):
    crawler = Crawler(url=args["url"], depth=args["depth"], webpages_dir=webpages_dir)
    crawler.crawl()
    crawler.get_results()


if __name__ == "__main__":
    setup_env()
    args = parse_and_validate_args()
    main(args)
