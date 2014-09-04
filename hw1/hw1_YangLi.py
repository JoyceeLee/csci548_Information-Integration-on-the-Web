# coding=utf-8
'''
Created on 2014.8.30
@author: Li, Yang
'''

from lxml import etree
import urllib2
import threading
import re
from pprint import PrettyPrinter


root = etree.Element("Paintings")
mutex = threading.Lock()
host = "http://www.musee-orsay.fr/"

def get_html(url):  
    try:
        request=urllib2.Request(url) 
        response = urllib2.urlopen(request)
        html = response.read()
        return html  
    except Exception, e:  
        print e

def constructInfo(str):
    imgHTML = etree.HTML(str)
    paint = etree.SubElement(root, "Painting")
    imgTitle = etree.SubElement(paint, "Title")
    imgLink = etree.SubElement(paint, "Link")
    imgAuthors = etree.SubElement(paint, "AuthorList")
    imgTime = etree.SubElement(paint, "PaintTime")
    imgMaterial = etree.SubElement(paint, "Material")
    imgSize = etree.SubElement(paint, "Size")
    imgHight = etree.SubElement(imgSize, "Hight") 
    imgWidth = etree.SubElement(imgSize, "Width")
    
    imgSrc = imgHTML.xpath('//*[@style="padding-top:10px"]/div/div[1]/a/img')[0].attrib['src']
    imgLink.text = host + imgSrc
    
    titleStr = imgHTML.xpath('//*[@style="padding-top:10px"]/div/div[1]/a/img')[0].attrib['title']
    imgTitle.text = titleStr
    
    infoList = imgHTML.xpath('//*[@style="padding-top:10px"]/div/div[2]/*')
    authorInfo = imgHTML.xpath('//*[@style="padding-top:10px"]/div/div[2]')[0].text.strip()
    
#     print titleStr+": "
    
    authorList = []
    if ")," in authorInfo :
        authorList = authorInfo.split(',')
    else :
        authorList.append(authorInfo)

    for author in authorList:
        try:
            imgAuthor = etree.SubElement(imgAuthors, "Author")
            authorName = etree.SubElement(imgAuthor, "Name")
            authorBio = etree.SubElement(imgAuthor, "Biographical")
            authorIdx = author.index("(")
            authorName.text = author[:authorIdx].strip()
            authorBio.text = author[authorIdx+1:-1]
        except Exception, e:
            authorName.text = authorInfo.strip()
            authorBio.text = ""
    
    paintTimeInfo = etree.tostring(infoList[2])[6:]
    if "Undated" in paintTimeInfo: 
        paintTimeInfo = ""
    imgTime.text = paintTimeInfo
    materialInfo = etree.tostring(infoList[3])[6:]
    imgMaterial.text = materialInfo
    sizeInfo = etree.tostring(infoList[4])[6:]
    try:
        sizeInfo = sizeInfo.replace('&#160;', " ")
#         print titleStr+": "
#         print sizeInfo+" ."
        hIdx = sizeInfo.index("H")
        scolIdx = sizeInfo.index(";")
        unitIdx = re.search(r"[cm|m]", sizeInfo).start()
        imgHight.text = sizeInfo[hIdx+2:scolIdx].replace(" ","")
        imgWidth.text = sizeInfo[scolIdx+4:unitIdx].replace(" ","")
        imgSize.set("unit", sizeInfo[unitIdx:])
    except Exception, e:
        imgHight.text = ""
        imgWidth.text = ""
        imgSize.set("unit", "cm")  
    return

class getImgInfo(threading.Thread):
    def __init__(self, threadname, urlList):
        threading.Thread.__init__(self)
        self.urlList = urlList
        self.name = threadname
        
    def run(self):
        for imgURL in self.urlList:
            imgPage = get_html(imgURL)
            if mutex.acquire(1):  
                constructInfo(imgPage)
                mutex.release()     
        
if __name__=='__main__' :
    homePage = get_html("http://www.musee-orsay.fr/en/collections/works-in-focus/home.html")
    htmlRoot = etree.HTML(homePage)
    paintingsHrefs = htmlRoot.xpath('//*[@id="menuNavA3"]/ul/li[2]/a')
    for href in paintingsHrefs:
        paintingsURL = host + href.attrib['href']
    paintingsPage = get_html(paintingsURL)
    paintingsRoot = etree.HTML(paintingsPage)
    paintPagesHrefs = paintingsRoot.xpath('//*[@class="archive"]/ul/li[1]/a')
    paintPageList = []
    for paintPageURL in paintPagesHrefs:
        paintPageList.append(host + paintPageURL.attrib['href'])
    numPages = len(paintPageList)
    blocks = numPages / 100
    threads = []
    for i in range(0,blocks):
        task = getImgInfo("thread_%d" % i, paintPageList[i*100:i*100+100])
        threads.append(task)
    task = getImgInfo("thread_%d" % blocks, paintPageList[blocks*100:numPages])
    threads.append(task)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    tree = etree.ElementTree(root)
    tree.write("paintings.xml", pretty_print=True, encoding="UTF-8") 