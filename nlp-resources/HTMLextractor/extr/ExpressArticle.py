from newspaper import Article
from urllib.parse import urlparse
import regex as re

class HTMLextractor:
    def __init__(self) -> None:
        pass
    
    def clean_string(self, string):
        string = re.sub('( {2,})', '', string) # remove excess white spaces
        string = re.sub('(\n{2,})', '\n', string) # remove excess new lines
        string = re.sub('(^[\n ]*)|([\n ]*$)', '', string)
        return string
    
    def extract(self, html_text) -> (str, dict):
        article = Article(url = '')
        article.set_html(html_text)
        ## Extracting text
        article.parse()

        text = self.clean_string(article.title + '\n' + article.meta_description + '\n' + article.text)

        ## Extracting meta data

        metadata_dict = {}
        metadata_dict['website'] = urlparse(article.canonical_link).netloc
        metadata_dict['name'] = article.title
        metadata_dict['keywords'] = article.keywords
        metadata_dict['meta_keywords'] = article.meta_keywords
        metadata_dict['tags'] = article.tags
        metadata_dict['authors'] = article.authors
        metadata_dict['publish_date'] = article.publish_date
        metadata_dict['summary'] = article.summary
       
        return (text, metadata_dict)