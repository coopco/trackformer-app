import sys, os
import subprocess
from flask import abort, Flask, flash, request, redirect, render_template, send_file, url_for, send_from_directory
from werkzeug.utils import secure_filename

import redis
from rq import Queue

import uuid

import time

from track import run_command

app = Flask(__name__)

app.config.update(
    UPLOAD_FOLDER=os.path.join(app.root_path, 'uploads'),
    UPLOAD_FILENAME='in.mp4',
    DOWNLOAD_FILENAME='out.mp4',
    TASK_TIMEOUT=60*60,
    UPLOAD_NUM_LIMIT=10,
    MAX_CONTENT_LENGTH=1024*1024*1024
)

r = redis.Redis()
q = Queue(connection=r,
          default_timeout=app.config['TASK_TIMEOUT'])

# import toml
# app.config.from_file('config.toml', load=toml.load)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        plotseq = True if request.form.get('plotseq') == "true" else False
        debug = True if request.form.get('debug') == "true" else False

        file_id = str(uuid.uuid4().hex)
        path = os.path.join(app.config["UPLOAD_FOLDER"], file_id)
        os.makedirs(path)

        out_name = os.path.splitext(file.filename)[0]

        r.hset(file_id, mapping={
            "name": out_name,
            "progress": "QUEUED",
            "download": out_name + ('.zip' if plotseq else '.csv')
        })
        r.expire(file_id, 24*60*60)

        file.save(os.path.join(path, app.config["UPLOAD_FILENAME"]))

        q.enqueue(run_command, file_id, out_name, plotseq, debug,
                  job_id=file_id)

        return file_id

    return render_template("index.html")


@app.route('/progress/<uuid>')
def progress(uuid):
    try:
        progress = r.hget(uuid, "progress").decode('utf-8').split()
    except AttributeError:
        abort(404)

    if progress[0] == "COMPLETE":
        return "COMPLETE"
    elif progress[0] == "PROCESSING":
        return "Processing..."
    elif progress[0] == "QUEUED":
        # Note, this is O(n)
        job_ids = q.job_ids
        try:
            place = job_ids.index(uuid) + 1
            string = f"Queued: {place}/{len(job_ids)}"
        except ValueError:
            string = "Queued..."

        return string
    else:
        stage, frame_id, num_frames = progress
        return f"{stage}: Frame {frame_id}/{num_frames}"


@app.route('/uploads/<uuid>')
def download_file(uuid):
    try:
        download_file = r.hget(uuid, "download").decode('utf-8')
    except AttributeError:
        abort(404)

    return send_from_directory(os.path.join("uploads", uuid), download_file)


@app.route('/u/<uuid>', methods=['GET'])
def download_page(uuid):
    uuids = uuid.split('-')

    if len(uuids) > app.config['UPLOAD_NUM_LIMIT']:
        abort(404)

    try:
        names = [os.path.splitext(r.hget(uuid, "name").decode('utf-8'))[0] for uuid in uuids]
    except AttributeError:
        abort(404)

    tasks = [{'uuid': uuid, 'name': name} for uuid, name in zip(uuids, names)]

    return render_template('download.html', tasks=tasks)


@app.errorhandler(413)
def file_too_big(e):
    return 'File to big: ' + str(e)


if __name__ == "__main__":
    print('to upload files navigate to http://127.0.0.1:5000/')
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
