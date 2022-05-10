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

            with open(os.path.join(path, "download.txt"), "w+") as f:
                if plotseq:
                    f.write(f"{out_name}.zip")
                else:
                    f.write(f"{out_name}.csv")

            with open(os.path.join(path, "progress.txt"), "w+") as f:
                f.write("QUEUED")

            file.save(os.path.join(path, app.config["UPLOAD_FILENAME"]))

            q.enqueue(run_command, file_id, out_name, plotseq, debug,
                      job_id=file_id)

            return file_id

    return render_template("index.html")


def run_command(file_id, out_name, plotseq, debug):
    uuid = file_id
    model_file = "models/ant_finetune/checkpoint.pth"
    output_dir = os.path.join("uploads", uuid)
    data_root_dir = output_dir
    write_images = "pretty" if plotseq else False
    write_images = "debug" if debug and plotseq else write_images

    track.main(model_file, data_root_dir, output_dir,
               out_name, write_images, debug)
    return "Complete"


@app.route('/progress/<name>')
def progress(name):
    # TODO Error handling
    try:
        f = open(os.path.join(app.config["UPLOAD_FOLDER"], name, "progress.txt"))
    except FileNotFoundError:
        return "Processing..."
    progress = f.read().split()
    f.close()

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
    folder = os.path.join(app.config["UPLOAD_FOLDER"], name)
    f = open(os.path.join(folder, "download.txt"))
    download_file = f.read()
    f.close()

    return send_from_directory(folder, download_file)


@app.route('/download', methods=['GET'])
def return_file():
    obj = request.args.get('obj')
    loc = os.path.join("static", obj)
    print(loc)
    try:
        return send_file(os.path.join("runs/detect", obj), attachment_filename=obj)
    except Exception as e:
        return str(e)

@app.route('/u/<uuid>', methods=['GET'])
def download_page(uuid):
    uuids = uuid.split('-')
    names = []
    for uuid in uuids:
        # TODO error handling
        f = open(os.path.join(app.config["UPLOAD_FOLDER"], uuid, "download.txt"))
        name = os.path.splitext(f.read())[0]
        names.append(name)
        f.close()

    tasks = [{'uuid': uuid, 'name': name} for uuid, name in zip(uuids, names)]
    # Setup progress get requests?
    #   Need download.js file in static
    return render_template('download.html', tasks=tasks)


if __name__ == "__main__":
    print('to upload files navigate to http://127.0.0.1:5000/')
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
