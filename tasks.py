import datetime
import json
import os
from math import ceil
from celery import Celery
import requests
from environs import Env

app = Celery('tasks', broker='redis://redis/0')
app.conf.timezone = 'UTC'

env = Env()
env.read_env()

STREAM_URL = env('STREAM_URL')
STATUS_FILE_URL = env('STATUS_FILE_URL')
MAX_HISTORY_LENGTH = env.int('MAX_HISTORY_LENGTH', default=5)


def save_status_to_file(title: str, listeners: int, listeners_peak: int) -> None:
    """
    Saves actual status to file, if statuses count more 10 delete old.

    :param title:
    :param listeners:
    :param listeners_peak:
    :return:
    """
    now = datetime.datetime.now().isoformat()

    try:
        with open('history.json', 'r') as history_file:
            history: dict = json.loads(history_file.read())
    except Exception:
        history: dict = {
            'songs': [

            ],
            'listeners': 0,
            'listeners_peak': 0,
            'updated_at': now
        }

    if len(history['songs']) != 0:
        if history['songs'][-1]['title'] == title:
            history['songs'][-1]['last_played_at'] = now
        else:
            history['songs'].append({
                'title': title,
                'last_played_at': now
            })
    else:
        history['songs'].append({
            'title': title,
            'last_played_at': now
        })

    if len(history['songs']) > MAX_HISTORY_LENGTH+1:
        history['songs'] = history['songs'][-(MAX_HISTORY_LENGTH+1):]

    songs = []
    for song in history['songs']:
        song['last_played'] = str(ceil((datetime.datetime.fromisoformat(now) - datetime.datetime.fromisoformat(
            song['last_played_at'])).seconds / 60)) + '\''
        songs.append(song)
    history['songs'] = songs

    history['listeners'] = listeners
    history['listeners_peak'] = listeners_peak
    history['updated_at'] = now

    with open('history.json', 'w') as history_file:
        history_file.write(json.dumps(history))


@app.task
def load_status() -> None:
    res = requests.get(STATUS_FILE_URL)

    res.raise_for_status()

    icestats = res.json().get('icestats')

    source = {}
    if isinstance(icestats.get('source'), list):
        for item in icestats.get('source'):
            if item.get('listenurl').endswith(f'/{os.path.basename(STREAM_URL)}'):
                source = item
                break
    else:
        if icestats.get('source').get('listenurl').endswith(f'/{os.path.basename(STREAM_URL)}'):
            source = icestats.get('source')

    if not source:
        raise Exception('Source not found')

    save_status_to_file(
        title=source.get('title'),
        listeners=source.get('listeners'),
        listeners_peak=source.get('listener_peak')
    )


app.conf.beat_schedule = {
    'update_status_every_3_secs': {
        'task': 'tasks.load_status',
        'schedule': 3
    },
}