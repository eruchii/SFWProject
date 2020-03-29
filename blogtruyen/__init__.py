import requests
from bs4 import BeautifulSoup
import os
import codecs
import time

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Chapter:
    def __init__(self, url):
        self.url = url
        self.request = requests.get(url, verify = False, stream = True)
        self.soup = BeautifulSoup(self.request.content, "html.parser")
        self.name = self.getName()
        self.images = self.getImageList()
        self.prevChapter = None
        self.nextChapter = None
        try:
            self.prevChapter = "-".join(self.soup.find("link", rel = "Prev")["href"].replace("/","-").split("-")[3:])
        except:
            pass
        try:
            self.nextChapter = "-".join(self.soup.find("link", rel = "Next")["href"].replace("/","-").split("-")[3:])
        except:
            pass

    def getImageList(self):
        lst = []
        try:
            imgElement = self.soup.find("article", id = "content").findAll("img")
            lst = [x["src"] for x in imgElement]
        except:
            pass
        return lst
    def getName(self):
        return self.soup.find("h1").text

class Manga:
    global soup
    def __init__(self, url):
        global soup
        self.url = url
        start = time.time()
        headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
        success = 0
        count = 0
        while not success and count <= 10:
            try:
                request = requests.get(url, timeout = 5, headers = headers, verify = False, stream = True)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.ChunkedEncodingError):
                print("Retrying "+self.url)
                count = count + 1
            else:
                success = 1
        soup = BeautifulSoup(request.content, "html.parser")
        self.time = time.time() - start
        self.chapterList = self.getChapterList()
        self.name = soup.title.string.replace(" | BlogTruyen.Com","")
        self.thumb = soup.find("meta", property="og:image")["content"]
        if("http" not in self.thumb):
            self.thumb = "https://img.blogtruyen.com"+self.thumb
        self.id = url.split("/")[3]
        self.chapterCount = len(self.chapterList)
        self.lastUpdate = self.chapterList[0]["date"]
    def getChapterList(self):
        global soup
        pF = soup.find("div", id = "list-chapters").findAll("p")
        lst = [ {'id': x.find("a")["href"].split("/")[1],'name':x.find("a")["title"], 'url':x.find("a")["href"].replace("/","-")[1:], 'date':x.find("span", class_='publishedDate').string} for x in pF]
        return lst

def main():
    thisMangaIsGood = Manga("https://blogtruyen.com/15488/")
    print(thisMangaIsGood.name)

if __name__ == "__main__":
    main()
