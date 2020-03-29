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
IDs = {}

maxthreads = 100
sema = Semaphore(value=maxthreads)
global cookie
cookie = {
	"_ga":"GA1.2.2054448878.1553762453",
	"btpop1":"Popunder"
}

def encodeImageUrl(url):
	return base64.b64encode(url.encode("utf-8")).decode("utf-8")

@app.route("/stream/<base64Url>")
def streamImage(base64Url):
	dUrl = base64.b64decode(base64Url).decode("utf-8")
	filename = dUrl.split("/")[-1]
	if(not os.path.exists("./img/"+base64Url)):
		s = requests.Session()
		cookies = dict(s.get("https://blogtruyen.com", verify = False).cookies)
		headers = {"Referer" : "https://blogtruyen.com/"}
		r = s.get(url = dUrl, headers = headers, cookies = cookies, verify = False)
		with open(r"./img/"+base64Url,"wb") as f:
			f.write(r.content)
		response = make_response(r.content)
		# if(".png" in dUrl):
		# 	response.headers.set('Content-Type', 'image/png')
		# else:
		# 	if(".jpg" in dUrl or ".jpeg" in dUrl):
		# 		response.headers.set('Content-Type', 'image/jpeg')
		response.headers.set('Content-Disposition', 'inline', filename='%s' % filename)
		return response
	else:
		return send_from_directory("./img", filename = base64Url, attachment_filename=filename)
		# if(".png" in dUrl):
		# 	return send_from_directory("./img", filename = base64Url, mimetype="image/png", attachment_filename=filename)
		# else:
		# 	if(".jpg" in dUrl or ".jpeg" in dUrl):
		# 		return send_from_directory("./img", filename = base64Url, mimetype="image/jpeg", attachment_filename=filename)
		# 	else:
		# 		if(".gif" in dUrl):
		# 			return send_from_directory("./img", filename = base64Url, mimetype="image/gif", attachment_filename=filename)

def multithreadRequest(url):
	sema.acquire()
	global manga
	global IDs
	start = time.time()
	m = blogtruyen.Manga(url)
	manga.append(m)
	print("%s: %f" % (url, m.time))
	manga = sorted(manga, key = lambda x: datetime.strptime(x.lastUpdate, "%d/%m/%Y %H:%M"), reverse = True)
	for i in range(0, len(manga)):
		IDs[manga[i].id] = i
	for i in range(0, len(manga)):
		if("img.blogtruyen.com" in manga[i].thumb or "i.blogtruyen.com" in manga[i].thumb):
			newThumb = encodeImageUrl(manga[i].thumb)
			if(len(newThumb) < 256):
				manga[i].thumb = "/stream/%s" % newThumb
	sema.release()

def update():
	global followingManga
	global manga
	manga = []
	
	followingManga = [x.strip("\n") for x in open("following.txt","r").readlines()]
	start = time.time()
	threads = []
	for x in followingManga:
		t = Thread(target= multithreadRequest, args = (x,))
		t.start()
		threads.append(t)
	print("total: %f" % (time.time()-start))


def exportJson():
	global manga
	for x in manga:
		with codecs.open("./data/"+x.id+".json", "w", "utf-8") as f:
			json.dump(x.__dict__, f, indent = 4)


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

@app.route("/clear")
def clear_cache():
	lst = os.listdir("./img")
	for a in lst:
		os.remove("./img/"+a)
	return redirect(url_for("main"))

@app.context_processor
def infomation():
	mangaPerColumn = 5
	return dict(column = mangaPerColumn)

def run_server():
	app.jinja_env.globals.update(min=min)
	update()
	# exportJson()
	app.jinja_env.auto_reload = True
	app.config['TEMPLATES_AUTO_RELOAD'] = True
	http_server = WSGIServer(('0.0.0.0', 80), DebuggedApplication(app))
	http_server.serve_forever()

if __name__ == '__main__':
	run_with_reloader(run_server)
