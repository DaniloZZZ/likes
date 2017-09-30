usersPath = '../data/data.csv'
from PIL import Image
import requests
import numpy as np
from StringIO import StringIO
import pandas
def getImg(url):
    response = requests.get(url)
    return np.array(Image.open(StringIO(response.content)))

def getUsers():
    return pandas.DataFrame.from_csv(usersPath)

def readFile(path):
    file = open(path,'r')
    return file.read()

def delFromList(lis,vals):
    res= [ ]
    for l in lis:
        bad = False
        for v in vals:
            if(l==v):
                bad=True
        if not(bad):
            res.append(l)
    return res

def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z