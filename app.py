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
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )