import pandas as pd
import json
from helpers import *

rawDataPath = "../data/rawusers.json"
users = json.loads(readFile (rawDataPath))

print "Loaded this many data:",len(users)
# initialize feature names
photoKeys = ['id','photo_url','likes','comments','reposts']
userKeys = ['user_id','city_id']
countersKeys = ['videos','audios','photos','albums',
'friends','followers','pages','subscriptions']
keys = photoKeys + userKeys + countersKeys

data = pd.DataFrame(columns=keys)
i=0
for user in users:
    i=i+1
    if sum([x not in user.keys() for x in ['photos','city','counters']])==0:
        for photo in user['photos']:
            item = pd.DataFrame([range(len(keys))],columns=keys)

            item['id']=photo['id']
            # use 604 resolution lin
            item['photo_url'] =  photo['photo_604']
            item['likes']=photo['likes']['count']
            item['comments']=photo['comments']['count']
            item['reposts']=photo['reposts']['count']
            item['user_id']=user['id']
            if 'city' not in user.keys():
                print i
            item['city_id']=user['city']['id']
            # assign counters' features
            for k in countersKeys:
                item[k]=user['counters'][k]
            # append photo item to dataframe
            data = data.append(item,ignore_index=True)

data.to_csv('../data/data.csv',mode='w+')

goodKeys=  delFromList(keys,['comments','friends','followers'])
data.filter(goodKeys).to_csv('../data/datafilt.csv',mode='w+')

