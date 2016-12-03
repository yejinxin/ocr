# -*- coding: utf-8 -*-

from PIL import Image
import cPickle as pickle
import os.path
from pprint import pprint
import math

IMG_DIR=os.path.join(os.path.split(os.path.realpath(__file__))[0], "images")

def splitIM(im):
    '''Split the Image into 4 small ones by size.
    '''
    (width, height)=im.size
    k1=im.crop((0,             0,   width/4,   height))
    k2=im.crop((width/4 + 1,   0,   width/2,   height))
    k3=im.crop((width/2 + 1,   0,   width*3/4, height))
    k4=im.crop((width*3/4 + 1, 0,   width,     height))
    return k1, k2, k3, k4

def getOutline(k1):
    '''Get the outline of a grey(mode L) Image by converting it into a balck
    (mode 1) one.
    '''
    kh=k1.histogram()
    n1=Image.new("1", k1.size, 1)
    (width, height) = k1.size
    for x in range(width):
        for y in range(height):
            pix=k1.getpixel((x,y))
            #pixel greater than 180 is usually a background color. 
            if pix < 180 and kh[pix] > 1:
                n1.putpixel((x,y), 0)
    return n1

def normalize(n1):
    '''Cut out the blank at bordor, and normalize it.
    '''
    (width, height) = n1.size
    #n1.show()
    (left, top) = (0, 0)
    (right, bottom) = (width - 1, height - 1)
    _LF=False
    while left < width and not _LF:
        tmp=0
        while tmp < height:
            if n1.getpixel((left, tmp)) == 0:
                _LF=True
                break
            tmp += 1
        left += 1
    
    _RF=False
    while right > left and not _RF:
        tmp=0
        while tmp < height:
            if n1.getpixel((right, tmp)) == 0:
                _RF=True
                break
            tmp += 1
        right -= 1
    
    _TF=False
    while top < height and not _TF:
        tmp=0
        while tmp < width:
            if n1.getpixel((tmp, top)) == 0:
                _TF=True
                break
            tmp += 1
        top += 1
    
    _BF=False
    while bottom > top and not _BF:
        tmp=0
        while tmp < width:
            if n1.getpixel((tmp, bottom)) == 0:
                _BF=True
                break
            tmp += 1
        bottom -= 1
    
    pim=n1.crop((left-1, top-1, right+2, bottom+2))
    pim=pim.resize(n1.size)  
    return pim    
    
def magnitude(xy):
    '''calculate the magnitude of a matrix'''
    total=0
    for x in xy:
        for y in x:
            total += y**2
    return math.sqrt(total)

def relation(xy1, xy2):
    '''calculate normalized relationship between two matrix, using VSM and cosine'''
    topvalue=0
    for i in range(len(xy1)):
        for j in range(len(xy1[i])):
            topvalue += xy1[i][j]*xy2[i][j]
    return topvalue / (magnitude(xy1)*magnitude(xy2))

def im2list(im):
    '''get a matrix representing the Image'''
    xy=[]
    for j in range(im.size[1]):
        xy.append([1 if im.getpixel((i,j)) == 0 else 0 for i in range(im.size[0])])
    return xy
    
def train(filename):
    def learn(k1, num):
        k1=k1.convert('L')
        n1=getOutline(k1)
        (width, height) = n1.size
        pim=normalize(n1)
        #pim.show()
        dnum=data.get(num)
        if dnum is None:
            dnum = [ ]
            for i in range(height):
                dnum.append([0]*width)
        for i in range(height):
            for j in range(width):
                if pim.getpixel((j,i)) == 0:
                    #print "i=", i, " j=", j
                    dnum[i][j] += 1
        data[num]=dnum
        
    ###################--main--################################
    data={}
    with open(filename,'r') as f:
        for line in f.readlines():
            if not line.strip() or line.startswith('#'):
                continue
            (png, nums) = line.split('=')
            im=Image.open(os.path.join(IMG_DIR, png))
            (k1, k2, k3, k4)=splitIM(im)
            learn(k1, nums[0])
            learn(k2, nums[1])
            learn(k3, nums[2])
            learn(k4, nums[3])
    with open('data.pkl', 'wb') as pkf:
        pickle.dump(data, pkf)

def getstat():
    '''Get trained data'''
    with open('data.pkl', 'rb') as pkf:
        data=pickle.load(pkf)
        return data
    
def showstat(num=None):
    with open('data.pkl', 'rb') as pkf:
        data=pickle.load(pkf)
        if num is None:
            pprint(data)
        else:
            pprint(data[num])

def matchSingle(k1):
    '''Test single number.'''
    k1=k1.convert('L')
    n1=getOutline(k1)
    pim=normalize(n1)
    #pim.show()
    xy=im2list(pim)
    data=getstat()
    return sorted([(num, relation(xy, dnum)) for num, dnum in data.items()], 
                  key=lambda i:i[1], reverse=True)

def testCaptcha(filename):
    '''Test a Captcha.'''
    im=Image.open(filename)
    (k1,k2,k3,k4) = splitIM(im)
    return matchSingle(k1)[0][0] + matchSingle(k2)[0][0] + matchSingle(k3)[0][0] + matchSingle(k4)[0][0]
    
if __name__=='__main__':
    #train(os.path.join(IMG_DIR, 'train.txt'))
    #showstat()
    filename=os.path.join(IMG_DIR, '10.png')
    print testCaptcha(filename)
    
    im=Image.open(filename)
    im.show()        
    (k1,k2,k3,k4) = splitIM(im)
    print matchSingle(k1)[:3]
    print matchSingle(k2)[:3]
    print matchSingle(k3)[:3]
    print matchSingle(k4)[:3]
    