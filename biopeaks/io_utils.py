# -*- coding: utf-8 -*-

import json
import pandas as pd
import numpy as np
from itertools import islice
from struct import unpack


def read_opensignals(path, channel, channeltype):

    # Prepare output.
    output = {"status": False,
              "sec": None,
              "signal": None,
              "sfreq": None}

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


def read_edf(path, channel, channeltype):
    """
    Have a look at the EDF publication (Kemp et al. 1992) for a specification
    of header fields etc..
    Very helpful testfiles are hosted here:
        https://www.teuniz.net/edf_bdf_testfiles/
    """

    # Prepare output.
    output = {"status": False,
              "sec": None,
              "signal": None,
              "sfreq": None}

    chanidx = int(channel[1])

    with open(path, 'rb') as f:

        # Use seek to skip ahead to the interesting bytes.
        f.seek(184)
        end_header = int(f.read(8).strip().decode())
        # print(f"number of bytes in header: {end_header}")
        f.seek(236)
        n_epochs = int(f.read(8).strip().decode())
        # print(f"number of epochs: {n_epochs}")
        duration_epoch = float(f.read(8).strip().decode())
        # print(f"epoch duration: {duration_epoch}")
        n_channels = int(f.read(4).strip().decode())
        # print(f"number of channels: {n_channels}")

        if n_channels < chanidx:    # both indices are one-based
            output["status"] = f"Error: {channeltype.capitalize()} channel not found."
            return output

        # Get the number of samples channel per epoch.
        f.seek(256 + (n_channels * 216))
        n_samples = [int(f.read(8).strip().decode()) for i in range(n_channels)]
        # print(f"each epoch contains {n_samples} samples per channel")

        # Infer the sampling rate.
        chansfreq = int(np.rint(n_samples[chanidx - 1] / duration_epoch))

        # Skip to the start of the data records.
        f.seek(end_header)

        # Read all the data.
        signal = np.fromfile(f, dtype=np.int16)    # one sample is encoded as two-byte integer (16 bits)

    signallen = signal.size

    # Take care of improperly specified number of epochs.
    if n_epochs == -1:
        n_epochs = int(np.rint(signallen / sum(n_samples)))

    assert signallen == sum(n_samples) * n_epochs

    chansignallen = n_epochs * n_samples[chanidx - 1]

    sec = np.linspace(0, chansignallen / chansfreq, chansignallen)

    # Select the data belonging to the requested channel.
    channel_offset = np.cumsum(n_samples)[chanidx - 1] - n_samples[chanidx - 1]
    channel_stride = sum(n_samples)
    chansignal = []
    for i in np.arange(channel_offset, signallen, channel_stride):
        chansignal.append(signal[i:i + n_samples[chanidx - 1]])

    if channeltype == "signal":
        output["sec"] = sec
        output["signal"] = np.ravel(chansignal)
        output["sfreq"] = chansfreq

    elif channeltype == "marker":
        output["signal"] = np.ravel(chansignal)

    return output


def write_edf(rpath, wpath, segment=None):
    pass
