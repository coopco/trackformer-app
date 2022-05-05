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



def rand_cmap(nlabels, type='bright', first_color_black=True, last_color_black=False, verbose=False):
    """
    Creates a random colormap to be used together with matplotlib. Useful for segmentation tasks
    :param nlabels: Number of labels (size of colormap)
    :param type: 'bright' for strong colors, 'soft' for pastel colors
    :param first_color_black: Option to use first color as black, True or False
    :param last_color_black: Option to use last color as black, True or False
    :param verbose: Prints the number of labels and shows the colormap. True or False
    :return: colormap for matplotlib
    """
    import colorsys

    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap


    if type not in ('bright', 'soft'):
        print ('Please choose "bright" or "soft" for type')
        return

    if verbose:
        print('Number of labels: ' + str(nlabels))

    # Generate color map for bright colors, based on hsv
    if type == 'bright':
        randHSVcolors = [(np.random.uniform(low=0.0, high=1),
                          np.random.uniform(low=0.2, high=1),
                          np.random.uniform(low=0.9, high=1)) for i in range(nlabels)]

        # Convert HSV list to RGB
        randRGBcolors = []
        for HSVcolor in randHSVcolors:
            randRGBcolors.append(colorsys.hsv_to_rgb(HSVcolor[0], HSVcolor[1], HSVcolor[2]))

        if first_color_black:
            randRGBcolors[0] = [0, 0, 0]

        if last_color_black:
            randRGBcolors[-1] = [0, 0, 0]

        random_colormap = LinearSegmentedColormap.from_list('new_map', randRGBcolors, N=nlabels)

    # Generate soft pastel colors, by limiting the RGB spectrum
    if type == 'soft':
        low = 0.6
        high = 0.95
        randRGBcolors = [(np.random.uniform(low=low, high=high),
                          np.random.uniform(low=low, high=high),
                          np.random.uniform(low=low, high=high)) for i in range(nlabels)]

        if first_color_black:
            randRGBcolors[0] = [0, 0, 0]

        if last_color_black:
            randRGBcolors[-1] = [0, 0, 0]
        random_colormap = LinearSegmentedColormap.from_list('new_map', randRGBcolors, N=nlabels)

    # Display colorbar
    if verbose:
        from matplotlib import colorbar, colors
        from matplotlib import pyplot as plt
        fig, ax = plt.subplots(1, 1, figsize=(15, 0.5))

        bounds = np.linspace(0, nlabels, nlabels + 1)
        norm = colors.BoundaryNorm(bounds, nlabels)

        colorbar.ColorbarBase(ax, cmap=random_colormap, norm=norm, spacing='proportional', ticks=None,
                              boundaries=bounds, format='%1i', orientation=u'horizontal')

    return random_colormap


def plot_sequence(tracks, data_loader, output_dir, write_images, generate_attention_maps):
    """Plots a whole sequence

    Args:
        tracks (dict): The dictionary containing the track dictionaries in the form tracks[track_id][frame] = bb
        db (torch.utils.data.Dataset): The dataset with the images belonging to the tracks (e.g. MOT_Sequence object)
        output_dir (String): Directory where to save the resulting images
    """
    if not osp.exists(output_dir):
        os.makedirs(output_dir)

    # infinite color loop
    # cyl = cy('ec', COLORS)
    # loop_cy_iter = cyl()
    # styles = defaultdict(lambda: next(loop_cy_iter))

    # cmap = plt.cm.get_cmap('hsv', )
    cmap = rand_cmap(len(tracks), type='bright', first_color_black=False, last_color_black=False)

    # if generate_attention_maps:
    #     attention_maps_per_track = {
    #         track_id: (np.concatenate([t['attention_map'] for t in track.values()])
    #                    if len(track) > 1
    #                    else list(track.values())[0]['attention_map'])
    #         for track_id, track in tracks.items()}
    #     attention_map_thresholds = {
    #         track_id: np.histogram(maps, bins=2)[1][1]
    #         for track_id, maps in attention_maps_per_track.items()}

        # _, attention_maps_bin_edges = np.histogram(all_attention_maps, bins=2)

    for frame_id, frame_data  in enumerate(tqdm.tqdm(data_loader)):
        f = open(os.path.join(output_dir, "../../progress.txt"), "w+")
        f.write(f"Plotting {str(frame_id+1)} {len(data_loader)}")
        f.close()

        img_path = frame_data['img_path'][0]
        img = cv2.imread(img_path)[:, :, (2, 1, 0)]
        height, width, _ = img.shape

        fig = plt.figure()
        fig.set_size_inches(width / 96, height / 96)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        ax.imshow(img)

        if generate_attention_maps:
            attention_map_img = np.zeros((height, width, 4))

        for track_id, track_data in tracks.items():
            if frame_id in track_data.keys():
                bbox = track_data[frame_id]['bbox']

                if 'mask' in track_data[frame_id]:
                    mask = track_data[frame_id]['mask']
                    mask = np.ma.masked_where(mask == 0.0, mask)

                    ax.imshow(mask, alpha=0.5, cmap=colors.ListedColormap([cmap(track_id)]))

                    annotate_color = 'white'
                else:
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

                if 'attention_map' in track_data[frame_id]:
                    attention_map = track_data[frame_id]['attention_map']
                    attention_map = cv2.resize(attention_map, (width, height))

                    # attention_map_img = np.ones((height, width, 4)) * cmap(track_id)
                    # # max value will be at 0.75 transparency
                    # attention_map_img[:, :, 3] = attention_map * 0.75 / attention_map.max()

                    # _, bin_edges = np.histogram(attention_map, bins=2)
                    # attention_map_img[:, :][attention_map < bin_edges[1]] = 0.0

                    # attention_map_img += attention_map_img

                    # _, bin_edges = np.histogram(attention_map, bins=2)

                    norm_attention_map = attention_map / attention_map.max()

                    high_att_mask = norm_attention_map > 0.25 # bin_edges[1]
                    attention_map_img[:, :][high_att_mask] = cmap(track_id)
                    attention_map_img[:, :, 3][high_att_mask] = norm_attention_map[high_att_mask] * 0.5

                    # attention_map_img[:, :] += (np.tile(attention_map[..., np.newaxis], (1,1,4)) / attention_map.max()) * cmap(track_id)
                    # attention_map_img[:, :, 3] = 0.75

        if generate_attention_maps:
            ax.imshow(attention_map_img, vmin=0.0, vmax=1.0)

        plt.axis('off')
        # plt.tight_layout()
        plt.draw()
        plt.savefig(osp.join(output_dir, osp.basename(img_path)), dpi=96)
        plt.close()


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

