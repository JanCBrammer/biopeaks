# -*- coding: utf-8 -*-

import json
import pandas as pd
import numpy as np
from itertools import islice
from struct import pack
from pathlib import Path


def read_custom(rpath, customheader, channeltype):

    # Prepare output.
    output = {"error": False,
              "sec": None,
              "signal": None,
              "sfreq": None}

    if channeltype == "signal":
        chanidx = customheader["signalidx"]
    elif channeltype == "marker":
        chanidx = customheader["markeridx"]

    try:
        signal = pd.read_csv(rpath, sep=customheader["separator"],
                             usecols=[chanidx - 1], header=None,    # convert chanidx from one-based to zero-based
                             skiprows=customheader["skiprows"])
    except Exception as error:
        output["error"] = str(error)
        return output

    if signal.empty:
        output["error"] = (f"{channeltype.capitalize()}-column {chanidx} didn't"
                           " contain any data.")
        return output

    if channeltype == "signal":
        sfreq = customheader["sfreq"]
        signallen = signal.size
        sec = np.linspace(0, signallen / sfreq, signallen)
        output["sec"] = sec
        output["sfreq"] = sfreq

    output["signal"] = np.ravel(signal)

    return output


def write_custom(rpath, wpath, segment, customheader):
    """
    segment : list
    Start and end of segments in seconds.
    """
    # Get the header.
    with open(rpath, "rt") as oldfile:
        header = [line for line in islice(oldfile, customheader["skiprows"])]
    # Get the data.
    data = pd.read_csv(rpath, sep=customheader["separator"], header=None,
                       skiprows=customheader["skiprows"])
    # Apply segmentation to all channels.
    begsamp = int(np.rint(segment[0] * customheader["sfreq"]))
    endsamp = int(np.rint(segment[1] * customheader["sfreq"]))
    data = data.iloc[begsamp:endsamp, :]

    # Write header and segmented data to the new file.
    with open(wpath, "w", newline='') as newfile:
        for line in header:
            newfile.write(line)
        data.to_csv(newfile, sep=customheader["separator"], header=False,
                    index=False)


def read_opensignals(rpath, channel, channeltype):

    # Prepare output.
    output = {"error": False,
              "sec": None,
              "signal": None,
              "sfreq": None}

    with open(rpath, "r") as f:

        # Read first line and check if user provided an OpenSignals
        # file. Note that the file is closed automatically once the "with"
        # block is exited.
        if "OpenSignals" not in f.readline():
            output["error"] = "Error: Text file is not in OpenSignals format."
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
            output["error"] = f"Error: {channeltype.capitalize()} channel not found."
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
    signal = pd.read_csv(rpath, sep='\t', usecols=[chanidx], header=None,
                         comment='#')

    if channeltype == "signal":
        signallen = signal.size
        sec = np.linspace(0, signallen / sfreq, signallen)
        output["sec"] = sec
        output["sfreq"] = sfreq

    output["signal"] = np.ravel(signal)

    return output


def write_opensignals(rpath, wpath, segment, sfreq):
    """
    segment : list
    Start and end of segments in seconds.
    """
    # Get the header.
    with open(rpath, "rt") as oldfile:
        header = [line for line in islice(oldfile, 3)]
    # Get the data.
    data = pd.read_csv(rpath, sep='\t', header=None, comment='#')
    # Apply segmentation to all channels.
    begsamp = int(np.rint(segment[0] * sfreq))
    endsamp = int(np.rint(segment[1] * sfreq))
    data = data.iloc[begsamp:endsamp, :]

    # Write header and segmented data to the new file.
    with open(wpath, "w", newline='') as newfile:
        for line in header:
            newfile.write(line)
        data.to_csv(newfile, sep='\t', header=False, index=False)


def read_edf(rpath, channel, channeltype):
    """
    Have a look at the EDF publication (Kemp et al. 1992) for a specification
    of header fields etc..
    Very helpful testfiles are hosted here:
        https://www.teuniz.net/edf_bdf_testfiles/
    """
    # Prepare output.
    output = {"error": False,
              "sec": None,
              "signal": None,
              "sfreq": None}

    file_extension = Path(rpath).suffix
    if file_extension != ".edf":
        output["error"] = "Error: File is not in EDF format."
        return output

    chanidx = int(channel[1])

    with open(rpath, "rb") as f:
        info, _ = _read_edfheader(f)
        signal = _read_edfsignal(f, info["end_header"])

    if info["n_channels"] < chanidx:    # both indices are one-based
        output["error"] = f"Error: {channeltype.capitalize()} channel not found."
        return output

    # Take care of improperly specified number of epochs.
    if info["n_epochs"] == -1:
        info["n_epochs"] = int(np.rint(signal.size / sum(info["n_samples"])))

    chansfreq = info["sfreqs"][chanidx - 1]
    chansignal = _read_edfchannel(signal, info["n_samples"], chanidx)

    if channeltype == "signal":
        chansignallen = info["n_epochs"] * info["n_samples"][chanidx - 1]
        sec = np.linspace(0, chansignallen / chansfreq, chansignallen)
        output["sec"] = sec

    output["signal"] = chansignal
    output["sfreq"] = chansfreq    # important to send for both marker and signal, since they can differ in sfreq

    return output


def write_edf(rpath, wpath, segment, *args):
    """
    segment : list
    Start and end of segments in seconds.
    """
    with open(rpath, "rb") as f:
        info, header = _read_edfheader(f)
        signal = _read_edfsignal(f, info["end_header"])

    # If the segment is shorter than the original epoch duration, abort the
    # writing process.
    duration_segment = segment[1] - segment[0]
    if duration_segment < info["duration_epoch"]:
        error = f"Error: The segment is shorter than the epoch duration of " \
                f"{info['duration_epoch']} seconds in the original EDF file. " \
                f"Choose a segment longer than {info['duration_epoch']}."
        print(duration_segment, info["duration_epoch"])
        return error

    # Store the signal belonging to each channel as entry in a list.
    chansignals = [_read_edfchannel(signal, info["n_samples"], i)
                   for i in np.arange(info["n_channels"]) + 1]

    # Cut out the segment from each channel.
    for chan in range(info["n_channels"]):

        beg_segment = int(np.rint(info["sfreqs"][chan] * segment[0]))
        end_segment = int(np.rint(info["sfreqs"][chan] * segment[1]))
        chansignals[chan] = chansignals[chan][beg_segment:end_segment]

    # Update file version.
    version = info["version"] + 1
    # Update number of epochs.
    n_epochs = int(np.floor(duration_segment / info["duration_epoch"]))    # rounding off is important, otherwise fraction of incomplete epoch could be appended

    with open(wpath, "wb") as f:

        # Copy the header to the new file ...
        f.write(header)
        # ... and update the required fields:
        # Update version.
        f.seek(0)
        f.write(_padtrim(version, 8))
        # Update number of epochs.
        f.seek(236)
        f.write(_padtrim(n_epochs, 8))

        # Write the segment to the new file using the original epoch duration.
        f.seek(info["end_header"])
        for epoch in range(n_epochs):

            for chan in range(info["n_channels"]):

                beg_epoch = epoch * info["n_samples"][chan]
                end_epoch = beg_epoch + info["n_samples"][chan]
                buffer = chansignals[chan][beg_epoch:end_epoch]
                buffer = [pack('h', i) for i in buffer]    # convert to C type
                for i in buffer:
                    f.write(i)


def _read_edfheader(f):
    """
    Parameters
    ----------
    f : file
        File opened in "rb" mode.

    Returns
    -------
    info : dict
        Pre-selected relevant header fields.
    header : TYPE
        A copy of the entire header.
    """
    version = int(f.read(8).strip().decode())
    # Use seek to skip ahead to the interesting bytes.
    f.seek(184)
    end_header = int(f.read(8).strip().decode())
    f.seek(236)
    n_epochs = int(f.read(8).strip().decode())
    duration_epoch = float(f.read(8).strip().decode())
    n_channels = int(f.read(4).strip().decode())
    # Get the number of samples per channel per epoch.
    f.seek(256 + (n_channels * 216))    # within the channel specific section of the header, skip ahead to the number of samples fields
    n_samples = [int(f.read(8).strip().decode()) for i in range(n_channels)]
    # Infer the sampling rate.
    sfreqs = [int(np.rint(i / duration_epoch)) for i in n_samples]

    # Copy the entire header.
    f.seek(0)
    header = f.read(end_header)

    info = {"version": version,
            "end_header": end_header,
            "n_epochs": n_epochs,
            "duration_epoch": duration_epoch,
            "n_channels": n_channels,
            "n_samples": n_samples,
            "sfreqs": sfreqs}

    return info, header


def _read_edfsignal(f, startsignal):
    """
    Parameters
    ----------
    f : file
        File openend in "ab" mode.
    startsignal : TYPE
        Start of the signal in bytes.
    """
    # Skip to the start of the data records.
    f.seek(startsignal)
    # Read all the data.
    signal = np.fromfile(f, dtype=np.int16)    # one sample is encoded as two-byte integer (16 bits)

    return signal


def _read_edfchannel(signal, n_samples, chanidx):
    """
    Parameters
    ----------
    signal : Numpy array
        As returned by `_read_edfsignal()`.
    n_samples : list
        As returned by `_read_edfheader()`.
    chanidx : int
        One-based channel index.

    Returns
    -------
    chansignal : list
        The channel with index `chanidx` in `signal`.
    """
    n_chansamples = n_samples[chanidx - 1]
    # Get the starting index of the channel within an epoch.
    channel_offset = np.cumsum(n_samples)[chanidx - 1] - n_chansamples
    # Get the number of samples to skip from epoch to epoch.
    channel_stride = sum(n_samples)
    # Skip from epoch to epoch and read the signal belonging to the channel.
    epochstarts = np.arange(channel_offset, signal.size, channel_stride)
    chansignal = [signal[i:i + n_chansamples] for i in epochstarts]

    return np.ravel(chansignal)


def _padtrim(entry, n_bytes):
    """
    Pad or trim an EDF header field entry to n_bytes bytes.
    """
    entry = str(entry)
    n_bytes -= len(entry)
    if n_bytes >= 0:
        # Pad the input to the requested length.
        entry = entry + " " * n_bytes
    else:
        # Trim the input to the specified length-
        entry = entry[0:n_bytes]
    return entry.encode()
