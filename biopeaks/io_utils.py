# -*- coding: utf-8 -*-
"""Input/output utilities."""

import json
import pandas as pd
import numpy as np
from itertools import islice
from struct import pack
from pathlib import Path


def read_custom(rpath, customheader, channeltype):
    """Read a channel from a plain text file.

    Parameters
    ----------
    rpath : str
        File system location of the file.
    customheader : dict
        Dictionary containing header information (channel index,
        column separator, number of header rows, sampling frequency).
    channeltype : str
        The kind of channel to read. One of {"marker", "signal"}.

    Returns
    -------
    output : dict
        Dictionary containing the signal corresponding to the requested
        channel and any error raised while reading the signal from file. If
        `channeltype` is "signal", `output` also contains a vector containing
        the  seconds corresponding to the samples in the signal, as well as the
        signal's sampling frequency.
    """
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
        output["sec"] = np.linspace(0, signallen / sfreq, signallen)
        output["sfreq"] = sfreq

    output["signal"] = np.ravel(signal)

    return output


def write_custom(rpath, wpath, segment, customheader):
    """Write segmented channels to a plain text file.

    Save a copy of a plain text file after segmenting all channels it contains.

    Parameters
    ----------
    rpath : str
        File system location to read the original file from.
    wpath : str
        File system location to write the segmented copy of the file to.
    segment : list of float
        Start and end of the user-selected segment in seconds. This segment
        will be retained for all channels in the copy of the file.
    customheader : dict
        Dictionary containing custom header information (column separator,
        number of header rows, sampling frequency).
    """
    with open(rpath, "rt") as oldfile:
        header = [line for line in islice(oldfile, customheader["skiprows"])]    # original header
    data = pd.read_csv(rpath, sep=customheader["separator"], header=None,
                       skiprows=customheader["skiprows"])    # original channels
    begsamp = int(np.rint(segment[0] * customheader["sfreq"]))
    endsamp = int(np.rint(segment[1] * customheader["sfreq"]))
    data = data.iloc[begsamp:endsamp, :]    # apply segmentation to all channels

    with open(wpath, "w", newline='') as newfile:    # write header and segmented channels to new file
        for line in header:
            newfile.write(line)
        data.to_csv(newfile, sep=customheader["separator"], header=False,
                    index=False)


def read_opensignals(rpath, channel, channeltype):
    """Read a channel from an OpenSignals file.

    Parameters
    ----------
    rpath : str
        File system location of the file.
    channel : str
        The channel to be read.
    channeltype : str
        The kind of channel to read. One of {"marker", "signal"}.

    Returns
    -------
    output : dict
        Dictionary containing the signal corresponding to the requested
        channel and any error raised while reading the signal from file. If
        `channeltype` is "signal", `output` also contains a vector containing
        the  seconds corresponding to the samples in the signal, as well as the
        signal's sampling frequency.
    """
    output = {"error": False,
              "sec": None,
              "signal": None,
              "sfreq": None}

    with open(rpath, "r") as f:

        if "OpenSignals" not in f.readline():    # read first line
            output["error"] = "Error: Text file is not in OpenSignals format."
            return output

        metadata = json.loads(f.readline()[1:])    # read second line

    metadata = metadata[list(metadata.keys())[0]]    # convert json header to dict (only select first device / MAC address)
    sfreq = metadata["sampling rate"]
    channels = metadata["channels"]

    if channel[0] == "A":
        chanidx = [i for i, s in enumerate(channels) if int(channel[1]) == s]    # search index of the requested channel

        if not chanidx:
            output["error"] = f"Error: {channeltype.capitalize()} channel not found."
            return output

        chanidx = chanidx[0]    # select only first sensor of the selected modality (it is possible that multiple sensors of the same kind have been recorded)
        chanidx += 5    # since analog channels start in column 5 (zero based), add 5 to sensor index to obtain signal from selected modality

    elif channel[0] == "I":
        chanidx = int(channel[1])

    signal = pd.read_csv(rpath, sep='\t', usecols=[chanidx], header=None,
                         comment='#')

    if channeltype == "signal":
        signallen = signal.size
        output["sec"] = np.linspace(0, signallen / sfreq, signallen)
        output["sfreq"] = sfreq

    output["signal"] = np.ravel(signal)

    return output


def write_opensignals(rpath, wpath, segment, sfreq):
    """Write segmented channels to an OpenSignals file.

    Save a copy of an OpenSignals file after segmenting all channels it
    contains.

    Parameters
    ----------
    rpath : str
        File system location to read the original file from.
    wpath : str
        File system location to write the segmented copy of the file to.
    segment : list of float
        Start and end of the user-selected segment in seconds. This segment
        will be retained for all channels in the copy of the file.
    sfreq : int
        The sampling frequency of the channels.
    """
    with open(rpath, "rt") as oldfile:
        header = [line for line in islice(oldfile, 3)]
    data = pd.read_csv(rpath, sep='\t', header=None, comment='#')
    begsamp = int(np.rint(segment[0] * sfreq))
    endsamp = int(np.rint(segment[1] * sfreq))
    data = data.iloc[begsamp:endsamp, :]    # apply segmentation to all channels

    with open(wpath, "w", newline='') as newfile:
        for line in header:
            newfile.write(line)
        data.to_csv(newfile, sep='\t', header=False, index=False)


def read_edf(rpath, channel, channeltype):
    """Read a channel from an EDF file.

    Parameters
    ----------
    rpath : str
        File system location of the file.
    channel : str
        The channel to be read.
    channeltype : str
        The kind of channel to read. One of {"marker", "signal"}.

    Returns
    -------
    output : dict
        Dictionary containing the signal corresponding to the requested
        channel and any error raised while reading the signal from file. If
        `channeltype` is "signal", `output` also contains a vector containing
        the  seconds corresponding to the samples in the signal, as well as the
        signal's sampling frequency.

    Notes
    -----
    [1] contains details on the EDF file format. EDF testfiles are hosted here:
    https://www.teuniz.net/edf_bdf_testfiles/

    References
    ----------
    [1] B. Kemp, A. Värri, A. C. Rosa, K. D. Nielsen, and J. Gade, “A simple
    format for exchange of digitized polygraphic recordings,”
    Electroencephalography and Clinical Neurophysiology, vol. 82, no. 5,
    pp. 391–393, May 1992, doi: 10.1016/0013-4694(92)90009-7.
    """
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

    if info["n_epochs"] == -1:    # take care of improperly specified number of epochs
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
    """Write segmented channels to an EDF file.

    Save a copy of an EDF file after segmenting all channels it contains.

    Parameters
    ----------
    rpath : str
        File system location to read the original file from.
    wpath : str
        File system location to write the segmented copy of the file to.
    segment : list of float
        Start and end of the user-selected segment in seconds. This segment
        will be retained for all channels in the copy of the file.

    Notes
    -----
    [1] contains details on the EDF file format. EDF testfiles are hosted here:
    https://www.teuniz.net/edf_bdf_testfiles/

    References
    ----------
    [1] B. Kemp, A. Värri, A. C. Rosa, K. D. Nielsen, and J. Gade, “A simple
    format for exchange of digitized polygraphic recordings,”
    Electroencephalography and Clinical Neurophysiology, vol. 82, no. 5,
    pp. 391–393, May 1992, doi: 10.1016/0013-4694(92)90009-7.
    """
    with open(rpath, "rb") as f:
        info, header = _read_edfheader(f)
        signal = _read_edfsignal(f, info["end_header"])

    duration_segment = segment[1] - segment[0]
    if duration_segment < info["duration_epoch"]:
        error = f"Error: The segment is shorter than the epoch duration of " \
                f"{info['duration_epoch']} seconds in the original EDF file. " \
                f"Choose a segment longer than {info['duration_epoch']}."
        print(duration_segment, info["duration_epoch"])
        return error

    chansignals = [_read_edfchannel(signal, info["n_samples"], i)
                   for i in np.arange(info["n_channels"]) + 1]    # store the signal belonging to each channel as entry in a list

    for chan in range(info["n_channels"]):

        beg_segment = int(np.rint(info["sfreqs"][chan] * segment[0]))
        end_segment = int(np.rint(info["sfreqs"][chan] * segment[1]))
        chansignals[chan] = chansignals[chan][beg_segment:end_segment]    # cut out the segment from each channel.

    version = info["version"] + 1    # update file version.
    n_epochs = int(np.floor(duration_segment / info["duration_epoch"]))    # update number of epochs: rounding off is important, otherwise fraction of incomplete epoch could be appended

    with open(wpath, "wb") as f:

        f.write(header)    # copy the header to the new file ...
        f.seek(0)
        f.write(_padtrim(version, 8))    # update version
        f.seek(236)
        f.write(_padtrim(n_epochs, 8))    # update number of epochs
        f.seek(info["end_header"])
        for epoch in range(n_epochs):    # write the segmented channels to the new file using the original epoch duration

            for chan in range(info["n_channels"]):

                beg_epoch = epoch * info["n_samples"][chan]
                end_epoch = beg_epoch + info["n_samples"][chan]
                buffer = chansignals[chan][beg_epoch:end_epoch]
                buffer = [pack('h', i) for i in buffer]    # convert to C type
                for i in buffer:
                    f.write(i)


def _read_edfheader(f):
    """Read the header of an EDF file.

    Parameters
    ----------
    f : BufferedReader
        File opened in "rb" mode.

    Returns
    -------
    info : dict
        Dictionary containing a selection of relevant header fields.
    header : bytes
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
    """Read all channels in an EDF file.

    Parameters
    ----------
    f : BufferedReader
        File openend in "ab" mode.
    startsignal : int
        Start byte of the channels.

    Returns
    -------
    signal : ndarray
        Signal of all channels.
    """
    f.seek(startsignal)    # skip to the start of the data records
    signal = np.fromfile(f, dtype=np.int16)    # one sample is encoded as two-byte integer (16 bits)

    return signal


def _read_edfchannel(signal, n_samples, chanidx):
    """Read an EDF channel.

    Parameters
    ----------
    signal : ndarray
        Signal of all channels as returned by `_read_edfsignal`.
    n_samples : list
        As returned by `_read_edfheader`.
    chanidx : int
        One-based channel index.

    Returns
    -------
    chansignal : ndarray
        The channel with index `chanidx` in `signal`.
    """
    n_chansamples = n_samples[chanidx - 1]
    channel_offset = np.cumsum(n_samples)[chanidx - 1] - n_chansamples    # get starting index of the channel within an epoch
    channel_stride = sum(n_samples)    # number of samples to skip from epoch to epoch
    epochstarts = np.arange(channel_offset, signal.size, channel_stride)    # skip from epoch to epoch and read the signal belonging to the channel
    chansignal = [signal[i:i + n_chansamples] for i in epochstarts]

    return np.ravel(chansignal)


def _padtrim(entry, n_bytes):
    """Pad or trim an EDF header field `entry` to `n_bytes` bytes."""
    entry = str(entry)
    n_bytes -= len(entry)
    if n_bytes >= 0:
        entry = entry + " " * n_bytes    # pad entry to the requested length
    else:
        entry = entry[0:n_bytes]    # trim entry to the requested length
    return entry.encode()
