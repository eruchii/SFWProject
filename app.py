import gevent.monkey
gevent.monkey.patch_all()
from werkzeug.serving import run_with_reloader
from werkzeug.debug import DebuggedApplication
from gevent.pywsgi import WSGIServer
from werkzeug.serving import run_simple

from flask import *
import requests
import os
import json
import blogtruyen
from datetime import datetime
import sys
import time
import codecs
from threading import Thread, Semaphore
import base64

app = Flask(__name__)

global followingManga
global manga
manga = []
global IDs 

maxthreads = 12
sema = Semaphore(value=maxthreads)
global cookie
cookie = {
	"_ga":"GA1.2.2054448878.1553762453",
	"btpop1":"Popunder"
}

def multithreadRequest(url):
    sema.acquire()
    start = time.time()
    m = blogtruyen.Manga(url)
    manga.append(m)
    print("%s: %f" % (url, m.time))
    sema.release()

def encodeImageUrl(url):
    return base64.b64encode(url.encode("utf-8")).decode("utf-8")

@app.route("/stream/<base64Url>")
def streamImage(base64Url):
    dUrl = base64.b64decode(base64Url).decode("utf-8")
    cookies = {
	"__cfduid":"d3750ed1feee91e95c77f9ef76cb4a1701552046450",
	"_ga":"GA1.2.2054448878.1553762453",
	"btpop1":"Popunder"
    }
    r = requests.get(dUrl, cookies = cookies)
    filename = dUrl.split("/")[-1]
    response = make_response(r.content)
    if(".png" in dUrl):
        response.headers.set('Content-Type', 'image/png')
    else:
        if(".jpg" in dUrl or ".jpeg" in dUrl):
            response.headers.set('Content-Type', 'image/jpeg')
    response.headers.set('Content-Disposition', 'inline', filename='%s' % filename)
    return response

def update():
    global followingManga
    global manga
    manga = []
    global IDs
    followingManga = [x.strip("\n") for x in open("following.txt","r").readlines()]
    followingManga = list(set(followingManga))
    start = time.time()
    threads = []
    for x in followingManga:
        t = Thread(target= multithreadRequest, args = (x,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print("total: %f" % (time.time()-start))
    manga = sorted(manga, key = lambda x: int(x.url.split("/")[3]))
    for i in range(0, len(manga)):
         if("img.blogtruyen.com" in manga[i].thumb or "i.blogtruyen.com" in manga[i].thumb):
            manga[i].thumb = "/stream/%s" % encodeImageUrl(manga[i].thumb)
    with open("following.txt","w") as f:
        for x in manga:
            f.write(x.url+"\n")
    manga = sorted(manga, key = lambda x: datetime.strptime(x.lastUpdate, "%d/%m/%Y %H:%M"), reverse = True)
    
    IDs = {}
    for i in range(0, len(manga)):
        IDs[manga[i].id] = i
app.jinja_env.globals.update(min=min)

def exportJson():
    followingManga = [x.strip("\n") for x in open("following.txt","r").readlines()]
    followingManga = list(set(followingManga))
    for x in followingManga:
        print(x)
        manga = blogtruyen.Manga(x)
        with codecs.open("./data/"+manga.id+".json", "w", "utf-8") as f:
            json.dump(manga.__dict__, f, indent = 4)


@app.route("/")
def main():
    global manga
    global cookie
    page = request.args.get("page",default=1,type=int)
    return render_template("main.html", manga = manga, page = page)

@app.route("/manga/<mangaId>")
def mangaInfo(mangaId):
    thisManga = manga[IDs[mangaId]]
    return render_template("manga.html", manga = thisManga)

@app.route("/read/<chapterId>")
def read(chapterId):
    url = "https://blogtruyen.com/" + chapterId.replace("-","/",1)
    thisChapter = blogtruyen.Chapter(url)
    images = thisChapter.images
    for i in range(0, len(images)):
        if("img.blogtruyen.com" in images[i] or "i.blogtruyen.com" in images[i]):
            images[i] = "/stream/%s" % encodeImageUrl(images[i])
    return render_template("read.html", chapter = thisChapter, images = images)
@app.route("/update")
def updateNewManga():
    update()
    return redirect(url_for("main"))
@app.route("/add",methods=['GET','POST'])
def addManga():
    if request.method == "POST":
        newUrl = request.form["mangaUrl"]
        if("blogtruyen" in newUrl):
            with open("following.txt", "a") as f:
                f.write(newUrl)
                f.write("\n")
            return render_template("add.html", status = 2)
        return render_template("add.html", status = 1)
    return render_template("add.html", status = 0)


@app.context_processor
def infomation():
    mangaPerColumn = 5
    return dict(column = mangaPerColumn)

def run_server():
    update()
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    http_server = WSGIServer(('0.0.0.0', 8080), DebuggedApplication(app))
    http_server.serve_forever()

if __name__ == '__main__':
	run_with_reloader(run_server)
#    exportJson()
