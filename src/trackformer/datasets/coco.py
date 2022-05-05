# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
"""
COCO dataset which returns image_id for evaluation.

Mostly copy-paste from https://github.com/pytorch/vision/blob/13b35ff/references/detection/coco_utils.py
"""
from . import transforms as T


def make_coco_transforms(image_set, img_transform=None):
    normalize = T.Compose([
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    # default
    max_size = 1333
    val_width = 800
    print(f"img_transform: {img_transform}")

    if img_transform is not None:
        scale = img_transform.max_size / max_size
        max_size = img_transform.max_size
        val_width = img_transform.val_width

    transforms = [
        T.RandomResize([val_width], max_size=max_size),
    ]

    return T.Compose(transforms), normalize

