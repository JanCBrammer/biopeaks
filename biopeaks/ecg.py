# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from scipy.signal import find_peaks, medfilt
from .filters import butter_highpass_filter, powerline_filter
from .analysis_utils import (moving_average, threshold_normalization,
                             interp_stats, update_indices)


def ecg_peaks(signal, sfreq, smoothwindow=.1, avgwindow=.75,
              gradthreshweight=1.5, minlenweight=0.4, enable_plot=False):
    """
    enable_plot is for debugging and demonstration purposes when the function
    is called in isolation.
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
    mindelay = int(np.rint(sfreq * 0.3))

    # Visualize thresholds.
    if enable_plot:
        ax1.plot(filt)
        ax2.plot(smoothgrad)
        ax2.plot(gradthreshold)

    # Identify start and end of QRS complexes.
    qrs = smoothgrad > gradthreshold
    beg_qrs = np.where(np.logical_and(np.logical_not(qrs[0:-1]), qrs[1:]))[0]
    end_qrs = np.where(np.logical_and(qrs[0:-1], np.logical_not(qrs[1:])))[0]
    # Throw out QRS-ends that precede first QRS-start.
    end_qrs = end_qrs[end_qrs > beg_qrs[0]]

    # Identify R-peaks within QRS (ignore QRS that are too short).
    num_qrs = min(beg_qrs.size, end_qrs.size)
    min_len = np.mean(end_qrs[:num_qrs] - beg_qrs[:num_qrs]) * minlenweight
    peaks = [0]

    for i in range(num_qrs):

        beg = beg_qrs[i]
        end = end_qrs[i]
        len_qrs = end - beg

        if len_qrs < min_len:
            continue

        # Visualize QRS intervals.
        if enable_plot:
            ax2.axvspan(beg, end, facecolor="m", alpha=0.5)

        # Find local maxima and their prominence within QRS.
        data = signal[beg:end]
        locmax, props = find_peaks(data, prominence=(None, None))

        if locmax.size > 0:
            # Identify most prominent local maximum.
            peak = beg + locmax[np.argmax(props["prominences"])]
            # Enforce minimum delay between peaks.
            if peak - peaks[-1] > mindelay:
                peaks.append(peak)

    peaks.pop(0)

    if enable_plot:
        ax1.scatter(peaks, filt[peaks], c="r")

    return np.asarray(peaks).astype(int)


def ecg_period(peaks, sfreq, nsamp):

    # Get corrected peaks and normal-to-normal intervals.
    artifacts = _find_artifacts(peaks, sfreq)
    peaks_clean, nn = _correct_artifacts(artifacts, peaks, sfreq)

    # Iteratively apply the artifact correction until the number of artifact
    # reaches an equilibrium (i.e., the number of artifacts does not change
    # anymore from one iteration to the next).
    n_artifacts_previous = np.inf
    n_artifacts_current = sum([len(i) for i in artifacts.values()])

    previous_diff = 0

    while n_artifacts_current - n_artifacts_previous != previous_diff:

        previous_diff = n_artifacts_previous - n_artifacts_current

        artifacts = _find_artifacts(peaks_clean, sfreq)
        peaks_clean, nn = _correct_artifacts(artifacts, peaks_clean, sfreq)

        n_artifacts_previous = n_artifacts_current
        n_artifacts_current = sum([len(i) for i in artifacts.values()])

    # Interpolate rr at the signals sampling rate for plotting.
    periodintp = interp_stats(peaks_clean, nn, nsamp)
    rateintp = 60 / periodintp

    return peaks_clean, periodintp, rateintp


def _find_artifacts(peaks, sfreq, enable_plot=False):
    """
    Implementation of Jukka A. Lipponen & Mika P. Tarvainen (2019): A robust
    algorithm for heart rate variability time series artefact correction using
    novel beat classification, Journal of Medical Engineering & Technology,
    DOI: 10.1080/03091902.2019.1640306
    """
    peaks = np.ravel(peaks)

    # Set free parameters.
    c1 = 0.13
    c2 = 0.17
    alpha = 5.2
    window_half = 45
    medfilt_order = 11

    # Compute period series (make sure it has same numer of elements as peaks);
    # peaks are in samples, convert to seconds.
    rr = np.ediff1d(peaks, to_begin=0) / sfreq
    # For subsequent analysis it is important that the first element has
    # a value in a realistic range (e.g., for median filtering).
    rr[0] = np.mean(rr[1:])

    # Compute differences of consecutive periods.
    drrs = np.ediff1d(rr, to_begin=0)
    drrs[0] = np.mean(drrs[1:])
    # Normalize by threshold.
    drrs, _ = threshold_normalization(drrs, alpha, window_half)

    # Pad drrs with one element.
    padding = 2
    drrs_pad = np.pad(drrs, padding, "reflect")
    # Cast drrs to two-dimesnional subspace s1.
    s12 = np.zeros(drrs.size)
    for d in np.arange(padding, padding + drrs.size):

        if drrs_pad[d] > 0:
            s12[d - padding] = np.max([drrs_pad[d - 1], drrs_pad[d + 1]])
        elif drrs_pad[d] < 0:
            s12[d - padding] = np.min([drrs_pad[d - 1], drrs_pad[d + 1]])

    # Cast drrs to two-dimensional subspace s2 (looping over index d a second
    # consecutive time is choice to be explicit rather than efficient).
    s22 = np.zeros(drrs.size)
    for d in np.arange(padding, padding + drrs.size):

        if drrs_pad[d] > 0:
            s22[d - padding] = np.max([drrs_pad[d + 1], drrs_pad[d + 2]])
        elif drrs_pad[d] < 0:
            s22[d - padding] = np.min([drrs_pad[d + 1], drrs_pad[d + 2]])

    # Compute deviation of RRs from median RRs.
    padding = medfilt_order // 2    # pad RR series before filtering
    rr_pad = np.pad(rr, padding, "reflect")
    medrr = medfilt(rr_pad, medfilt_order)
    medrr = medrr[padding:padding + rr.size]    # remove padding
    mrrs = rr - medrr
    mrrs[mrrs < 0] = mrrs[mrrs < 0] * 2
    mrrs, th2 = threshold_normalization(mrrs, alpha, window_half)    # normalize by threshold

    # Artifact identification
    #########################
    # Keep track of indices that need to be interpolated, removed, or added.
    extra_idcs = []
    missed_idcs = []
    ectopic_idcs = []
    longshort_idcs = []

    for i in range(peaks.size - 2):

        if np.abs(drrs[i]) <= 1:
            continue

        # Check for ectopic peaks (based on Figure 2a).
        eq1 = np.logical_and(drrs[i] > 1, s12[i] < (-c1 * drrs[i] - c2))
        eq2 = np.logical_and(drrs[i] < -1, s12[i] > (-c1 * drrs[i] + c2))

        if np.any([eq1, eq2]):
            # If any of the two equations is true.
            ectopic_idcs.append(i)
            continue

        # If none of the two equations is true.
        # Check for long or short beats (based on Figure 2b).
        if np.logical_or(np.abs(drrs[i]) > 1, np.abs(mrrs[i]) > 3):
            # Long beat.
            eq3 = np.logical_and(drrs[i] > 1, s22[i] < -1)
            eq4 = np.abs(mrrs[i]) > 3
            # Short beat.
            eq5 = np.logical_and(drrs[i] < -1, s22[i] > 1)

        if ~np.any([eq3, eq4, eq5]):
            # If none of the three equations is true: normal beat.
            continue

        # If any of the three equations is true: check for missing or extra
        # peaks.

        # Missing.
        eq6 = np.abs(rr[i] / 2 - medrr[i]) < th2[i]
        # Extra.
        eq7 = np.abs(rr[i] + rr[i + 1] - medrr[i]) < th2[i]

        # Check if short or extra.
        if eq5:
            if eq7:
                extra_idcs.append(i)
            else:
                longshort_idcs.append(i)
                if np.abs(drrs[i + 1]) < np.abs(drrs[i + 2]):
                    longshort_idcs.append(i + 1)
        # Check if long or missing.
        if np.any([eq3, eq4]):
            if eq6:
                missed_idcs.append(i)
            else:
                longshort_idcs.append(i)
                if np.abs(drrs[i + 1]) < np.abs(drrs[i + 2]):
                    longshort_idcs.append(i + 1)

    if enable_plot:
        # Visualize artifact type indices.
        fig0, (ax0, ax1, ax2) = plt.subplots(nrows=3, ncols=1, sharex=True)
        ax0.set_title("Artifact types", fontweight="bold")
        ax0.plot(rr, label="heart period")
        ax0.scatter(longshort_idcs, rr[longshort_idcs], marker='x', c='m',
                    s=100, zorder=3, label="long/short")
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

    artifacts = {"extra": extra_idcs, "missed": missed_idcs,
                 "longshort": longshort_idcs, "ectopic": ectopic_idcs}

    return artifacts


def _correct_artifacts(artifacts, peaks, sfreq):

    # Artifact correction
    #####################
    # The integrity of indices must be maintained if peaks are inserted or
    # deleted: for each deleted beat, decrease indices following that beat in
    # all other index lists by 1. Likewise, for each added beat, increment the
    # indices following that beat in all other lists by 1.
    extra_idcs = artifacts["extra"]
    missed_idcs = artifacts["missed"]
    ectopic_idcs = artifacts["ectopic"]
    longshort_idcs = artifacts["longshort"]

    # Delete extra peaks.
    if extra_idcs:
        peaks = np.delete(peaks, extra_idcs)
        # Update remaining indices.
        missed_idcs = update_indices(extra_idcs, missed_idcs, -1)
        ectopic_idcs = update_indices(extra_idcs, ectopic_idcs, -1)
        longshort_idcs = update_indices(extra_idcs, longshort_idcs, -1)

    # Add missing peaks.
    if missed_idcs:
        # Calculate the position(s) of new beat(s). Make sure to not generate
        # negative indices.
        prev_peaks = peaks[[i - 1 for i in missed_idcs if i >= 1]]
        next_peaks = peaks[missed_idcs]
        added_peaks = prev_peaks + (next_peaks - prev_peaks) / 2
        # Add the new peaks before the missed indices (see numpy docs).
        peaks = np.insert(peaks, missed_idcs, added_peaks)
        # Update remaining indices.
        ectopic_idcs = update_indices(missed_idcs, ectopic_idcs, 1)
        longshort_idcs = update_indices(missed_idcs, longshort_idcs, 1)

    # Interpolate ectopic as well as long or short peaks (important to do
    # this after peaks are deleted and/or added).
    interp_idcs = np.concatenate((ectopic_idcs, longshort_idcs)).astype(int)
    if interp_idcs.size > 0:
        interp_idcs.sort(kind='mergesort')
        # Make sure to not generate negative indices, or indices that exceed
        # the total number of peaks.
        prev_peaks = peaks[[i - 1 for i in interp_idcs if i >= 1]]
        next_peaks = peaks[[i + 1 for i in interp_idcs if i < len(peaks)]]
        peaks_interp = prev_peaks + (next_peaks - prev_peaks) / 2
        # Shift the R-peaks from the old to the new position.
        peaks = np.delete(peaks, interp_idcs)
        peaks = np.concatenate((peaks, peaks_interp)).astype(int)
        peaks.sort(kind="mergesort")
        peaks = np.unique(peaks)

    # Compute normal-to-normal intervals.
    nn = np.ediff1d(peaks, to_begin=0) / sfreq
    nn[0] = np.mean(nn[1:])

    return peaks, nn
