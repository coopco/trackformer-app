# Plot sequence

#########################################
# Still ugly file with helper functions #
#########################################

import os
from collections import defaultdict
from os import path as osp

import cv2
import matplotlib
import matplotlib.pyplot as plt
import motmetrics as mm
import numpy as np
import torch
import torchvision.transforms.functional as F
import tqdm
from cycler import cycler as cy
from matplotlib import colors
from scipy.interpolate import interp1d

matplotlib.use('Agg')

def video_to_frames(filename, output_dir):
    # TODO Error handling
    vidcap = cv2.VideoCapture(filename)
    success, image = vidcap.read()

    count = 0
    while success:
        cv2.imwrite(os.path.join(output_dir, f"{count:06d}.jpg"), image)
        success, image = vidcap.read()
        count += 1

# TODO Copy settings from original video
def frames_to_video(input_dir, output_file):
    images = sorted([img for img in os.listdir(input_dir) if img.endswith(".jpg")])
    print(images)
    frame = cv2.imread(os.path.join(input_dir, images[0]))
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_file, fourcc, 15, (width, height))

    for image in images:
        video.write(cv2.imread(os.path.join(input_dir, image)))

    cv2.destroyAllWindows()
    video.release()



# Borrowed from trackformer code
def rand_cmap(nlabels, type='bright'):
    """
    Creates a random colormap to be used together with matplotlib. Useful for segmentation tasks
    :param nlabels: Number of labels (size of colormap)
    :param type: 'bright' for strong colors, 'soft' for pastel colors
    :return: colormap for matplotlib
    """
    import colorsys

    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap


    if type not in ('bright', 'soft'):
        print ('Please choose "bright" or "soft" for type')
        return

    # Generate color map for bright colors, based on hsv
    if type == 'bright':
        randHSVcolors = [(np.random.uniform(low=0.0, high=1),
                          np.random.uniform(low=0.2, high=1),
                          np.random.uniform(low=0.9, high=1)) for i in range(nlabels)]

        # Convert HSV list to RGB
        randRGBcolors = []
        for HSVcolor in randHSVcolors:
            randRGBcolors.append(colorsys.hsv_to_rgb(HSVcolor[0], HSVcolor[1], HSVcolor[2]))

        random_colormap = LinearSegmentedColormap.from_list('new_map', randRGBcolors, N=nlabels)

    # Generate soft pastel colors, by limiting the RGB spectrum
    if type == 'soft':
        low = 0.6
        high = 0.95
        randRGBcolors = [(np.random.uniform(low=low, high=high),
                          np.random.uniform(low=low, high=high),
                          np.random.uniform(low=low, high=high)) for i in range(nlabels)]

        random_colormap = LinearSegmentedColormap.from_list('new_map', randRGBcolors, N=nlabels)

    return random_colormap


# Borrowed from trackformer code
def plot_sequence(tracks, data_loader, output_dir, write_images):
    """Plots a whole sequence

    Args:
        tracks (dict): The dictionary containing the track dictionaries in the form tracks[track_id][frame] = bb
        db (torch.utils.data.Dataset): The dataset with the images belonging to the tracks (e.g. MOT_Sequence object)
        output_dir (String): Directory where to save the resulting images
    """
    if not osp.exists(output_dir):
        os.makedirs(output_dir)

    cmap = rand_cmap(len(tracks), type='bright')

    for frame_id, frame_data  in enumerate(data_loader):
        with open(osp.join(output_dir, "../", "progress.txt"), "w+") as file:
            string = f"Plotting {str(frame_id+1)} {len(data_loader)}"
            print(string)
            file.write(string)

        img_path = frame_data['img_path'][0]
        img = cv2.imread(img_path)[:, :, (2, 1, 0)]
        height, width, _ = img.shape

        fig = plt.figure()
        fig.set_size_inches(width / 96, height / 96)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        ax.imshow(img)

        for track_id, track_data in tracks.items():
            if frame_id in track_data.keys():
                bbox = track_data[frame_id]['bbox']

                ax.add_patch(
                    plt.Rectangle(
                        (bbox[0], bbox[1]),
                        bbox[2] - bbox[0],
                        bbox[3] - bbox[1],
                        fill=False,
                        linewidth=2.0,
                        color=cmap(track_id),
                    ))

                annotate_color = cmap(track_id)

                if write_images == 'debug':
                    ax.annotate(
                        f"{track_id} ({track_data[frame_id]['score']:.2f})",
                        (bbox[0] + (bbox[2] - bbox[0]) / 2.0, bbox[1] + (bbox[3] - bbox[1]) / 2.0),
                        color=annotate_color, weight='bold', fontsize=12, ha='center', va='center')


        plt.axis('off')
        plt.draw()
        plt.savefig(osp.join(output_dir, osp.basename(img_path)), dpi=96)
        plt.close()


# Borrowed from trackformer code
def interpolate_tracks(tracks):
    for i, track in tracks.items():
        frames = []
        x0 = []
        y0 = []
        x1 = []
        y1 = []

        for f, data in track.items():
            frames.append(f)
            x0.append(data['bbox'][0])
            y0.append(data['bbox'][1])
            x1.append(data['bbox'][2])
            y1.append(data['bbox'][3])

        if frames:
            x0_inter = interp1d(frames, x0)
            y0_inter = interp1d(frames, y0)
            x1_inter = interp1d(frames, x1)
            y1_inter = interp1d(frames, y1)

            for f in range(min(frames), max(frames) + 1):
                bbox = np.array([
                    x0_inter(f),
                    y0_inter(f),
                    x1_inter(f),
                    y1_inter(f)])
                tracks[i][f]['bbox'] = bbox
        else:
            tracks[i][frames[0]]['bbox'] = np.array([
                x0[0], y0[0], x1[0], y1[0]])

    return interpolated

