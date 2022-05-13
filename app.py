import sys, os
import subprocess
from flask import Flask, flash, request, redirect, render_template, send_file, url_for, send_from_directory
from werkzeug.utils import secure_filename

import redis
from rq import Queue

import uuid

import time

import track

app = Flask(__name__)

r = redis.Redis()
q = Queue(connection=r)

app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, 'uploads')
app.config["UPLOAD_FILENAME"] = 'in.mp4'
app.config["DOWNLOAD_FILENAME"] = 'out.mp4'
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file:
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

            file.save(os.path.join(path, app.config["UPLOAD_FILENAME"]))

            q.enqueue(run_command, file_id, out_name, plotseq, debug,
                      job_id=file_id)

            return file_id

    return render_template("index.html")


def run_command(file_id, out_name, plotseq, debug):
    uuid = file_id
    model_file = "models/ant_finetune/checkpoint.pth"
    write_images = "pretty" if plotseq else False
    write_images = "debug" if debug and plotseq else write_images

    track.main(model_file, uuid, r, out_name, write_images, debug)
    return "Complete"


@app.route('/progress/<name>')
def progress(name):
    # TODO Error handling
    progress = r.hget(name, "progress").decode('utf-8').split()

    if progress[0] == "COMPLETE":
        return "COMPLETE"
    elif progress[0] == "PROCESSING":
        return "Processing..."
    elif progress[0] == "QUEUED":
        # Note, this is O(n)
        job_ids = q.job_ids
        try:
            place = job_ids.index(name) + 1
            string = f"Queued: {place}/{len(job_ids)}"
        except ValueError:
            string = "Queued..."

        return string
    else:
        stage, frame_id, num_frames = progress
        return f"{stage}: Frame {frame_id}/{num_frames}"


@app.route('/uploads/<name>')
def download_file(name):
    download_file = r.hget(name, "download").decode('utf-8')

    return send_from_directory(folder, download_file)


@app.route('/download/<uuids>')
def return_file(uuids):
    # TODO should probably convert everything to redis first
    uuids = uuids.split('-')
    if len(uuids) == 0:
        download_file = r.hget(name, "download").decode('utf-8')

        return send_from_directory(folder, download_file)
    else:
        names = []
        for uuid in uuids:
            f = open(os.path.join(app.config["UPLOAD_FOLDER"],
                                  uuid, "download.txt"))
            name = os.path.splitext(f.read())[0]
            names.append(name)
            f.close()


@app.route('/u/<uuid>', methods=['GET'])
def download_page(uuid):
    uuids = uuid.split('-')
    names = [os.path.splitext(r.hget(uuid, "name").decode('utf-8'))[0] for uuid in uuids]

    tasks = [{'uuid': uuid, 'name': name} for uuid, name in zip(uuids, names)]

    return render_template('download.html', tasks=tasks)


if __name__ == "__main__":
    print('to upload files navigate to http://127.0.0.1:5000/')
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
