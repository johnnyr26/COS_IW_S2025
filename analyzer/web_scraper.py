import sys
import requests
from bs4 import BeautifulSoup

class WebsiteNotFoundException(Exception):
    def __init__(self, message: str):
        """
        Exception raised for a website that does not have
        the expected content.

        :params message: the error message.
        """
        self.message = message
        super().__init__(self.message)


class Web_Scraper:
    def scrape_wikipedia_article(self, url: str) -> dict[str, str]:
        """
        Scrapes a wikipedia article and returns the first paragraph
        of the article.

        :params url: the url of the Wikipedia article.
        :returns: a dictionary with the url and the first paragraph
        """
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            if len(paragraphs) < 2 or paragraphs[0] == "The requested page title is empty or contains only a namespace prefix.\n":
                raise WebsiteNotFoundException(f"Wikipedia article url {url} is not found.")
            # the first element of a valid article is always \n.
            return {"url": url, "content": paragraphs[1]}
        except WebsiteNotFoundException as ex:
            raise ex

if __name__ == "__main__":
    id = sys.argv[1]
    web_scraper = Web_Scraper()
    response = web_scraper.scrape_wikipedia_article(f"https://en.wikipedia.org/?curid={id}")
    print(response)
