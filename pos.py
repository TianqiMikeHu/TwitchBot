import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer


def tag(txt):
    tokenized = sent_tokenize(txt)
    output = []
    for i in tokenized:
        wordsList = nltk.word_tokenize(i.lower())
        wordsList2 = nltk.word_tokenize(i)

        tagged = nltk.pos_tag(wordsList)
        print(tagged)
        for j in range(len(tagged)):
            tagged[j] = (wordsList2[j], tagged[j][1])
        output.append(tagged)
    return output


def assemble(words):
    return TreebankWordDetokenizer().detokenize(words)
