import pickle
import os
from copy import copy, deepcopy

from utils.data_utils import clutter_removal

input_dir = 'D:\PcProjects\mGesf\data\data_ev1\hw_no_cr_ABCDEGHIJ'
output_dir = 'D:\PcProjects\mGesf\data\data_ev1\hw_cr_ABCDEFGHIJ'

data_suffix = '_data.mgesf'
label_suffix = '_label.mgesf'

rd_clutter = None
ra_clutter = None
rd_signal_clutter_ratio = 0.5
ra_signal_clutter_ratio = 0.5

for i, fn in enumerate(os.listdir(input_dir)):
    print('processing files: ' + str(input_dir))
    if fn.endswith(data_suffix):
        data_path = os.path.join(input_dir, fn)
        label_path = os.path.join(input_dir, fn.replace(data_suffix, '') + label_suffix)
        subject_name = fn.split('_')[-2]
        data = pickle.load(open(data_path, 'rb'))
        label = pickle.load(open(label_path, 'rb'))

        data_RC = deepcopy(data)

        data_mmw_rd_RC = []
        for mmw_rd_frame in data['mmw']['range_doppler']:
            mmw_rd_frame_RC, rd_clutter = clutter_removal(cur_frame=mmw_rd_frame, clutter=rd_clutter, signal_clutter_ratio=rd_signal_clutter_ratio)
            data_mmw_rd_RC.append(mmw_rd_frame_RC)


        data_mmw_ra_RC = []
        for mmw_ra_frame in data['mmw']['range_azi']:
            mmw_ra_frame_RC, ra_clutter = clutter_removal(cur_frame=mmw_ra_frame, clutter=ra_clutter, signal_clutter_ratio=ra_signal_clutter_ratio)
            data_mmw_ra_RC.append(mmw_ra_frame_RC)

        data_RC['mmw']['range_doppler'] = data_mmw_rd_RC
        data_RC['mmw']['range_azi'] = data_mmw_ra_RC

        print(data_RC['mmw']['range_doppler'][0])
        print(data_RC['mmw']['range_azi'][0])

        pickle.dump(data_RC, open(os.path.join(output_dir, fn), 'wb'))
        pickle.dump(label, open(os.path.join(output_dir, fn.replace(data_suffix, '') + label_suffix), 'wb'))