import regex as re
from bs4 import BeautifulSoup

class HTMLextractor:
    def __init__(self) -> None:
        pass
    
    def clean_string(self, string):
        string = re.sub('( {2,})', '', string) # remove excess white spaces
        string = re.sub('(\n{2,})', '\n', string) # remove excess new lines
        string = re.sub('(^[\n ]*)|([\n ]*$)', '', string)
        return string


    def extract(self, html_text) -> (str, dict):
        ## Extracting text
        soup = BeautifulSoup(html_text, 'html.parser')
        article = soup.find_all("div", class_= "article-content col-12")[0]
        for s in article.find_all('div', class_="vote recipe-page-vote"): # remove the score
            s.extract()

        text = self.clean_string(article.text)

        ## Extracting meta data
        soup = BeautifulSoup(html_text, 'html.parser')
        article = soup.find_all("div", class_= "article-content col-12")[0]

        metadata_dict = {}
        metadata_dict['website'] = 'AniaGotuje'
        metadata_dict['name'] = self.clean_string(article.find('h1', {"itemprop": "name"}).text)
        metadata_dict['category'] = [self.clean_string(tag) for tag in soup.find_all('div', class_="post-categories")[0].text.split('·')]
        metadata_dict['tags'] = [self.clean_string(tag) for tag in soup.find_all('div', class_="post-tags")[0].text.split('·')]

        voting = article.find_all('div', class_="vote recipe-page-vote")
        if len(voting) == 0:
            metadata_dict['score'] = ''
            metadata_dict['max_score'] = ''
            metadata_dict['votes'] = ''
            pass
        else:
            voting = voting[0]
            metadata_dict['score'] = self.clean_string(voting.find_all('span', class_="vote-value")[0].find_all('span')[0].text)
            metadata_dict['max_score'] =self.clean_string(voting.find_all('span', class_="vote-value")[0].find_all('span')[1].text)
            metadata_dict['votes'] =self.clean_string(voting.find_all('span', class_="vote-value")[0].find_all('span')[2].text)

        return (text, metadata_dict)