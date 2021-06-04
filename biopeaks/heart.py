# -*- coding: utf-8 -*-
"""Extract features from cardiac signals."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from scipy.signal import find_peaks
from biopeaks.filters import (butter_highpass_filter, powerline_filter,
                              moving_average, butter_bandpass_filter)
from biopeaks.analysis_utils import find_segments, interp_stats


def ecg_peaks(signal, sfreq, smoothwindow=.1, avgwindow=.75,
              gradthreshweight=1.5, minlenweight=.4, mindelay=.3,
              enable_plot=False):
    """Detect R-peaks in an electrocardiogram (ECG).

    QRS complexes are detected based on the steepness of the absolute gradient
    of the ECG signal. Subsequently, R-peaks are detected as local maxima in
    the QRS complexes.

    Parameters
    ----------
    signal : ndarray
        The ECG signal.
    sfreq : int
        The sampling frequency of `signal`.
    smoothwindow : float, optional
        Size of the kernel used for smoothing the absolute gradient of `signal`.
        In seconds. Default is .1.
    avgwindow : float, optional
        Size of the kernel used for computing the local average of the smoothed
        absolute gradient of `signal`. In seconds. Default is .75.
    gradthreshweight : float, optional
        Factor used to offset the averaged absolute gradient of `signal`. The
        resulting time series is then used as a threshold for QRS detection.
        Default is 1.5.
    minlenweight : float, optional
        The average QRS duration is multiplied by `minlenweight` in order to
        obtain a threshold for the minimal duration of QRS complexes (QRS
        complexes shorted than the minimal duration will be discared). Default
        is .4.
    mindelay : float, optional
        Minimal delay between R-peaks. R-peaks that follow other R-peaks by less
        than `mindelay` will be discarded. In seconds. Default is .3.
    enable_plot : bool, optional
        Visualize `signal` along with the detection thresholds, as well as the
        detected QRS complexes and R-peaks. Default is False.

    Returns
    -------
    peaks : ndarray
        The samples within `signal` that mark the occurrences of R-peaks.
    """
    if enable_plot:
        plt.figure()
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212, sharex=ax1)

    filt = butter_highpass_filter(signal, .5, sfreq)
    filt = powerline_filter(filt, sfreq)

    grad = np.gradient(filt)
    absgrad = np.abs(grad)
    smoothgrad = moving_average(absgrad, int(np.rint(smoothwindow * sfreq)))
    avggrad = moving_average(smoothgrad, int(np.rint(avgwindow * sfreq)))
    gradthreshold = gradthreshweight * avggrad
    mindelay = int(np.rint(sfreq * mindelay))

    if enable_plot:
        ax1.plot(filt)
        ax2.plot(smoothgrad)
        ax2.plot(gradthreshold)

    qrs = smoothgrad > gradthreshold
    beg_qrs, end_qrs, durations_qrs = find_segments(qrs)

    # Identify R-peaks within QRS (ignore QRS that are too short).
    min_len = np.mean(durations_qrs) * minlenweight
    peaks = [0]

    for beg, end, duration in zip(beg_qrs, end_qrs, durations_qrs):

        if duration < min_len:
            continue

        if enable_plot:
            ax2.axvspan(beg, end, facecolor="m", alpha=0.5)    # visualize QRS

        data = signal[beg:end]
        locmax, props = find_peaks(data, prominence=(None, None))    # find local maxima and their prominence within QRS

        if locmax.size > 0:
            peak = beg + locmax[np.argmax(props["prominences"])]    # identify most prominent local maximum
            if peak - peaks[-1] > mindelay:    # enforce minimum delay between R-peaks
                peaks.append(peak)

    peaks.pop(0)

    if enable_plot:
        ax1.scatter(peaks, filt[peaks], c="r")

    return np.asarray(peaks).astype(int)


def ppg_peaks(signal, sfreq, peakwindow=.111, beatwindow=.667, beatoffset=.02,
              mindelay=.3, enable_plot=False):
    """Detect systolic peaks in a photoplethysmogram (PPG).

    Implementation of "Method IV: Event-Related Moving Averages with Dynamic
    Threshold" introduced by [1].

    Parameters
    ----------
    signal : ndarray
        The PPG signal.
    sfreq : int
        Sampling frequency of `signal`.
    peakwindow : float, optional
        "W1" parameter described in [1]. In seconds. Default is .111.
    beatwindow : float, optional
        "W2" parameter described in [1]. In seconds. Default is .667.
    beatoffset : float, optional
        "beta" parameter described in [1]. Default is .02.
    mindelay : float, optional
        Minimal delay between systolic peaks. Systolic peaks that follow other
        systolic peaks by less than `mindelay` will be discarded. In seconds.
        Default is .3.
    enable_plot : bool, optional
        Visualize `signal` along with the detection thresholds, as well as the
        detected PPG waves and systolic peaks. Default is False.

    Returns
    -------
    peaks : ndarray
        The samples within `signal` that mark the occurrences of systolic peaks.

    References
    ----------
    [1] M. Elgendi, I. Norton, M. Brearley, D. Abbott, and D. Schuurmans,
    “Systolic Peak Detection in Acceleration Photoplethysmograms Measured from
    Emergency Responders in Tropical Conditions,” PLoS ONE, vol. 8, no. 10,
    Oct. 2013, doi: 10.1371/journal.pone.0076585.
    """
    if enable_plot:
        fig, (ax0, ax1) = plt.subplots(nrows=2, ncols=1, sharex=True)

    filt = butter_bandpass_filter(signal, lowcut=.5, highcut=8, sfreq=sfreq,
                                  order=3)
    filt[filt < 0] = 0
    sqrd = filt**2

    ma_peak = moving_average(sqrd, int(np.rint(peakwindow * sfreq)))
    ma_beat = moving_average(sqrd, int(np.rint(beatwindow * sfreq)))
    thr1 = ma_beat + beatoffset * np.mean(sqrd)

    if enable_plot:
        ax0.plot(signal)
        ax1.plot(filt, label="filtered")
        ax1.plot(sqrd, label="squared")
        ax1.plot(thr1, label="threshold")
        ax1.legend(loc="upper right")

    waves = ma_peak > thr1
    beg_waves, end_waves, duration_waves = find_segments(waves)

    min_len = int(np.rint(peakwindow * sfreq))
    min_delay = int(np.rint(mindelay * sfreq))
    peaks = [0]

    for beg, end, duration in zip(beg_waves, end_waves, duration_waves):

        if duration < min_len:
            continue

        if enable_plot:
            ax1.axvspan(beg, end, facecolor="m", alpha=0.5)    # visualize waves

        data = signal[beg:end]
        locmax, props = find_peaks(data, prominence=(None, None))    # find local maxima and their prominence within waves

        if locmax.size > 0:

            peak = beg + locmax[np.argmax(props["prominences"])]    # identify most prominent local maximum
            if peak - peaks[-1] > min_delay:    # enforce minimum delay between systolic peaks
                peaks.append(peak)

    peaks.pop(0)

    if enable_plot:
        ax0.scatter(peaks, signal[peaks], c="r")

    return np.asarray(peaks).astype(int)


def heart_stats(peaks, sfreq, nsamp):
    """Compute instantaneous cardiac features.

    Compute heart period and -rate based on cardiac extrema (R-peaks or
    systolic peaks). Cardiac period and -rate are calculated as horizontal
    (temporal) peak-peak differences. I.e., to each peak assign the horizontal
    difference to the preceding peak.

    Parameters
    ----------
    peaks : ndarray
        Cardiac extrema (R-peaks or systolic peaks).
    sfreq : int
        Sampling frequency of the cardiac signal containing `peaks`.
    nsamp : int
        The length of the signal containing `peaks`. In samples.

    Returns
    -------
    periodintp, rateintp : ndarray, ndarray
        Vectors with witb `nsamp` elements, containing the instantaneous
        heart period, and -rate.
    """
    rr = np.ediff1d(peaks, to_begin=0) / sfreq
    rr[0] = np.mean(rr[1:])

    periodintp = interp_stats(peaks, rr, nsamp)
    rateintp = 60 / periodintp

    return periodintp, rateintp


def correct_peaks(peaks, sfreq, iterative=True):
    """Correct artifacts in cardiac peak detection.

    Implementation of [1].

    Parameters
    ----------
    peaks : ndarray
        Cardiac extrema (R-peaks or systolic peaks).
    sfreq : int
        Sampling frequency of the cardiac signal containing `peaks`.
    iterative : bool, optional
        Repeat correction until heuristic convergence. Default is True.
        The iterative application of the artifact correction is not part of
        the algorithm described in [1].

    Returns
    -------
    peaks_clean : ndarray
        Cardiac extrema (R-peaks or systolic peaks) after artifact correction.

    References
    ----------
    [1] J. A. Lipponen and M. P. Tarvainen, “A robust algorithm for heart rate
    variability time series artefact correction using novel beat
    classification,” Journal of Medical Engineering & Technology, vol. 43,
    no. 3, pp. 173–181, Apr. 2019, doi: 10.1080/03091902.2019.1640306.
    """
    artifacts = _find_artifacts(peaks, sfreq)
    peaks_clean = _correct_artifacts(artifacts, peaks)

    if iterative:
        hashed_artifacts = _hash_artifacts(artifacts)
        # Keep track of all artifact constellations that occurred throughout iterations.
        # Hash artifacts to avoid keeping track of dictionaries. Use set for fast lookup.
        previous_artifacts = {hashed_artifacts}

        while True:

            artifacts = _find_artifacts(peaks_clean, sfreq)
            hashed_artifacts = _hash_artifacts(artifacts)
            if hashed_artifacts in previous_artifacts:
                # Stop iterating if this exact artifact constellation occurred before,
                # which heuristically implies convergence in the form of
                # a) cyclic recurrence of artifact constellations or b) unchanging artifact constellation.
                break
            previous_artifacts.add(hashed_artifacts)
            peaks_clean = _correct_artifacts(artifacts, peaks_clean)

    return peaks_clean


def _hash_artifacts(artifacts):
    """Hash artifact constellation."""
    flattened_artifacts = [item for sublist in artifacts.values()
                           for item in sublist]
    hashed_artifacts = hash(tuple(flattened_artifacts))    # only immutable structures allow hashing, hence conversion

    return hashed_artifacts


def _find_artifacts(peaks, sfreq, enable_plot=False):
    """Detect and classify artifacts."""
    peaks = np.ravel(peaks)

    c1 = 0.13
    c2 = 0.17
    alpha = 5.2
    window_width = 91
    medfilt_order = 11

    rr = np.ediff1d(peaks, to_begin=0) / sfreq    # first difference of peaks
    rr[0] = np.mean(rr[1:])

    # Artifact identification #################################################
    ###########################################################################

    drrs = np.ediff1d(rr, to_begin=0)    # differences of consecutive periods, i.e., second difference of peaks
    drrs[0] = np.mean(drrs[1:])
    th1 = _compute_threshold(drrs, alpha, window_width)
    drrs /= th1    # normalize by threshold

    padding = 2
    drrs_pad = np.pad(drrs, padding, "reflect")    # pad drrs with two elements

    s12 = np.zeros(drrs.size)
    for d in np.arange(padding, padding + drrs.size):    # cast dRRs to subspace s12

        if drrs_pad[d] > 0:
            s12[d - padding] = np.max([drrs_pad[d - 1], drrs_pad[d + 1]])
        elif drrs_pad[d] < 0:
            s12[d - padding] = np.min([drrs_pad[d - 1], drrs_pad[d + 1]])

    s22 = np.zeros(drrs.size)
    for d in np.arange(padding, padding + drrs.size):    # cast dRRs to subspace s22

        if drrs_pad[d] >= 0:
            s22[d - padding] = np.min([drrs_pad[d + 1], drrs_pad[d + 2]])
        elif drrs_pad[d] < 0:
            s22[d - padding] = np.max([drrs_pad[d + 1], drrs_pad[d + 2]])

    df = pd.DataFrame({'signal': rr})
    medrr = df.rolling(medfilt_order, center=True,
                       min_periods=1).median().signal.to_numpy()
    mrrs = rr - medrr    # deviation of RRs from median RR
    mrrs[mrrs < 0] = mrrs[mrrs < 0] * 2
    th2 = _compute_threshold(mrrs, alpha, window_width)
    mrrs /= th2    # normalize by threshold

    # Artifact classification #################################################
    ###########################################################################
    extra_idcs = []
    missed_idcs = []
    ectopic_idcs = []
    longshort_idcs = []

    i = 0
    while i < rr.size - 2:    # flow control is implemented based on Figure 1

        if np.abs(drrs[i]) <= 1:    # Figure 1
            i += 1
            continue
        eq1 = np.logical_and(drrs[i] > 1, s12[i] < (-c1 * drrs[i] - c2))    # Figure 2a
        eq2 = np.logical_and(drrs[i] < -1, s12[i] > (-c1 * drrs[i] + c2))    # Figure 2a

        if np.any([eq1, eq2]):    # If any of the two equations is true.
            ectopic_idcs.append(i)
            i += 1
            continue
        # If none of the two equations is true.
        if ~np.any([np.abs(drrs[i]) > 1, np.abs(mrrs[i]) > 3]):    # Figure 1
            i += 1
            continue
        longshort_candidates = [i]

        if np.abs(drrs[i + 1]) < np.abs(drrs[i + 2]):    # check if the following beat also needs to be evaluated
            longshort_candidates.append(i + 1)

        for j in longshort_candidates:

            eq3 = np.logical_and(drrs[j] > 1, s22[j] < -1)    # long beat, Figure 2b
            eq4 = np.abs(mrrs[j]) > 3    # long or short, Figure 1
            eq5 = np.logical_and(drrs[j] < -1, s22[j] > 1)    # short beat, Figure 2b

            if ~np.any([eq3, eq4, eq5]):    # if none of the three equations is true: normal beat
                i += 1
                continue
            # If any of the three equations is true: check for missing or extra
            # peaks.
            eq6 = np.abs(rr[j] / 2 - medrr[j]) < th2[j]    # missing beat, Figure 1
            eq7 = np.abs(rr[j] + rr[j + 1] - medrr[j]) < th2[j]    # extra beat, Figure 1

            if np.all([eq5, eq7]):    # check if extra
                extra_idcs.append(j)
                i += 1
                continue
            if np.all([eq3, eq6]):    # check if missing
                missed_idcs.append(j)
                i += 1
                continue
            longshort_idcs.append(j)    # if neither classified as extra or missing, classify as "long or short"
            i += 1

    artifacts = {"ectopic": ectopic_idcs, "missed": missed_idcs,
                 "extra": extra_idcs, "longshort": longshort_idcs}

    if enable_plot:
        # Visualize artifact type indices.
        fig0, (ax0, ax1, ax2) = plt.subplots(nrows=3, ncols=1, sharex=True)
        ax0.set_title("Artifact types", fontweight="bold")
        ax0.plot(rr, label="heart period")
        ax0.scatter(longshort_idcs, rr[longshort_idcs], marker='x', c='m',
                    s=100, zorder=3, label="longshort")
        ax0.scatter(ectopic_idcs, rr[ectopic_idcs], marker='x', c='g', s=100,
                    zorder=3, label="ectopic")
        ax0.scatter(extra_idcs, rr[extra_idcs], marker='x', c='y', s=100,
                    zorder=3, label="false positive")
        ax0.scatter(missed_idcs, rr[missed_idcs], marker='x', c='r', s=100,
                    zorder=3, label="false negative")
        ax0.legend(loc="upper right")

        # Visualize first threshold.
        ax1.set_title("Consecutive-difference criterion", fontweight="bold")
        ax1.plot(np.abs(drrs), label="difference consecutive heart periods")
        ax1.axhline(1, c='r', label="artifact threshold")
        ax1.legend(loc="upper right")

        # Visualize second thresold.
        ax2.set_title("Difference-from-median criterion", fontweight="bold")
        ax2.plot(np.abs(mrrs), label="difference from median over 11 periods")
        ax2.axhline(3, c="r", label="artifact threshold")
        ax2.legend(loc="upper right")

        # Visualize subspaces.
        fig1, (ax3, ax4) = plt.subplots(nrows=1, ncols=2)
        ax3.set_title("Subspace 1", fontweight="bold")
        ax3.set_xlabel("S11")
        ax3.set_ylabel("S12")
        ax3.scatter(drrs, s12, marker="x", label="heart periods")
        verts0 = [(min(drrs), max(s12)),
                  (min(drrs), -c1 * min(drrs) + c2),
                  (-1, -c1 * -1 + c2),
                  (-1, max(s12))]
        poly0 = Polygon(verts0, alpha=0.3, facecolor="r", edgecolor=None,
                        label="ectopic periods")
        ax3.add_patch(poly0)
        verts1 = [(1, -c1 * 1 - c2),
                  (1, min(s12)),
                  (max(drrs), min(s12)),
                  (max(drrs), -c1 * max(drrs) - c2)]
        poly1 = Polygon(verts1, alpha=0.3, facecolor="r", edgecolor=None)
        ax3.add_patch(poly1)
        ax3.legend(loc="upper right")

        ax4.set_title("Subspace 2", fontweight="bold")
        ax4.set_xlabel("S21")
        ax4.set_ylabel("S22")
        ax4.scatter(drrs, s22, marker="x", label="heart periods")
        verts2 = [(min(drrs), max(s22)),
                  (min(drrs), 1),
                  (-1, 1),
                  (-1, max(s22))]
        poly2 = Polygon(verts2, alpha=0.3, facecolor="r", edgecolor=None,
                        label="short periods")
        ax4.add_patch(poly2)
        verts3 = [(1, -1),
                  (1, min(s22)),
                  (max(drrs), min(s22)),
                  (max(drrs), -1)]
        poly3 = Polygon(verts3, alpha=0.3, facecolor="y", edgecolor=None,
                        label="long periods")
        ax4.add_patch(poly3)
        ax4.legend(loc="upper right")

    return artifacts


def _correct_artifacts(artifacts, peaks):
    """Apply artifact-class specific correction.

    The integrity of indices must be maintained if peaks are inserted or
    deleted: for each deleted beat, decrease indices following that beat in
    all other index lists by 1. Likewise, for each added beat, increment the
    indices following that beat in all other lists by 1.
    """
    extra_idcs = artifacts["extra"]
    missed_idcs = artifacts["missed"]
    ectopic_idcs = artifacts["ectopic"]
    longshort_idcs = artifacts["longshort"]

    # Delete extra peaks.
    if extra_idcs:
        peaks = _correct_extra(extra_idcs, peaks)
        # Update remaining indices.
        missed_idcs = _update_indices(extra_idcs, missed_idcs, -1)
        ectopic_idcs = _update_indices(extra_idcs, ectopic_idcs, -1)
        longshort_idcs = _update_indices(extra_idcs, longshort_idcs, -1)

    # Add missing peaks.
    if missed_idcs:
        peaks = _correct_missed(missed_idcs, peaks)
        # Update remaining indices.
        ectopic_idcs = _update_indices(missed_idcs, ectopic_idcs, 1)
        longshort_idcs = _update_indices(missed_idcs, longshort_idcs, 1)

    if ectopic_idcs:
        peaks = _correct_misaligned(ectopic_idcs, peaks)

    if longshort_idcs:
        peaks = _correct_misaligned(longshort_idcs, peaks)

    return peaks


def _correct_extra(extra_idcs, peaks):

    corrected_peaks = peaks.copy()
    corrected_peaks = np.delete(corrected_peaks, extra_idcs)

    return corrected_peaks


def _correct_missed(missed_idcs, peaks):

    corrected_peaks = peaks.copy()
    missed_idcs = np.array(missed_idcs)
    valid_idcs = missed_idcs > 1    # make sure to not generate negative indices
    missed_idcs = missed_idcs[valid_idcs]
    prev_peaks = corrected_peaks[[i - 1 for i in missed_idcs]]
    next_peaks = corrected_peaks[missed_idcs]    # prev_peaks and next_peaks must have the same number of elements
    added_peaks = prev_peaks + (next_peaks - prev_peaks) / 2    # calculate the position(s) of new beat(s)
    corrected_peaks = np.insert(corrected_peaks, missed_idcs, added_peaks)    # add the new peaks before the missed indices (see NumPy docs)

    return corrected_peaks


def _correct_misaligned(misaligned_idcs, peaks):

    corrected_peaks = peaks.copy()
    misaligned_idcs = np.array(misaligned_idcs)
    valid_idcs = np.logical_and(misaligned_idcs > 1,
                                misaligned_idcs < (len(corrected_peaks) - 1))    # make sure to not generate negative indices, or indices that exceed the total number of peaks
    misaligned_idcs = misaligned_idcs[valid_idcs]
    prev_peaks = corrected_peaks[[i - 1 for i in misaligned_idcs]]
    next_peaks = corrected_peaks[[i + 1 for i in misaligned_idcs]]    # prev_peaks and next_peaks must have the same number of elements
    # Shift the R-peaks from the old to the new position.
    half_ibi = (next_peaks - prev_peaks) / 2
    peaks_interp = prev_peaks + half_ibi
    corrected_peaks = np.delete(corrected_peaks, misaligned_idcs)
    corrected_peaks = np.concatenate((corrected_peaks,
                                      peaks_interp)).astype(int)
    corrected_peaks.sort(kind="mergesort")

    return corrected_peaks


def _compute_threshold(signal, alpha, window_width):

    df = pd.DataFrame({'signal': np.abs(signal)})
    q1 = df.rolling(window_width, center=True,
                    min_periods=1).quantile(.25).signal.to_numpy()
    q3 = df.rolling(window_width, center=True,
                    min_periods=1).quantile(.75).signal.to_numpy()
    th = alpha * ((q3 - q1) / 2)

    return th


def _update_indices(source_idcs, update_idcs, update):

    if not update_idcs:
        return update_idcs

    for s in source_idcs:
        update_idcs = [u + update if u > s else u for u in update_idcs]    # for each list, find the indices (of indices) that need to be updated

    return update_idcs
