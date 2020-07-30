# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from scipy.signal import find_peaks
from .filters import (butter_highpass_filter, powerline_filter,
                      moving_average, butter_bandpass_filter)
from .analysis_utils import (compute_threshold, interp_stats, update_indices)


def ecg_peaks(signal, sfreq, smoothwindow=.1, avgwindow=.75,
              gradthreshweight=1.5, minlenweight=0.4, mindelay=.3,
              enable_plot=False):
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
    mindelay = int(np.rint(sfreq * mindelay))

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

    for beg, end in zip(beg_qrs, end_qrs):

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


def ppg_peaks(signal, sfreq, peakwindow=.111, beatwindow=.667, beatoffset=.02,
              mindelay=.3, enable_plot=False):
    """
    Implementation of Elgendi M, Norton I, Brearley M, Abbott D, Schuurmans D
    (2013) Systolic Peak Detection in Acceleration Photoplethysmograms Measured
    from Emergency Responders in Tropical Conditions. PLoS ONE 8(10): e76585.
    doi:10.1371/journal.pone.0076585.

    Enable_plot is for debugging and demonstration purposes when the function
    is called in isolation.
    """

    if enable_plot:
        fig, (ax0, ax1) = plt.subplots(nrows=2, ncols=1, sharex=True)

    filt = butter_bandpass_filter(signal, lowcut=.5, highcut=8, fs=sfreq,
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

    # Identify start and end of PPG waves.
    waves = ma_peak > thr1
    beg_waves = np.where(np.logical_and(np.logical_not(waves[0:-1]),
                                        waves[1:]))[0]
    end_waves = np.where(np.logical_and(waves[0:-1],
                                        np.logical_not(waves[1:])))[0]
    # Throw out wave-ends that precede first wave-start.
    end_waves = end_waves[end_waves > beg_waves[0]]

    # Identify systolic peaks within waves (ignore waves that are too short).
    min_len = int(np.rint(peakwindow * sfreq))
    min_delay = int(np.rint(mindelay * sfreq))
    peaks = [0]

    for beg, end in zip(beg_waves, end_waves):

        len_wave = end - beg
        if len_wave < min_len:
            continue

        # Visualize wave span.
        if enable_plot:
            ax1.axvspan(beg, end, facecolor="m", alpha=0.5)

        # Find local maxima and their prominence within wave span.
        data = signal[beg:end]
        locmax, props = find_peaks(data, prominence=(None, None))

        if locmax.size > 0:
            # Identify most prominent local maximum.
            peak = beg + locmax[np.argmax(props["prominences"])]
            # Enforce minimum delay between peaks.
            if peak - peaks[-1] > min_delay:
                peaks.append(peak)

    peaks.pop(0)

    if enable_plot:
        ax0.scatter(peaks, signal[peaks], c="r")

    return np.asarray(peaks).astype(int)


def heart_period(peaks, sfreq, nsamp):

    # Compute normal-to-normal intervals.
    rr = np.ediff1d(peaks, to_begin=0) / sfreq
    rr[0] = np.mean(rr[1:])

    # Interpolate rr at the signals sampling rate for plotting.
    periodintp = interp_stats(peaks, rr, nsamp)
    rateintp = 60 / periodintp

    return periodintp, rateintp


def correct_peaks(peaks, sfreq, iterative=True):

    # Get corrected peaks and normal-to-normal intervals.
    artifacts = _find_artifacts(peaks, sfreq)
    peaks_clean = _correct_artifacts(artifacts, peaks)

    if iterative:

        # Iteratively apply the artifact correction until the number of artifact
        # reaches an equilibrium (i.e., the number of artifacts does not change
        # anymore from one iteration to the next).
        n_artifacts_previous = np.inf
        n_artifacts_current = sum([len(i) for i in artifacts.values()])

        previous_diff = 0

        while n_artifacts_current - n_artifacts_previous != previous_diff:

            previous_diff = n_artifacts_previous - n_artifacts_current

            artifacts = _find_artifacts(peaks_clean, sfreq)
            peaks_clean = _correct_artifacts(artifacts, peaks_clean)

            n_artifacts_previous = n_artifacts_current
            n_artifacts_current = sum([len(i) for i in artifacts.values()])

    return peaks_clean


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
    window_width = 91
    medfilt_order = 11

    # Compute period series (make sure it has same numer of elements as peaks);
    # peaks are in samples, convert to seconds.
    rr = np.ediff1d(peaks, to_begin=0) / sfreq
    # For subsequent analysis it is important that the first element has
    # a value in a realistic range (e.g., for median filtering).
    rr[0] = np.mean(rr[1:])

    # Artifact identification #################################################
    ###########################################################################

    # Compute dRRs: time series of differences of consecutive periods (dRRs).
    drrs = np.ediff1d(rr, to_begin=0)
    drrs[0] = np.mean(drrs[1:])
    # Normalize by threshold.
    th1 = compute_threshold(drrs, alpha, window_width)
    drrs /= th1

    # Cast dRRs to subspace s12.
    # Pad drrs with one element.
    padding = 2
    drrs_pad = np.pad(drrs, padding, "reflect")

    s12 = np.zeros(drrs.size)
    for d in np.arange(padding, padding + drrs.size):

        if drrs_pad[d] > 0:
            s12[d - padding] = np.max([drrs_pad[d - 1], drrs_pad[d + 1]])
        elif drrs_pad[d] < 0:
            s12[d - padding] = np.min([drrs_pad[d - 1], drrs_pad[d + 1]])

    # Cast dRRs to subspace s22.
    s22 = np.zeros(drrs.size)
    for d in np.arange(padding, padding + drrs.size):

        if drrs_pad[d] >= 0:
            s22[d - padding] = np.min([drrs_pad[d + 1], drrs_pad[d + 2]])
        elif drrs_pad[d] < 0:
            s22[d - padding] = np.max([drrs_pad[d + 1], drrs_pad[d + 2]])

    # Compute mRRs: time series of deviation of RRs from median.
    df = pd.DataFrame({'signal': rr})
    medrr = df.rolling(medfilt_order, center=True,
                       min_periods=1).median().signal.to_numpy()
    mrrs = rr - medrr
    mrrs[mrrs < 0] = mrrs[mrrs < 0] * 2
    # Normalize by threshold.
    th2 = compute_threshold(mrrs, alpha, window_width)
    mrrs /= th2

    # Artifact classification #################################################
    ###########################################################################

    # Artifact classes.
    extra_idcs = []
    missed_idcs = []
    ectopic_idcs = []
    longshort_idcs = []

    i = 0
    while i < rr.size - 2:    # The flow control is implemented based on Figure 1

        if np.abs(drrs[i]) <= 1:    # Figure 1
            i += 1
            continue
        eq1 = np.logical_and(drrs[i] > 1, s12[i] < (-c1 * drrs[i] - c2))    # Figure 2a
        eq2 = np.logical_and(drrs[i] < -1, s12[i] > (-c1 * drrs[i] + c2))    # Figure 2a

        if np.any([eq1, eq2]):
            # If any of the two equations is true.
            ectopic_idcs.append(i)
            i += 1
            continue
        # If none of the two equations is true.
        if ~np.any([np.abs(drrs[i]) > 1, np.abs(mrrs[i]) > 3]):    # Figure 1
            i += 1
            continue
        longshort_candidates = [i]
        # Check if the following beat also needs to be evaluated.
        if np.abs(drrs[i + 1]) < np.abs(drrs[i + 2]):
            longshort_candidates.append(i + 1)

        for j in longshort_candidates:
            # Long beat.
            eq3 = np.logical_and(drrs[j] > 1, s22[j] < -1)    # Figure 2b
            # Long or short.
            eq4 = np.abs(mrrs[j]) > 3    # Figure 1
            # Short beat.
            eq5 = np.logical_and(drrs[j] < -1, s22[j] > 1)    # Figure 2b

            if ~np.any([eq3, eq4, eq5]):
                # If none of the three equations is true: normal beat.
                i += 1
                continue
            # If any of the three equations is true: check for missing or extra
            # peaks.

            # Missing.
            eq6 = np.abs(rr[j] / 2 - medrr[j]) < th2[j]    # Figure 1
            # Extra.
            eq7 = np.abs(rr[j] + rr[j + 1] - medrr[j]) < th2[j]    # Figure 1

            # Check if extra.
            if np.all([eq5, eq7]):
                extra_idcs.append(j)
                i += 1
                continue
            # Check if missing.
            if np.all([eq3, eq6]):
                missed_idcs.append(j)
                i += 1
                continue
            # If neither classified as extra or missing, classify as "long or
            # short".
            longshort_idcs.append(j)
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
        peaks = _correct_extra(extra_idcs, peaks)
        # Update remaining indices.
        missed_idcs = update_indices(extra_idcs, missed_idcs, -1)
        ectopic_idcs = update_indices(extra_idcs, ectopic_idcs, -1)
        longshort_idcs = update_indices(extra_idcs, longshort_idcs, -1)

    # Add missing peaks.
    if missed_idcs:
        peaks = _correct_missed(missed_idcs, peaks)
        # Update remaining indices.
        ectopic_idcs = update_indices(missed_idcs, ectopic_idcs, 1)
        longshort_idcs = update_indices(missed_idcs, longshort_idcs, 1)

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
    # Calculate the position(s) of new beat(s). Make sure to not generate
    # negative indices. prev_peaks and next_peaks must have the same
    # number of elements.
    valid_idcs = missed_idcs > 1
    missed_idcs = missed_idcs[valid_idcs]
    prev_peaks = corrected_peaks[[i - 1 for i in missed_idcs]]
    next_peaks = corrected_peaks[missed_idcs]
    added_peaks = prev_peaks + (next_peaks - prev_peaks) / 2
    # Add the new peaks before the missed indices (see numpy docs).
    corrected_peaks = np.insert(corrected_peaks, missed_idcs, added_peaks)

    return corrected_peaks


def _correct_misaligned(misaligned_idcs, peaks):

    corrected_peaks = peaks.copy()
    misaligned_idcs = np.array(misaligned_idcs)
    # Make sure to not generate negative indices, or indices that exceed
    # the total number of peaks. prev_peaks and next_peaks must have the
    # same number of elements.
    valid_idcs = np.logical_and(misaligned_idcs > 1,
                                misaligned_idcs < (len(corrected_peaks) - 1))
    misaligned_idcs = misaligned_idcs[valid_idcs]
    prev_peaks = corrected_peaks[[i - 1 for i in misaligned_idcs]]
    next_peaks = corrected_peaks[[i + 1 for i in misaligned_idcs]]
    half_ibi = (next_peaks - prev_peaks) / 2
    peaks_interp = prev_peaks + half_ibi
    # Shift the R-peaks from the old to the new position.
    corrected_peaks = np.delete(corrected_peaks, misaligned_idcs)
    corrected_peaks = np.concatenate((corrected_peaks,
                                      peaks_interp)).astype(int)
    corrected_peaks.sort(kind="mergesort")

    return corrected_peaks
