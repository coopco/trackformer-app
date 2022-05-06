import os
import time
from os import path as osp
from argparse import ArgumentParser

from trackformer import Trackformer
from util import video_to_frames, frames_to_video

def main(checkpoint_file, data_root_dir, output_dir,
         write_images="pretty", debug=False):
    if output_dir is not None:
        if not osp.exists(output_dir):
            os.makedirs(output_dir)

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
        with open(osp.join(output_dir, "progress.txt"), "w+") as file:
            string = f"Tracking {str(frame_id+1)} {len(tracker.data_loader)}"
            print(string)
            file.write(string)

    results = tracker.results()
    time_total = time.time() - start

    print(f"RUNTIME: {time.time() - start :.2f} s")

    #   Write results
    if output_dir is not None:
        tracker.write_results(results, output_dir)

        if write_images:
            out_path = osp.join(output_dir, "plots")
            tracker.plot_seq(results, out_path, write_images)
            frames_to_video(out_path, osp.join(output_dir, "out.mp4"))

    with open(osp.join(output_dir, "progress.txt"), "w+") as file:
        print("COMPLETE")
        file.write(f"COMPLETE")


if __name__=="__main__":
    parser = ArgumentParser()
    parser.add_argument("-u", "--uuid", dest="uuid", default="../test_track")
    parser.add_argument("--plotseq", action='store_true', dest="plotseq")
    parser.add_argument("--debug", action='store_true', dest="debug") #TODO for plot_seq
    parser.add_argument("-m", "--model-file", dest="model_file",
                        default="models/ant_finetune/checkpoint.pth")

    args = parser.parse_args()

    checkpoint_file = args.model_file
    output_dir = osp.join("uploads", args.uuid)
    data_root_dir = output_dir
    write_images = "pretty" if args.plotseq else False
    write_images = "debug" if args.plotseq else write_images
    debug = args.debug

    main(checkpoint_file, data_root_dir, output_dir, write_images, debug)
