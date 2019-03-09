import requests
from bs4 import BeautifulSoup
import os
import codecs

class Chapter:
    def __init__(self, url):
        self.url = url
        self.request = requests.get(url)
        self.soup = BeautifulSoup(self.request.content, "html.parser")
        self.name = self.getName()
        self.images = self.getImageList()

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
    def __init__(self, url):
        self.url = url
        self.request = requests.get(url)
        self.soup = BeautifulSoup(self.request.content, "html.parser")
        self.chapterList = self.getChapterList()
        self.name = self.soup.title.string.replace(" | BlogTruyen.Com","")
        self.thumb = self.soup.find("meta", property="og:image")["content"]
        self.id = url.split("/")[3]
        self.chapterCount = len(self.chapterList)
    def getChapterList(self):
        pF = self.soup.find("div", id = "list-chapters").findAll("p")
        lst = [ {'id': x.find("a")["href"].split("/")[1],'name':x.find("a")["title"], 'url':"https://blogtruyen.com" + x.find("a")["href"], 'date':x.find("span", class_='publishedDate').string} for x in pF]
        return lst

def main():
    thisMangaIsGood = Manga("https://blogtruyen.com/15488/")
    print(thisMangaIsGood.name)

if __name__ == "__main__":
    main()
