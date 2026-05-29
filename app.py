import os
from flask import Flask, send_file
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chat123'

socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return send_file("chat.html")

@socketio.on("message")
def handle_message(msg):
    send(msg, broadcast=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)