# -*- coding: utf-8 -*-

import json
import pandas as pd
import numpy as np
from itertools import islice


def read_opensignals(path, channel, channeltype):

    # Prepare output.
    output = {"status": False,
              "sec": None,
              "signal": None,
              "sfreq": None,
              "rpathsignal": None}

    with open(path, "r") as f:

        # Read first line and check if user provided an OpenSignals
        # file. Note that the file is closed automatically once the "with"
        # block is exited.
        if "OpenSignals" not in f.readline():
            output["status"] = "Error: Text file is not in OpenSignals format."
            return output

        # Read second line and convert json header to dict (only select first
        # device / MAC adress).
        metadata = json.loads(f.readline()[1:])

    metadata = metadata[list(metadata.keys())[0]]
    # Parse header and extract relevant metadata.
    sfreq = metadata["sampling rate"]
    channels = metadata["channels"]

    if channel[0] == "A":
        # Search the index of the requested channel.
        chanidx = [i for i, s in enumerate(channels) if int(channel[1]) == s]

        if not chanidx:
            output["status"] = f"Error: {channeltype.capitalize()} channel not found."
            return output

        # Select only first sensor of the selected modality (it is possible
        # that multiple sensors of the same kind have been recorded).
        chanidx = chanidx[0]
        # Since analog channels start in column 5 (zero based), add 5 to sensor
        # index to obtain signal from selected modality.
        chanidx += 5

    elif channel[0] == "I":
        chanidx = int(channel[1])

    # Load data with pandas for performance.
    signal = pd.read_csv(path, delimiter='\t', usecols=[chanidx], header=None,
                         comment='#')
    signallen = signal.size
    sec = np.linspace(0, signallen / sfreq, signallen)

    if channeltype == "signal":
        output["rpathsignal"] = path
        output["sec"] = sec
        output["signal"] = np.ravel(signal)
        output["sfreq"] = sfreq

    elif channeltype == "marker":
        output["signal"] = np.ravel(signal)

    return output


def write_opensignals(rpath, wpath, segment=None):

    # Get the header.
    header = []
    with open(rpath, 'rt') as oldfile:
        for line in islice(oldfile, 3):
            header.append(line)
    # Get the data.
    data = pd.read_csv(rpath, delimiter='\t', header=None, comment='#')
    # If the signal has been segmented apply segmentation to all channels.
    if segment is not None:
        data = data.iloc[segment[0]:segment[1], :]

    # Write header and (segmented) data to the new file.
    with open(wpath, 'w', newline='') as newfile:
        for line in header:
            newfile.write(line)
        data.to_csv(newfile, sep='\t', header=False, index=False)


def read_edf(path):
    with open(path, 'rb') as f:
        return f.readline(256).strip().decode()


def write_edf(rpath, wpath, segment=None):
    pass
