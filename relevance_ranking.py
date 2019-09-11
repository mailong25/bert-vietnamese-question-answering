from random import randint
from scipy import sparse
from multiprocessing import Pool
from collections import Counter
import gc,string
import requests,time
import numpy
import re
from math import log
import logging
import timeout_decorator
from bs4 import BeautifulSoup,SoupStrainer
import pickle
from underthesea import pos_tag
from synonyms import generateVariants
from underthesea import pos_tag, ner, word_tokenize
from entity_linking import extractEntVariants

#w2v = KeyedVectors.load('resources/word2vec-200')

stopwords = open('resources/stopwords_small.txt').read().split('\n')
stopwords = set([w.replace(' ','_') for w in stopwords])
punct_set = set([c for c in string.punctuation]) | set(['“','”',"...","–","…","..","•",'“','”'])

def cos_sim(a, b):
    return numpy.dot(a, b) / (numpy.linalg.norm(a) * numpy.linalg.norm(b))

def document_vector(doc):
    vec = [w2v.wv[i] for i in doc]
    return numpy.sum(vec,axis = 0)

def embedding_similarity(s1,s2):
    s1 = list(set(s1.lower().split()))
    s2 = list(set(s2.lower().split()))
    
    s1 = [word for word in s1 if word in w2v.wv.vocab]
    s2 = [word for word in s2 if word in w2v.wv.vocab]
    
    if len(s1) == 0 or len(s2) == 0:
        return 0
    
    return cos_sim(document_vector(s1),document_vector(s2)) 

def generateNgram(paper, ngram = 2, deli = '_', rmSet = {}):
    words = paper.split()
    if len(words) == 1:
        return ''
    
    ngrams = []
    for i in range(0,len(words) - ngram + 1):
        block = words[i:i + ngram]
        if not any(w in rmSet for w in block):
            ngrams.append(deli.join(block))
            
    return ngrams

def generatePassages(document,n):
    passages = []
    paragraphs = document.split('\n\n')
    for para in paragraphs:
        sentences = para.rsplit(' . ')
        
        if len(sentences) <= 3:
            passages.append(' '.join(sentences))
        else:
            for i in range(0,len(sentences) - n + 1):
                passages.append(' '.join([sentences[i + j] for j in range(0,n) if '?' not in sentences[i + j]]))
        
    return passages

def passage_score(q_ngrams,passage):
    try:
        passage = passage.lower()

        p_unigram = set(generateNgram(passage,1,'_',punct_set | stopwords))
        
        uni_score = len(p_unigram & q_ngrams['unigram'])

        p_bigram  = set(generateNgram(passage,2,'_',punct_set | stopwords))
        p_trigram = set(generateNgram(passage,3,'_',punct_set | stopwords))
        p_fourgram= set(generateNgram(passage,4,'_',punct_set))

        bi_score = len(p_bigram & q_ngrams['bigram'])
        tri_score = len(p_trigram & q_ngrams['trigram'])
        four_score = len(p_fourgram & q_ngrams['fourgram'])

        #emd_sim = embedding_similarity(' '.join(p_unigram),' '.join(q_ngrams['unigram']))
        emd_sim = 0

        return uni_score + bi_score*2 + tri_score*3 + four_score*4 + emd_sim*3
    except:
        return 0

def passage_score_wrap(args):
    return passage_score(args[0],args[1])

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def get_entities(seq):
    i = 0
    chunks = []
    seq = seq + ['O']  # add sentinel
    types = [tag.split('-')[-1] for tag in seq]
    while i < len(seq):
        if seq[i].startswith('B'):
            for j in range(i+1, len(seq)):
                if seq[j].startswith('I') and types[j] == types[i]:
                    continue
                break
            chunks.append((types[i], i, j))
            i = j
        else:
            i += 1
    return chunks

def get_ner(text):
    res = ner(text)
    words = [r[0] for r in res]
    tags = [t[3] for t in res]
    
    chunks = get_entities(tags)
    res = []
    for chunk_type, chunk_start, chunk_end in chunks:
        res.append(' '.join(words[chunk_start: chunk_end]))
    return res

def keyword_extraction(question):
    keywords = []
    question = question.replace('_',' ')
    
    if 'nhất' in question.lower():
        keywords.append('nhất')

    words = pos_tag(question)
    for i in range(0,len(words)):
        words[i] = (words[i][0].replace(' ','_'),words[i][1])
        
    for token in words:
        word = token[0]
        pos = token[1]
        if (pos in ['A','Ab']):
            keywords += word.lower().split('_')
    
    keywords = list(set(keywords))
    keywords = [[w] for w in keywords]
    
    ners = get_ner(question)
    ners = [n.lower() for n in ners]
    
    for ne in ners:
        variants = extractEntVariants(ne)
        keywords.append(variants)
    
    return keywords

def isRelevant(text,keywords):
    text = text.lower().replace('_',' ')
    
    for words in keywords:
        if not any(e for e in words if e in text):
            return False

    return True

def removeDuplicate(documents):
    mapUnigram  = {}
    for doc in documents:
        mapUnigram[doc] = generateNgram(doc.lower(),1,'_',punct_set | stopwords)

    uniqueDocs = []
    for i in range(0,len(documents)):
        check = True
        for j in range(0,len(uniqueDocs)):
            check_doc  = mapUnigram[documents[i]]
            exists_doc = mapUnigram[uniqueDocs[j]]
            overlap_score = len( set(check_doc) & set(exists_doc) )
            if overlap_score >= 0.8 * len(set(check_doc)) or overlap_score >= 0.8 * len(set(exists_doc)):
                check = False
        if check:
            uniqueDocs.append(documents[i])
    
    return uniqueDocs

def rel_ranking(question,documents):
    #Return ranked list of passages from list of documents
    pool = Pool(4)
    
    q_variants = generateVariants(question)
    q_keywords = keyword_extraction(question)

    q_ngrams = {'unigram': set(generateNgram(question.lower(),1,'_',punct_set | stopwords))
                , 'bigram' : set([]), 'trigram': set([]), 'fourgram': set([])}

    for q in q_variants:
        q = q.lower()
        q_ngrams['bigram']  = q_ngrams['bigram']   | set(generateNgram(q,2,'_',punct_set | stopwords))
        q_ngrams['trigram'] = q_ngrams['trigram']  | set(generateNgram(q,3,'_',punct_set | stopwords))
        q_ngrams['fourgram']= q_ngrams['fourgram'] | set(generateNgram(q,4,'_',punct_set))
    
    documents = [d for d in documents if isRelevant(d,q_keywords)]

    passages = [generatePassages(d,3) for d in documents]
    passages = [j for i in passages for j in i]
    passages = list(set(passages))

    passages = [p for p in passages if isRelevant(p,q_keywords)]

    p_scores = pool.map(passage_score_wrap,[(q_ngrams,p) for p in passages])
    p_res = numpy.argsort([-s for s in p_scores])

    relevantDocs = []
    for i in range(0,len(passages)):
        relevantDocs.append(passages[p_res[i]])
        
    relevantDocs = removeDuplicate(relevantDocs)
    
    pool.terminate()
    del pool
        
    return relevantDocs