# Vietnamese question answering with BERT

- Q: Người giàu nhất việt nam (richest man in Vietnam) ?
- A: Phạm Nhật Vượng

- Q: Ai là tác giả của ngôn ngữ lập trình C (Who invented C programming language)
- A: Dennis Ritchie

Install prerequisites:
pip3 install -r requirements.txt

Download pretrain model at: https://drive.google.com/open?id=1ml-Qwv4yHxepp852N-aL0U5iZzqLNZ4B
then extract and put all files into "resources" directory

Want to understand how the framework work ?
Open notebook file --> change the question --> run line by line

Due to the limitation of current dataset, the system only supports questions about person
Eg:
+ Who is the author of C programming language?
+ The richest man in Viet Nam ?


# Architecture Overview
 - Question Answering based IR - Speech and language processing (daniel jurafsky)
 - https://web.stanford.edu/~jurafsky/slp3/24.pdf
 
<img src="Framework.png">
