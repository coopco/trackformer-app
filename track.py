#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import os
import sys
import time
from os import path as osp
from argparse import ArgumentParser

import torch
import yaml

from trackformer import Trackformer
from util import video_to_frames, frames_to_video

def main(seed, dataset_name, obj_detect_checkpoint_file, tracker_cfg,
         write_images, output_dir, interpolate, verbose, load_results_dir,
         data_root_dir, frame_range,
         obj_detector_model=None):

    # set all seeds
    if seed is not None:
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.backends.cudnn.deterministic = True

    if output_dir is not None:
        if not osp.exists(output_dir):
            os.makedirs(output_dir)

    # Build Model
    tracker = Trackformer()
    tracker.build_model(obj_detect_checkpoint_file, tracker_cfg)
    img_transform = tracker.img_transform

    start = time.time()

    # For each video
    #   Extract frames from video
    filename = osp.join(output_dir, "in.mp4")
    video_to_frames(filename, output_dir)
    #   Build dataset
    tracker.reset()
    tracker.build_dataset(data_root_dir)

    for frame_id, frame_data in enumerate(tracker.data_loader):
        print(frame_id)
        tracker.step(frame_data)
        # TODO Write progress to file
        with open(osp.join(output_dir, "progress.txt"), "w+") as file:
            file.write(f"Tracking {str(frame_id+1)} {len(tracker.data_loader)}")

    results = tracker.results(interpolate)
    time_total = time.time() - start


    print(f"RUNTIME: {time.time() - start :.2f} s")

    #   Write results
    if output_dir is not None:
        print(f"WRITE RESULTS")
        tracker.write_results(results, output_dir)

    #   Plot results
    if output_dir is not None and write_images:
        print("PLOT SEQ")
        out_path = osp.join(output_dir, "plots")
        tracker.plot_seq(results, out_path, write_images)
        frames_to_video(out_path, osp.join(output_dir, "out.mp4"))

    with open(osp.join(output_dir, "progress.txt"), "w+") as file:
        file.write(f"COMPLETE")


if __name__=="__main__":
    parser = ArgumentParser()
    parser.add_argument("-u", "--uuid", dest="uuid")
    parser.add_argument("--plotseq", action='store_true', dest="plotseq")

    args = parser.parse_args()


    # TODO put this stuff back in config file
    seed = 666
    verbose = "false"
    load_results_dir = "null"
    dataset_name = "DEMO"
    obj_detect_checkpoint_file = "models/ant_finetune/checkpoint.pth"
    interpolate = False
    data_root_dir = "test_track"
    output_dir = "test_track"

    write_images = "pretty"

    tracker_cfg = {
        # [False, 'center_distance', 'min_iou_0_5']
        'public_detections': False,
        # score threshold for detections
        'detection_obj_score_thresh': 0.9,
        # score threshold for keeping the track alive
        'track_obj_score_thresh': 0.8,
        # NMS threshold for detection
        'detection_nms_thresh': 0.9,
        # NMS theshold while tracking
        'track_nms_thresh': 0.9,
        # motion model settings
        # How many timesteps inactive tracks are kept and cosidered for reid
        'inactive_patience': 5,
        # How similar do image and old track need to be to be considered the same person
        'reid_sim_threshold': 0.0,
        'reid_sim_only': 'false',
        'reid_score_thresh': 0.8,
        'reid_greedy_matching': 'false'
    }

    frame_range = {
        'start': 0.0,
        'end': 1.0
    }

    obj_detector_model = None

    output_dir = osp.join("uploads", args.uuid)
    data_root_dir = output_dir
    write_images = "pretty" if args.plotseq else False
    main(seed, dataset_name, obj_detect_checkpoint_file, tracker_cfg,
         write_images, output_dir, interpolate, verbose, load_results_dir,
         data_root_dir, frame_range,
         obj_detector_model)



