import os
import pickle

import numpy as np
import pandas as pd
from scipy.spatial import distance
from sklearn.cluster import DBSCAN
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt

import time

from sklearn.preprocessing import MinMaxScaler
from sklearn.utils.multiclass import unique_labels

from Learn.data_in import idp_preprocess, flatten, idp_preprocess_legacy
from utils.transformation import translate, sphere_search, rotateZ, rotateY, rotateX, scale

volume_shape = [25, 25, 25]


def prepare_x(data_stream, window_size, stride=1):
    x = []
    for i in range(0, len(data_stream) - window_size, stride):
        # print('creating sample ' + str(i) + ' of ' + str((len(data_stream) - window_size) / stride))
        input_ = data_stream[i:i + window_size]
        x.append(np.expand_dims(input_, axis=-1))
    return np.array(x)


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


def split(word):
    return [char for char in word]


def load_idp(data_directory, sensor_feature_dict, complete_class, encoder, sensor_sample_points_dict,
             input_interval=4.0):
    '''
    load everything in the given path
    :return:
    '''
    Y = []
    X_dict = dict()
    data_suffix = '_data.mgesf'
    label_suffix = '_label.mgesf'
    feature_names = flatten(list(sensor_feature_dict.values()))
    labeled_sample_dict = dict([(char, dict([(ftn, []) for ftn in feature_names])) for char in complete_class])
    for fn in os.listdir(data_directory):
        if fn.endswith(data_suffix):
            data_path = os.path.join(data_directory, fn)
            label_path = os.path.join(data_directory, fn.replace(data_suffix, '') + label_suffix)
            subject_name = fn.split('_')[-2]
            data = pickle.load(open(data_path, 'rb'))
            label = pickle.load(open(label_path, 'rb'))
            labeled_sample_dict = idp_preprocess(data, char_set=label, input_interval=input_interval,
                                                 sensor_sample_points_dict=sensor_sample_points_dict,
                                                 sensor_features_dict=sensor_feature_dict,
                                                 labeled_sample_dict=labeled_sample_dict)
    # add to x and y
    for char, feature_samples in labeled_sample_dict.items():
        if len(flatten(feature_samples.values())) > 0:
            for ft_name, ft_samples in feature_samples.items():
                if ft_name in X_dict:
                    X_dict[ft_name] = np.concatenate([X_dict[ft_name], np.array(ft_samples)])
                else:
                    X_dict[ft_name] = np.array(ft_samples)
            Y += [char] * len(ft_samples)
    return X_dict, encoder.transform(np.reshape(Y, (-1, 1))).toarray()


def load_idp_new_and_legacy(data_directory, sensor_feature_dict, complete_class, encoder, sensor_sample_points_dict,
                            input_interval=4.0, legacy_root=None):
    '''
    load everything in the given path
    :return:
    '''
    Y = []
    X_dict = dict()
    data_suffix = '_data.mgesf'
    label_suffix = '_label.mgesf'
    feature_names = flatten(list(sensor_feature_dict.values()))
    labeled_sample_dict = dict([(char, dict([(ftn, []) for ftn in feature_names])) for char in complete_class])
    for i, fn in enumerate(os.listdir(data_directory)):
        print('loading file ' + str(i) + ' of ' + str(len(os.listdir(data_directory))) + ', file name is ' + fn)
        if fn.endswith(data_suffix):
            data_path = os.path.join(data_directory, fn)
            label_path = os.path.join(data_directory, fn.replace(data_suffix, '') + label_suffix)
            subject_name = fn.split('_')[-2]
            data = pickle.load(open(data_path, 'rb'))
            label = pickle.load(open(label_path, 'rb'))
            labeled_sample_dict = idp_preprocess(data, char_set=label, input_interval=input_interval,
                                                 sensor_sample_points_dict=sensor_sample_points_dict,
                                                 sensor_features_dict=sensor_feature_dict,
                                                 labeled_sample_dict=labeled_sample_dict, channel_mode='channels_first')
    # add to x and y
    for char, feature_samples in labeled_sample_dict.items():
        if len(flatten(feature_samples.values())) > 0:
            for ft_name, ft_samples in feature_samples.items():
                if ft_name in X_dict:
                    X_dict[ft_name] = np.concatenate([X_dict[ft_name], np.array(ft_samples)])
                else:
                    X_dict[ft_name] = np.array(ft_samples)
            Y += [char] * len(ft_samples)

    X_mmw_rD = X_dict['range_doppler']
    X_mmw_rA = X_dict['range_azi']

    if legacy_root is not None:
        print('loading legacy zl data')
        X_mmw_rD_legacy, X_mmw_rA_legacy, Y_legacy = idp_legacy_xy(legacy_root)
        X_mmw_rD = np.concatenate((X_mmw_rD, X_mmw_rD_legacy))
        X_mmw_rA = np.concatenate((X_mmw_rA, X_mmw_rA_legacy))
        Y = Y + Y_legacy
    return X_mmw_rD, X_mmw_rA, encoder.transform(np.reshape(Y, (-1, 1))).toarray()


def idp_legacy_xy(legacy_root):
    idp_data_dir = ['idp-ABCDE-rpt10',
                    'idp-ABCDE-rpt2',
                    'idp-FGHIJ-rpt10',
                    'idp-KLMNO-rpt10',
                    'idp-PQRST-rpt10',
                    'idp-UVWXY-rpt10',
                    'idp-ZSpcBspcEnt-rpt10'
                    ]
    idp_data_dir = [os.path.join(legacy_root, x) for x in idp_data_dir]
    num_repeats = [10, 2,
                   10, 10, 10, 10, 10
                   ]
    sample_classes = [['A', 'B', 'C', 'D', 'E'],
                      ['A', 'B', 'C', 'D', 'E'],  # some of the ABCDE data are repeated twice
                      ['F', 'G', 'H', 'I', 'J'],
                      ['K', 'L', 'M', 'N', 'O'],
                      ['P', 'Q', 'R', 'S', 'T'],
                      ['U', 'V', 'W', 'X', 'Y'],
                      ['Z', 'Spc', 'Bspc', 'Ent']
                      ]
    classes = ['A', 'B', 'C', 'D', 'E',
               'F', 'G', 'H', 'I', 'J',
               'K', 'L', 'M', 'N', 'O',
               'P', 'Q', 'R', 'S', 'T',
               'U', 'V', 'W', 'X', 'Y',
               'Z', 'Spc', 'Bspc', 'Ent'
               ]

    assert len(idp_data_dir) == len(num_repeats) == len(sample_classes)  # check the consistency of zip variables
    assert set(classes) == set(
        [item for sublist in sample_classes for item in sublist])  # check categorical consistency

    interval_duration = 4.0  # how long does one writing take
    period = 33.45  # ms

    # classes = set([item for sublist in sample_classes for item in sublist])  # reduce to categorical classes
    ls_dicts = \
        [idp_preprocess_legacy(dr, interval_duration, classes=cs, num_repeat=nr, period=period)
         for dr, nr, cs in zip(idp_data_dir, num_repeats, sample_classes)]

    Y = []
    X_mmw_rD = []
    X_mmw_rA = []

    # add to x and y
    for lsd in ls_dicts:
        for key, value in lsd.items():
            X_mmw_rD += [d for d in value['mmw']['range_doppler']]
            X_mmw_rA += [a for a in value['mmw']['range_azi']]
            Y += [key for i in range(value['mmw']['range_doppler'].shape[0])]
            pass

    X_mmw_rD = np.asarray(X_mmw_rD)
    X_mmw_rA = np.asarray(X_mmw_rA)

    return X_mmw_rD, X_mmw_rA, Y


def plot_confusion_matrix(y_true, y_pred, classes,
                          normalize=False,
                          title=None,
                          cmap=plt.cm.Blues, axis_font_size=12):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if not title:
        if normalize:
            title = 'Normalized confusion matrix'
        else:
            title = 'Confusion matrix, without normalization'

    # Compute confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    # Only use the labels that appear in the data
    classes = classes[unique_labels(y_true, y_pred)]
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)
    plt.rcParams['xtick.labelsize'] = 20
    plt.rcParams['ytick.labelsize'] = 20
    plt.rcParams['axes.labelsize'] = axis_font_size
    plt.rcParams['axes.titlesize'] = axis_font_size
    fig, ax = plt.subplots()
    fig.set_size_inches(15, 15)
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    ax.figure.colorbar(im, ax=ax)
    # We want to show all ticks...
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           # ... and label them with the respective list entries
           xticklabels=classes, yticklabels=classes,
           title=title,
           ylabel='True label',
           xlabel='Predicted label')

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    fmt = '.2f' if normalize else 'd'
    fmt_0 = '.0f'
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], fmt if cm[i, j] else fmt_0),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    return ax


DBSCAN_esp = 0.2
DBSCAN_minSamples = 3


def produce_voxel(points, isCluster=True, isClipping=False):
    """

    :param frame: np a with input shape (n, 4)
    :return voxel
    """

    if len(points) == 0:  # if there's no detected points
        return np.zeros(tuple([1] + volume_shape))

    points_new = np.asarray([x for x in points if 1.0 > x[3] > -1.0])
    if not np.all(points_new == points):
        print('Warning: point VELOCITY out of bound')
    points = points_new

    if isCluster:
        # take off the doppler for clustering
        doppler_col = np.copy(points[:, 3])
        points[:, 3] = np.zeros(points[:, 3].shape)
        db = DBSCAN(eps=DBSCAN_esp, min_samples=DBSCAN_minSamples).fit(points)
        # append back the doppler
        points[:, 3] = doppler_col

        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        labels = db.labels_

        unique_labels = set(labels)
        clusters = []
        for k in zip(unique_labels):
            if k == -1:
                # Black used for noise.
                col = [0, 0, 0, 1]
            class_member_mask = (labels == k)
            xyz = points[class_member_mask & core_samples_mask]
            if xyz.any():  # in case there are none objects
                clusters.append(xyz)  # append this cluster data to the cluster list
            # each cluster is a 3 * n matrix
            xyz = points[class_member_mask & ~core_samples_mask]

        clusters.sort(key=lambda xyz: distance.euclidean((0.0, 0.0, 0.0), np.array(
            [np.mean(xyz[:, 0]), np.mean(xyz[:, 1]), np.mean(xyz[:, 2])])))

        #############################
        hand_cluster = []
        if len(clusters) > 0:
            hand_cluster = clusters[0]

    else:
        hand_cluster = points

    hand_cluster = np.array(hand_cluster)
    frame_3D_volume = snapPointsToVolume(hand_cluster, volume_shape, isClipping=isClipping)

    return np.expand_dims(frame_3D_volume, axis=0)


xmin, xmax = -0.255, 0.255
ymin, ymax = 0.0, 0.255
zmin, zmax = -0.255, 0.255

heatMin, heatMax = -1.0, 1.0
xyzScaler = MinMaxScaler().fit(np.array([[xmin, ymin, zmin],
                                         [xmax, ymax, zmax]]))
heatScaler = MinMaxScaler().fit(np.array([[heatMin],
                                          [heatMax]]))


def snapPointsToVolume(points, volume_shape, isClipping=False, radius=3, decay=0.8):
    """
    make sure volume is a square
    :param points: n * 4 a
    :param heat: scale 0 to 1
    :param volume:
    """
    assert len(volume_shape) == 3 and volume_shape[0] == volume_shape[1] == volume_shape[2]
    volume = np.zeros(volume_shape)

    if len(points) != 0:

        # filter out points that are outside the bounding box
        # using ABSOLUTE normalization

        points[:, :3] = xyzScaler.transform(points[:, :3])
        points[:, 3:] = heatScaler.transform(points[:, 3:])

        size = volume_shape[0]  # the length of the square side
        axis = np.array((size - 1) * points[:, :3], dtype=int)  # size minus 1 for index starts at 0

        for i, row in enumerate(points):
            heat = row[3]

            try:
                volume[axis[i][0], axis[i][1], axis[i][2]] = volume[axis[i][0], axis[i][1], axis[i][2]] + heat
            except IndexError:
                print(
                    'Index Out of Bound!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            if isClipping:
                point_to_clip = sphere_search(shape=volume_shape, index=(axis[i][0], axis[i][1], axis[i][2]), r=radius)
                for dist, ptc in point_to_clip:
                    if dist != 0.0:
                        factor = (radius - dist + 1) * decay / radius
                        volume[ptc[0], ptc[1], ptc[2]] = volume[ptc[0], ptc[1], ptc[2]] + heat * factor

    volume_mean = np.mean(volume)
    assert volume_mean < 0.1
    assert volume_mean > -0.1

    return volume


# frameArray = np.load('F:/test_frameArray.npy')
# start = time.time()
# result = preprocess_frame(frameArray[2])
# end = time.time()
# print('Preprocessing frame took ' + str(end-start))

def merge_dict(dicts: list):
    merged_dict = dict()
    merged_len = 0
    for d in dicts:
        merged_len += len(d)
        merged_dict = {**merged_dict, **d}

    # make sure there is no replacement of elements
    try:
        assert merged_len == len(merged_dict)
    except AssertionError as ae:
        print(str(ae))
        raise Exception('dict item replaced!')
    return merged_dict


class StreamingMovingAverage:
    def __init__(self, window_size):
        self.window_size = window_size
        self.values = []
        self.sum = 0

    def process(self, value):
        self.values.append(value)
        self.sum += value
        if len(self.values) > self.window_size:
            self.sum -= self.values.pop(0)
        return float(self.sum) + value / len(self.values)


def parse_deltalize_recording(file: str) -> dict:
    recording_list = list()
    xyz_array = list()
    lines = list()
    with open(file) as fp:  # first buffer all the lines so that the buffered lines supports indexing
        for l in fp:
            lines.append(l)

    for i, buffered_l in enumerate(lines):
        timestamp, x, y, z = [float(x) for x in buffered_l.split(',')]

        if i == 0:  # if this is the first frame
            x, y, z = 0, 0, 0
        else:
            # process delta
            prev_x, prev_y, prev_z = [float(x) for x in lines[i - 1].split(',')][1:]
            x, y, z = x - prev_x, y - prev_y, z - prev_z

        xyz_array.append([x, y, z])
        recording_list.append([timestamp, (x, y, z)])

    assert len(xyz_array) == len(recording_list)
    return dict(recording_list), np.asarray(xyz_array)


def linear_process(a: float, b: float, x: float):
    return x * a + b


class Queue:
    def __init__(self, maxlen):
        self.data = list()
        self.maxlen = maxlen

    def __getitem__(self, key):
        # It's probably better to catch any IndexError to at least provide
        # a class-specific exception
        return self.data[key]

    def get_list(self):
        return self.data

    def __len__(self):
        return len(self.data)

    def push_right(self, d):
        self.data = self.data[-self.maxlen + 1:] + [d]

    def pop_right(self):
        if len(self.data) > 0:
            temp = self.data[-1]
            self.data = self.data[:-1]
            return temp
        else:
            return None


rd_max, rd_min = 1500, -1500


def scale_rd_spectrogram(spectrogram):
    return 255 * (spectrogram - rd_min) / (rd_max - rd_min)


def clutter_removal(cur_frame, clutter, signal_clutter_ratio):
    if clutter is None:
        clutter = cur_frame
    else:
        clutter = signal_clutter_ratio * clutter + (1 - signal_clutter_ratio) * cur_frame
    return cur_frame - clutter, clutter


def index_to_class(index, encoder):
    rtn = [0.0] * len(encoder.categories_[0])
    rtn[index] = 1.0
    rtn = encoder.inverse_transform([rtn])
    return rtn[0][0]


def edit_distance(string1, string2):
    """Ref: https://bit.ly/2Pf4a6Z"""

    if len(string1) > len(string2):
        difference = len(string1) - len(string2)
        string1[:difference]

    elif len(string2) > len(string1):
        difference = len(string2) - len(string1)
        string2[:difference]

    else:
        difference = 0

    for i in range(len(string1)):
        if string1[i] != string2[i]:
            difference += 1

    return difference



def levenshtein_ratio_and_distance(s, t, ratio_calc = False):
    """ levenshtein_ratio_and_distance:
        Calculates levenshtein distance between two strings.
        If ratio_calc = True, the function computes the
        levenshtein distance ratio of similarity between two strings
        For all i and j, distance[i,j] will contain the Levenshtein
        distance between the first i characters of s and the
        first j characters of t
    """
    # Initialize matrix of zeros
    rows = len(s)+1
    cols = len(t)+1
    distance = np.zeros((rows,cols),dtype = int)

    # Populate matrix of zeros with the indeces of each character of both strings
    for i in range(1, rows):
        for k in range(1,cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row-1] == t[col-1]:
                cost = 0 # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
            else:
                # In order to align the results with those of the Python Levenshtein package, if we choose to calculate the ratio
                # the cost of a substitution is 2. If we calculate just distance, then the cost of a substitution is 1.
                if ratio_calc == True:
                    cost = 2
                else:
                    cost = 1
            distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
                                 distance[row][col-1] + 1,          # Cost of insertions
                                 distance[row-1][col-1] + cost)     # Cost of substitutions
    if ratio_calc == True:
        # Computation of the Levenshtein Distance Ratio
        Ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
        return Ratio
    else:
        # print(distance) # Uncomment if you want to see the matrix showing how the algorithm computes the cost of deletions,
        # insertions and/or substitutions
        # This is the minimum number of edits needed to convert string a to string b
        return "The strings are {} edits away".format(distance[row][col])