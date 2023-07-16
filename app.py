import json

from flask import Flask, jsonify
from flask import render_template
from environs import Env

env = Env()
env.read_env()

STREAM_URL = env('STREAM_URL')
TITLE = env('TITLE')

app = Flask(__name__)


@app.route('/')
def player():
    with open('history.json', 'r') as history_file:
        history = json.loads(history_file.read())

    if history:
        songs = list(reversed(history.get('songs', [])))

        if len(songs) > 0:
            now_playing = songs[-1].get('title', 'now playing')
            songs.pop(0)
        else:
            now_playing = 'now playing'

        listeners = history.get('listeners', 0)
    else:
        songs = []
        now_playing = 'now playing'
        listeners = 0

    return render_template('player.html', stream_url=STREAM_URL, title=TITLE,
                           songs=songs, now_playing=now_playing, listeners=listeners)


@app.route('/history.json')
def history_json():
    with open('history.json', 'r') as history_file:
        history = history_file.read()

    return jsonify(history)


if __name__ == '__main__':
    app.run()
