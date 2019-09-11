from __future__ import absolute_import, division, print_function

from torch.utils.data import (DataLoader, RandomSampler, SequentialSampler,TensorDataset)
from pytorch_pretrained_bert.modeling import BertForQuestionAnswering
from pytorch_pretrained_bert.tokenization import (BasicTokenizer,BertTokenizer,whitespace_tokenize)
from utils import *
from multiprocessing import Process, Pool

class Args:
    bert_model = './resources'
    max_seq_length = 160
    doc_stride = 160
    predict_batch_size = 20
    n_best_size=20
    max_answer_length=30
    verbose_logging = False
    no_cuda = True
    seed= 42
    do_lower_case= True
    version_2_with_negative = True
    null_score_diff_threshold=0.0
    max_query_length = 64
    THRESH_HOLD = 0.95
    
args=Args()

random.seed(args.seed)
np.random.seed(args.seed)
torch.manual_seed(args.seed)

class Reader():
    def __init__(self):
        self.log = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = BertTokenizer.from_pretrained(args.bert_model, do_lower_case=args.do_lower_case)
        self.model = BertForQuestionAnswering.from_pretrained(args.bert_model)
        self.model.to(self.device)
        self.model.eval()
        self.args = args
    
    def getPredictions(self,question,paragraphs):
        try:
            question   = question.replace('_',' ')
            paragraphs = [p.replace('_',' ') for p in paragraphs]
            
            predictions = predict(question,paragraphs,self.model,self.tokenizer,self.device,self.args)
            predictions = [list(p.values()) for p in predictions]
            predictions = [[str(i) for i in p] for p in predictions]
            predictions = [i[:2] for i in predictions]
            del question, paragraphs
            return predictions
        except:
            logger.info(sys.exc_info())
            return []