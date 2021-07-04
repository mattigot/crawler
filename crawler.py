import logging
import os
from web import WebPage

logger = logging.getLogger("web_crawler")

class Crawler:
    '''
        Crawler class

        This class implements a web crawler, that starts to crawl from a given url until the
        requested depth is reached.
    '''
    def  __init__(self, url, depth, webpages_dir, results_file="crawl_res.csv"):
        '''
            url: The url to start the crawling from
            depth: The depth to crawl
            webpages_dir: The directory where to cache all the downloaded webpages
            results_file: The name of the results file

            ranks: The results of the crawling (each item in the list a tuple of (url, depth, ration)
            ranked_urls: List of the urls we already ranked - so we won't try to download it again.
            urls_to_crawl: Dictionary of lists. each key represents a depth to crawl, and has a list
                           of the pages he need to crawl (This is implemented like this and not  in one
                           list, since when iterating on a list it is a problem to modify it. This way
                           for every depth, we modify one list(next depth), and iterate of another (current depth)
        '''
        self.url = url
        self.depth = depth
        self.webpages_dir = webpages_dir
        self.results_file = results_file

        self.ranks = [("url", "depth", "ratio")]
        self.ranked_urls = []
        self.urls_to_crawl = {"1" : [self.url]}


    def crawl_page(self, page_url, depth, url_idx):
        '''
            Crawl a page:
                - Download the url
                - Parse it
                - Filter unwanted links
                - Rank page.
        '''
        page = WebPage(page_url, self.webpages_dir)
        downloaded = page.download()
        if not downloaded:
            logger.error("CRAWLER: failed to download this url - %s" % page.get_url())

            return None

        page.parse()
        page.filter_links()

        rank = page.get_rank(calculate_rank=True)
        url = page.get_url()

        links = page.get_links()
        filtered_links = page.get_filtered_links()

        links_leave = []
        links_remove = []

        # Do not add any link to the list - filter some
        for link in links:
            # Already ranked this one or this is already in the list for future crawling - remove it. 
            if link in self.ranked_urls or link in self.urls_to_crawl:
                links_remove.append(link)
            else:
                links_leave.append(link)

        logger.info("CRAWLER: #%d: %s [rank = %f, links: new = %d duplicate = %d filtered = %d]" % (url_idx, page_url, rank, len(links_leave), len(links_remove), len(filtered_links)))

        # We ranked this url - add it for the final results.
        self.ranked_urls.append(url)
        self.ranks.append((url, rank, depth, links))

        # Add the new urls we found in this page to the future crawl list.
        self.urls_to_crawl[chr(ord(depth) + 1)].extend(links_leave)

        return rank, url, links


    def crawl(self):
        '''
            Crawl this page

            Go through all the links up to the configured depth, and store the results and rank them.
        '''
        #Go over all urls to crawl by depth
        for i in range(1, int(self.depth) + 1):
            depth_idx = str(i)

            # Get the current depth list
            depth_url_list = self.urls_to_crawl[depth_idx]

            logger.info("\n######################\n## Crawling Depth %d [%d links]\n######################" % (i, len(depth_url_list)))
            # There are no urls to crawl for this depth, so there is not point in continuing
            if len(depth_url_list) == 0:
                break

            # Prepare a new list for the next depth, to be filled out by the pages of the current depth
            self.urls_to_crawl[chr(ord(depth_idx) + 1)] = []

            # Crawl current depth urls
            url_idx = 0
            for url in depth_url_list:
                self.crawl_page(url, depth_idx, url_idx)
                url_idx += 1

    def get_results(self):
        '''
            Create the crawling results file
            File will be created in the webpage_dir under the name the user requested.
        '''

        res_file = os.path.join(self.webpages_dir, self.results_file)

        logger.info("\n######################\n## Crawling Results:\n######################")
        logger.info("See the results in the csv file: %s", res_file)

        with open(res_file, 'w') as f:
            for rank in self.ranks:
                print("%s, %s, %s" %(rank[0], rank[1], rank[2]))
                f.write("{url}\t{rank}\t{depth}\n".format(url=rank[0], depth=rank[1], rank=rank[2]))


