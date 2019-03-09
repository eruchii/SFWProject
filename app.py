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

app = Flask(__name__)

global followingManga
followingManga = [x.strip("\n") for x in open("following.txt","r").readlines()]
global manga
manga = [blogtruyen.Manga(x) for x in followingManga if "blogtruyen" in x]
app.jinja_env.globals.update(min=min)

@app.route("/")
def main():
    global manga
    page = request.args.get("page",default=1,type=int)
    return render_template("main.html", manga = manga, page = page)

@app.route("/manga/<int:mangaId>")
def mangaInfo(mangaId):
    thisManga = manga[mangaId]
    return render_template("manga.html", manga = thisManga)

@app.route("/read/<chapterId>")
def read(chapterId):
    url = "https://blogtruyen.com/" + chapterId+ "/thisisfiller"
    thisChapter = blogtruyen.Chapter(url)
    return render_template("read.html", chapter = thisChapter)

@app.context_processor
def infomation():
    mangaPerColumn = 5
    return dict(column = mangaPerColumn)

def run_server():
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    http_server = WSGIServer(('0.0.0.0', 8080), DebuggedApplication(app))
    http_server.serve_forever()

if __name__ == '__main__':
	run_with_reloader(run_server)
