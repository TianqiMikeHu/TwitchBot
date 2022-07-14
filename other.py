from tools import *

################################################    Other functions
def updatedeath(attributes):
    if len(attributes['args'])<2:
        return "Usage: !updatedeath [link]"
    myquery = 'call bot.updatedeath(%s)'
    query(attributes['pool'], myquery, True, (attributes['args'][1],))
    return "Done"

def updatepb(attributes):
    if len(attributes['args'])<2:
        return "Usage: !updatepb [link]"
    myquery = 'call bot.updatepb(%s)'
    query(attributes['pool'], myquery, True, (attributes['args'][1],))
    return "Done"

def manifest(attributes):
    return ' '.join(attributes['args'][1:])