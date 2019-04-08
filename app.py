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

app = Flask(__name__)

global followingManga
global manga
manga = []
global IDs 

maxthreads = 12
sema = Semaphore(value=maxthreads)

def multithreadRequest(url):
    sema.acquire()
    start = time.time()
    m = blogtruyen.Manga(url)
    manga.append(m)
    print("%s: %f" % (url, m.time))
    sema.release()

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
    return render_template("read.html", chapter = thisChapter)
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
