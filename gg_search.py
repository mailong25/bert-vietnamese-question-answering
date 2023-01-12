from googleapiclient.discovery import build
from numpy import random
import requests
from bs4 import BeautifulSoup
import timeout_decorator
from nltk import sent_tokenize
from multiprocessing import Pool
import re
import sys

api_key = ['your api key #1', 
           'your api key #2',
           'your api key #3',
           '...']

Custom_Search_Engine_ID = "your id"

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

@timeout_decorator.timeout(3)
def ggsearch(para):
    try:
        i = para[0]
        service = para[1]
        query = para[2]
        if (i == 0):
            res = service.cse().list(q=query,cx = Custom_Search_Engine_ID, gl ='vn', 
                                     googlehost = 'vn', hl = 'vi').execute()
        else:
            res = service.cse().list(q=query,cx = Custom_Search_Engine_ID,num=10,start = i*10, gl ='vn', 
                                     googlehost = 'vn', hl = 'vi').execute()
        return res[u'items']
    except:
        return []

@timeout_decorator.timeout(7)
def getContent(url):
    try:
        html = requests.get(url, timeout = 4)
        tree = BeautifulSoup(html.text,'lxml')
        for invisible_elem in tree.find_all(['script', 'style']):
            invisible_elem.extract()

        paragraphs = [p.get_text() for p in tree.find_all("p")]

        for para in tree.find_all('p'):
            para.extract()

        for href in tree.find_all(['a','strong']):
            href.unwrap()

        tree = BeautifulSoup(str(tree.html),'lxml')

        text = tree.get_text(separator='\n\n')
        text = re.sub('\n +\n','\n\n',text)

        paragraphs += text.split('\n\n')
        paragraphs = [re.sub(' +',' ',p.strip()) for p in paragraphs]
        paragraphs = [p for p in paragraphs if len(p.split()) > 10]

        for i in range(0,len(paragraphs)):
            sents = []
            text_chunks = list(chunks(paragraphs[i],100000))
            for chunk in text_chunks:
                sents += sent_tokenize(chunk)

            sents = [s for s in sents if len(s) > 2]
            sents = ' . '.join(sents)
            paragraphs[i] = sents

        return '\n\n'.join(paragraphs)
    except:
        #print('Cannot read ' + url, str(sys.exc_info()[0]))
        return ''


class GoogleSearch():
    __instance = None
    
    def __init__(self):
        
        if GoogleSearch.__instance != None:
            return GoogleSearch.__instance
        else:
            self.pool = Pool(4)
            GoogleSearch.__instance = self
            
    def search(self,question):
        service = build("customsearch", "v1",developerKey=api_key[random.randint(0,10)])
        pages_content = self.pool.map(ggsearch,[(i,service,question) for i in range(0,2)])
        pages_content = [j for i in pages_content for j in i]

        document_urls = set([])
        for page in pages_content:
            if 'fileFormat' in page:
                continue
            document_urls.add(page[u'link'])
        document_urls = list(document_urls)

        gg_documents = self.pool.map(getContent,document_urls)
        gg_documents = [d for d in gg_documents if len(d) > 20]

        return document_urls,gg_documents
