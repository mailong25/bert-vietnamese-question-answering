from gg_search import GoogleSearch
ggsearch = GoogleSearch()
from relevance_ranking import rel_ranking
from reader import Reader
reader = Reader()

if __name__ == "__main__":
    
    question = 'ai là người giàu nhất Việt Nam'
    
    #Using google to find relevant documents
    links, documents = ggsearch.search(question)
    
    #Find relevant passages from documents
    passages = rel_ranking(question,documents)
    
    # Select top 40 paragraphs
    passages = passages[:40]
    
    #Using reading comprehend model (BERT) to extract answer for each passage
    answers = reader.getPredictions(question,passages)
    
    #Reranking passages by answer score
    answers = [[passages[i], answers[i][0],answers[i][1]] for i in range(0,len(answers))]
    answers = [a for a in answers if a[1] != '']
    answers.sort(key = lambda x : x[2],reverse=True)
    
    print("Final result: ")
    print("Passage: ", answers[0][0])
    print("Answer : ", answers[0][1])
    print("Score  : ", answers[0][2])
    