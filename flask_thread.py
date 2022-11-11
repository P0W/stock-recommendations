from werkzeug.serving import make_server
import threading
import logging as log
from flask import Flask, render_template


class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server("0.0.0.0", 5000, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        log.info("starting server")
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


def start_server(websocketWorker):
    global server
    app = Flask(__name__)
    # App routes defined here

    @app.route("/")
    def home():
        websocketWorker.start()
        return render_template("logs.html", data={})

    server = ServerThread(app)
    server.start()
    log.info("server started")


def stop_server():
    global server
    server.shutdown()
