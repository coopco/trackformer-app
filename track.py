import os
import time
import zipfile
from os import path as osp
from argparse import ArgumentParser

from trackformer import Trackformer
from util import video_to_frames, frames_to_video
import redis


def run_command(file_id, out_name, plotseq, debug):
    r = redis.Redis()
    uuid = file_id
    model_file = "models/ant_finetune/checkpoint.pth"
    write_images = "pretty" if plotseq else False
    write_images = "debug" if debug and plotseq else write_images

    main(model_file, uuid, r, out_name, write_images, debug)
    return "Complete"


def main(checkpoint_file, uuid, r, out_name="out",
         write_images="pretty", debug=False):
    output_dir = osp.join("uploads", uuid)
    data_root_dir = output_dir

    if output_dir is not None:
        if not osp.exists(output_dir):
            os.makedirs(output_dir)

    r.hset(uuid, "progress", "PROCESSING")

    # Build Model
    tracker = Trackformer()
    tracker.build_model(checkpoint_file)

    start = time.time()

    # For each video
    #   Extract frames from video
    filename = osp.join(output_dir, "in.mp4")
    video_to_frames(filename, output_dir)
    #   Build dataset
    tracker.reset()
    tracker.build_dataset(data_root_dir)

    for frame_id, frame_data in enumerate(tracker.data_loader):
        if debug and frame_id == 10:
            break

        tracker.step(frame_data)
        string = f"Tracking {str(frame_id+1)} {len(tracker.data_loader)}"
        r.hset(uuid, "progress", string)

    results = tracker.results()

    print(f"RUNTIME: {time.time() - start :.2f} s")

    #   Write results
    if output_dir is not None:
        path = osp.join(output_dir, f"{out_name}.csv")
        tracker.write_results(results, path)

        print(write_images)
        if write_images:
            out_path = osp.join(output_dir, "plots")
            tracker.plot_seq(results, out_path, write_images)
            frames_to_video(out_path, osp.join(output_dir, f"{out_name}.mp4"))

    r.hset(uuid, "progress", "COMPLETE")

    if write_images:
        # Zip
        path = osp.join(output_dir, f"{out_name}.zip")
        with zipfile.ZipFile(path, 'w') as z:
            z.write(osp.join(output_dir, f"{out_name}.csv"),
                f"{out_name}.csv")
            z.write(osp.join(output_dir, f"{out_name}.mp4"),
                f"{out_name}.mp4")


if __name__=="__main__":
    parser = ArgumentParser()
    parser.add_argument("-u", "--uuid", dest="uuid", default="../test_track")
    parser.add_argument("-o", "--out-name", dest="out_name",
                        default="out")
    parser.add_argument("--plotseq", action='store_true', dest="plotseq")
    parser.add_argument("--debug", action='store_true', dest="debug") #TODO for plot_seq
    parser.add_argument("-m", "--model-file", dest="model_file",
                        default="models/ant_finetune/checkpoint.pth")

    args = parser.parse_args()

    checkpoint_file = args.model_file
    write_images = "pretty" if args.plotseq else False
    write_images = "debug" if args.debug else write_images
    debug = args.debug

    import redis
    r = redis.Redis()

    main(checkpoint_file, args.uuid, r, args.out_name,
         write_images, debug)
