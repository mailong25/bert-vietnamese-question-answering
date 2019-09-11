from underthesea import pos_tag
import string
import functools

stopwords = open('resources/stopwords_small.txt').read().split('\n')
stopwords = set([w.replace(' ','_') for w in stopwords])
punct_set = set([c for c in string.punctuation]) | set(['“','”',"...","–","…","..","•",'“','”'])

with open('resources/bigram.txt') as f:
    data = f.read().split('\n')

data = data[:-1]
markov_score = {}
for line in data:
    word, score = line.split('\t')
    markov_score[word] = int(score)
    
del data
    
def makovCal(a, b):
    
    termBigram = a + "_" + b
        
    if termBigram in markov_score:
        freBigram = markov_score[termBigram]
    else:
        freBigram = 1
        
    if a in markov_score:
        freUnigram = markov_score[a]
    else:
        freUnigram = 1
        
    if freUnigram < 5:
        freUnigram = 2000
    else:
        freUnigram += 2000
        
    return float(freBigram) / freUnigram

import json,itertools

map_pos = {'M':'noun', 'Y':'noun','Nb':'noun','Nc':'noun','Ni':'noun','Np':'noun','N':'noun','X':'adj',
           'Nu':'noun','Ny':'noun','V':'verb', 'Vb':'verb','Vy':'verb','A': 'adj','Ab': 'adj','R':'adj'}

map_synonym = json.load(open('resources/synonym.json'))

def generateCombinations(tokens,thresh_hold):
    combinations = []
    for i in range(0,len(tokens)):
        word = tokens[i][0].lower()
        
        if word in stopwords:
            combinations.append([word])
            continue
        
        pos  = tokens[i][1]
        if pos in map_pos:
            pos  = map_pos[pos]
            if word in map_synonym[pos]:
                synonyms = map_synonym[pos][word]
                
                possible_synonym = []
                
                for syn in synonyms:
                    if i == 0:
                        pre_word = 'NONE'
                    else:
                        pre_word = tokens[i-1][0].lower()

                    if i == len(tokens) - 1:
                        next_word = 'NONE'
                    else:
                        next_word = tokens[i+1][0].lower()

                    if makovCal(pre_word,syn) > thresh_hold or makovCal(syn,next_word) > thresh_hold:
                        possible_synonym.append(syn)
                    
                combinations.append([word] + possible_synonym)
            else:
                combinations.append([word])
        else:
            combinations.append([word])

    return combinations

def generateVariants(untokenize_text):
    words = pos_tag(untokenize_text)
    for i in range(0,len(words)):
        words[i] = (words[i][0].replace(' ','_'),words[i][1])
    
    tokens = words
    
    combinations = generateCombinations(tokens,0.001)
    num_variatns = functools.reduce(lambda x, y: x*y, [len(c) for c in combinations])
    
    base_line = 0.001
    while(num_variatns > 10000):
        base_line = base_line * 2
        combinations = generateCombinations(tokens,base_line)
        num_variatns = functools.reduce(lambda x, y: x*y, [len(c) for c in combinations])
     
    combinations = list(itertools.product(*combinations))
    combinations = [' '.join(e) for e in combinations]
    return combinations