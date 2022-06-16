# Class that exports some object that allows app to call object.step()
# With optional config options (that are defined by this file)

import os
import sys
import time
import csv
from os import path as osp

import torch
import yaml
from torch.utils.data import DataLoader

from src.trackformer.models import build_model
from src.trackformer.models.tracker import Tracker
from src.trackformer.util.misc import nested_dict_to_namespace
from src.trackformer.datasets.tracking.demo_sequence import DemoSequence

from util import interpolate_tracks, plot_sequence, plot_frame, rand_cmap

# TODO better tracker_cfg handling
# TODO Do it without this factory code
# TODO Move this file somewhere else
DATASETS = {}

DATASETS['DEMO'] = (lambda kwargs: [DemoSequence(**kwargs), ])

class TrackDatasetFactory:
    def __init__(self, datasets, **kwargs) -> None:
        """Initialize the corresponding dataloader.

        Keyword arguments:
        datasets --  the name of the dataset or list of dataset names
        kwargs -- arguments used to call the datasets
        """
        self._data = DATASETS['DEMO'](kwargs)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, idx: int):
        return self._data[idx]

class Trackformer:
    def __init__(self):
        self.tracker_cfg = {
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

    def build_dataset(self, data_root_dir):
        # Extract frames from video (util file?)
        # Get transforms
        # Build Demo dataset
        self.dataset = TrackDatasetFactory(
            "DEMO", root_dir=data_root_dir, img_transform=self.img_transform)
        seq = self.dataset[0]
        self.data_loader = DataLoader(seq)

    def build_model(self, checkpoint_file):
        # object detection
        obj_detect_config_path = os.path.join(
            os.path.dirname(checkpoint_file),
            'config.yaml')
        obj_detect_args = nested_dict_to_namespace(yaml.unsafe_load(open(obj_detect_config_path)))
        img_transform = obj_detect_args.img_transform
        obj_detector, _, obj_detector_post = build_model(obj_detect_args)

        obj_detect_checkpoint = torch.load(
            checkpoint_file, map_location=lambda storage, loc: storage)

        obj_detect_state_dict = obj_detect_checkpoint['model']

        obj_detect_state_dict = {
            k.replace('detr.', ''): v
            for k, v in obj_detect_state_dict.items()
            if 'track_encoding' not in k}

        obj_detector.load_state_dict(obj_detect_state_dict)

        obj_detector.cuda()

        if hasattr(obj_detector, 'tracking'):
            obj_detector.tracking()

        track_logger = None
        tracker = Tracker(
            obj_detector, obj_detector_post, self.tracker_cfg,
            False, track_logger)

        self.tracker = tracker
        self.img_transform = img_transform

    def step(self, frame_data):
        with torch.no_grad():
            self.tracker.step(frame_data)

    def reset(self):
        self.tracker.reset()

    def plot_frame(self, frame_id, frame_data, results, output_dir, options, cmap):
        plot_frame(frame_id, frame_data, results, output_dir, options, cmap)

    def plot_seq(self, results, output_dir, options):
        plot_sequence(results, self.data_loader, output_dir,
            options)

    def results(self, interpolate=False):
        results = self.tracker.get_results()
        if interpolate:
            results = interpolate_tracks(results)

        return results

    def write_results(self, results, out_path):
        """Write the tracks in the format for MOT16/MOT17 sumbission

        results: dictionary with 1 dictionary for every track with
        {..., i:np.array([x1,y1,x2,y2]), ...} at key track_num

        Each file contains these lines:
        <frame>, <id>, <bb_left>, <bb_top>, <bb_width>, <bb_height>, <conf>, <x>, <y>, <z>
        """

        # format_str = "{}, -1, {}, {}, {}, {}, {}, -1, -1, -1"
        with open(out_path, "w") as r_file:
            writer = csv.writer(r_file, delimiter=',')

            for i, track in results.items():
                for frame, data in track.items():
                    x1 = data['bbox'][0]
                    y1 = data['bbox'][1]
                    x2 = data['bbox'][2]
                    y2 = data['bbox'][3]

                    writer.writerow([
                        frame + 1,
                        i + 1,
                        x1 + 1,
                        y1 + 1,
                        x2 - x1 + 1,
                        y2 - y1 + 1,
                        -1, -1, -1, -1])
