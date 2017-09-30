"""
Used for generation of new features
Lets assume that there's an objective metrics of photo's quality:
    a) contrast
    b) saturation
    c) white balance
    d) resolution
OpenCV provides a feature detection and other fancy methods:
    e) eyes
    f) faces g) border lines
I think that
- lighter and warmer photos will get more likes
- size of eyes in respect to image size is good feature
- photos with sky/buildings will get more likes
- photos with sports/concerts too
- photos with friends too

Problems:
- professional photos of models/nature (fakes) get less likes than shitty
    low-res photos of owner of account!
- shitty photo with some celeb will get more likes
- the same photo used by different people can get different likes qnty
- 
"""
import cv2
import numpy as np
import scipy.stats

from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from matplotlib import gridspec, cm
import pandas as pd
import helpers

def generate_features(X,verbose = 0):
    if not type(X) ==pd.DataFrame:
        print type(X)
        raise Exception("input is not a pandas.DataFrame")
    if len(X) == 0:
        raise Exception("input is length zero")

    # initialise holder
    f_df = pd.DataFrame()
    n=0
    for idx,x in X.iterrows():
        feats = Features(helpers.getImg(x['photo_url'])) 
        if (verbose>0):print "> generating features for num",idx
        f_df = f_df.append(feats.generate(verbose=verbose-1),ignore_index = True)
        
    return pd.concat([X,f_df],axis=1)

class Features:

    def __init__(self,img):
        self._img = img
        
    def generate(self,verbose = 0):
        f = {}
        if verbose>0: print ">> contrast"
        f['contrast_gray'],f['contrast_rgb'] = self.contrast()
        if verbose>0: print ">> mean"
        f['edges_mean'] = self.edges()
        if verbose>0: print ">> faces_eyes"
        f['face_rel'], f['eye_rel'],f['face_count'] = self.faces_eyes()
        return f

    def faces_eyes(self):
        # load pre trained models and grayscale img
        face_cascade = cv2.CascadeClassifier('../data/haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier('../data/haarcascade_eye.xml')
        try:gray = cv2.cvtColor(self._img, cv2.COLOR_BGR2GRAY)
        except Exception: gray = self._img
        # find faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        # init accumulators
        eyes_sq = 0
        faces_sq = 0
        for (x,y,w,h) in faces:
            # find eyes for each face
            roi_gray = gray[y:y+h, x:x+w]
            eyes =  eye_cascade.detectMultiScale(roi_gray)
            # add square of face
            faces_sq = faces_sq + h*w
            # add square of each eye to eye square accumulator
            eyes_sq = eyes_sq + sum([eyes[i][2]*eyes[i][3] for i in range(len(eyes))])
            
        sqi =float(self._img.shape[0]*self._img.shape[1])
        # return relative squares and faces count
        return faces_sq/sqi,eyes_sq/sqi,len(faces)

    def edges(self):
        # use libraly to calculate edges in image
        edges = cv2.Canny(self._img,80,100)
        # return mean of edges heatmap
        return np.mean(edges)
        
    def contrast(self):
        ### contrastness in entropy of hist
        # convert to gray
        try:gray = cv2.cvtColor(self._img, cv2.COLOR_BGR2GRAY)
        except Exception: gray = self._img
        gray = np.float32(gray)
        # calculate contrastness for gray image
        h_g =  np.histogram(gray)
        e_g = scipy.stats.entropy(h_g[0])
        #if image has 3 channels
        if(len(self._img.shape)>2):
            # calculate 3 hists for each channel than return mean of entropy for each 
            rgbhist = [np.histogram(self._img[:,:,i],bins = 30) for i in range(3)]
            ent = [scipy.stats.entropy(rgbhist[i][0]) for i in range(3)]
            return e_g,np.mean(ent)
        else:
            # else return entropy for grayscale twice
            return e_g,e_g
       
class Corners:
    def __init__(self, img, percentile=97):
        # convert image to grayscale
        try:gray = cv2.cvtColor(self._img, cv2.COLOR_BGR2GRAY)
        except Exception: gray = self._img
        gray = np.float32(gray)
        # set image and percentile to local attribute 
        self._img = img
        self._pcnt = percentile
        # perform corner search
        self._dst = cv2.cornerHarris(gray, 2, 3, 0.04)
        # calc threchold
        self._thr = np.percentile(self._dst,percentile)
        self.__clustered = False 

    def cluster(self,eps = 25):
        dots  =[]
        im = self._img
        # populate array with pixels where dst is bigger than threshold
        for i in range(im.shape[0]):
            for j in range(im.shape[1]):
                if (self._dst[i][j]>self._thr):
                    dots.append([i,j])
        X= np.asarray(dots)
        # Run DBSCAN on array
        self._clusters = DBSCAN(eps=eps).fit(X)
        self.__clustered = True

    def show(self):
        img = self._img
        # dilate dst, to make dmall dots instead of pixels
        dst = cv2.dilate(self._dst,None)
        # paint with blue
        img[dst > self._thr] = [0,0,255]
        
        fig = plt.figure(figsize=(10, 8))
        gs = gridspec.GridSpec(1, 2)
        ax0 = plt.subplot(gs[0])
        ax0.imshow(dst)
        ax1 = plt.subplot(gs[1])
        ax1.imshow(img)
        plt.show()
