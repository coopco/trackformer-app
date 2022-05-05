# Class that exports some object that allows app to call object.step()
# With optional config options (that are defined by this file)

import os
import sys
import time
from os import path as osp

import torch
import yaml
from torch.utils.data import DataLoader

from src.trackformer.models import build_model
from src.trackformer.models.tracker import Tracker
from src.trackformer.util.misc import nested_dict_to_namespace
from src.trackformer.util.track_utils_simple import interpolate_tracks, plot_sequence

from src.trackformer.datasets.tracking.demo_sequence import DemoSequence

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
        pass

    def build_dataset(self, data_root_dir):
        # Extract frames from video (util file?)
        # Get transforms
        # Build Demo dataset
        self.dataset = TrackDatasetFactory(
            "DEMO", root_dir=data_root_dir, img_transform=self.img_transform)
        seq = self.dataset[0]
        self.data_loader = DataLoader(seq)

    def build_model(self, checkpoint_file, tracker_cfg):
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
            obj_detector, obj_detector_post, tracker_cfg,
            False, track_logger)

        self.tracker = tracker
        self.img_transform = img_transform

    def step(self, frame_data):
        with torch.no_grad():
            self.tracker.step(frame_data)

    def reset(self):
        self.tracker.reset()

    def plot_seq(self, results, output_dir, options):
        plot_sequence(results, self.data_loader, output_dir,
            options, False)

    def results(self, interpolate=False):
        results = self.tracker.get_results()
        if interpolate:
            results = interpolate_tracks(results)

        return results

    def write_results(self, results, output_dir):
        self.dataset[0].write_results(results, output_dir)

