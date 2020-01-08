# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from scipy.signal import find_peaks, medfilt
from .filters import butter_highpass_filter
from .analysis_utils import (moving_average, threshold_normalization,
                             interp_stats, update_indices)


def ecg_peaks(signal, sfreq, smoothwindow=.1, avgwindow=.75,
              gradthreshweight=1.5, minlenweight=0.4, enable_plot=False):
    """
    enable_plot is for debugging and demonstration purposes when the function
    is called in isolation
    """
    # initiate plot
    if enable_plot:
        plt.figure()
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212, sharex=ax1)

    filt = butter_highpass_filter(signal, .5, sfreq)

    grad = np.gradient(filt)
    absgrad = np.abs(grad)
    smoothgrad = moving_average(absgrad, int(np.rint(smoothwindow * sfreq)))
    avggrad = moving_average(smoothgrad, int(np.rint(avgwindow * sfreq)))
    gradthreshold = gradthreshweight * avggrad
    mindelay = int(np.rint(sfreq * 0.3))

    # visualize thresholding
    if enable_plot:
        ax1.plot(filt)
        ax2.plot(smoothgrad)
        ax2.plot(gradthreshold)

    # identify start and end of QRS
    qrs = smoothgrad > gradthreshold
    beg_qrs = np.where(np.logical_and(np.logical_not(qrs[0:-1]), qrs[1:]))[0]
    end_qrs = np.where(np.logical_and(qrs[0:-1], np.logical_not(qrs[1:])))[0]
    # throw out QRS-ends that precede first QRS-start
    end_qrs = end_qrs[end_qrs > beg_qrs[0]]

    # identify R-peaks within QRS (ignore QRS that are too short)
    num_qrs = min(beg_qrs.size, end_qrs.size)
    min_len = np.mean(end_qrs[:num_qrs] - beg_qrs[:num_qrs]) * minlenweight
    peaks = [0]

    for i in range(num_qrs):

        beg = beg_qrs[i]
        end = end_qrs[i]
        len_qrs = end - beg

        if len_qrs < min_len:
            continue

        # visualize QRS intervals
        if enable_plot:
            ax2.axvspan(beg, end, facecolor="m", alpha=0.5)

        # find local maxima and their prominence within QRS
        data = signal[beg:end]
        locmax, props = find_peaks(data, prominence=(None, None))

        if locmax.size > 0:
            # identify most prominent local maximum
            peak = beg + locmax[np.argmax(props["prominences"])]
            # enforce minimum delay between peaks
            if peak - peaks[-1] > mindelay:
                peaks.append(peak)

    peaks.pop(0)

    if enable_plot:
        ax1.scatter(peaks, filt[peaks], c="r")

    return np.asarray(peaks).astype(int)


def ecg_cleanperiod(peaks, sfreq, return_artifacts=False, enable_plot=False):
    """
    implementation of Jukka A. Lipponen & Mika P. Tarvainen (2019): A robust
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
    rr[0] = np.mean(rr)

    # Compute differences of consecutive periods.
    drrs = np.ediff1d(rr, to_begin=0)
    drrs[0] = np.mean(drrs)
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

    # Cast drrs to two-dimensional subspace s2 (looping over d a second
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
    etopic_idcs = []
    longshort_idcs = []

    for i in range(peaks.size - 2):

        # Check for etopic peaks.
        if np.abs(drrs[i]) <= 1:
            continue

        # Based on Figure 2a.
        eq1 = np.logical_and(drrs[i] > 1, s12[i] < (-c1 * drrs[i] - c2))
        eq2 = np.logical_and(drrs[i] < -1, s12[i] > (-c1 * drrs[i] + c2))

        if np.any([eq1, eq2]):
            # If any of the two equations is true.
            etopic_idcs.append(i)
            continue

        # If none of the two equations is true.
        # Based on Figure 2b.
        if np.logical_or(np.abs(drrs[i]) > 1, np.abs(mrrs[i]) > 3):
            # Long beat.
            eq3 = np.logical_and(drrs[i] > 1, s22[i] < -1)
            eq4 = np.abs(mrrs[i]) > 3
            # Short beat.
            eq5 = np.logical_and(drrs[i] < -1, s22[i] > 1)

        if ~np.any([eq3, eq4, eq5]):
            # Of none of the three equations is true: normal beat.
            continue

        # If any of the three equations is true: check for missing or extra
        # peaks.

        # Missing.
        eq6 = np.abs(rr[i] / 2 - medrr[i]) < th2[i]
        # Extra.
        eq7 = np.abs(rr[i] + rr[i + 1] - medrr[i]) < th2[i]

        # Check if short or extra.
        if np.any([eq3, eq4]):
            if eq7:
                extra_idcs.append(i)
            else:
                longshort_idcs.append(i)
                if np.abs(drrs[i + 1]) < np.abs(drrs[i + 2]):
                    longshort_idcs.append(i + 1)
        # Check if long or missing.
        if eq5:
            if eq6:
                missed_idcs.append(i)
            else:
                longshort_idcs.append(i)
                if np.abs(drrs[i + 1]) < np.abs(drrs[i + 2]):
                    longshort_idcs.append(i + 1)

    if enable_plot:
        # Visualize artifact type indices.
        fig0, (ax0, ax1) = plt.subplots(nrows=2, ncols=1, sharex=True)
        ax0.plot(rr, label="heart period")
        ax0.scatter(longshort_idcs, rr[longshort_idcs], marker='v', c='m',
                    s=100, zorder=3, label="long/short")
        ax0.scatter(etopic_idcs, rr[etopic_idcs], marker='v', c='g', s=100,
                    zorder=3, label="etopic")
        ax0.scatter(extra_idcs, rr[extra_idcs], marker='v', c='y', s=100,
                    zorder=3, label="false positive")
        ax0.scatter(missed_idcs, rr[missed_idcs], marker='v', c='r', s=100,
                    zorder=3, label="false negative")
        ax0.legend(loc="upper right")

        # Visualize first threshold.
        ax1.plot(np.abs(drrs), label="difference consecutive heart periods")
        ax1.axhline(1, c='r', label="artifact threshold")
        ax1.legend(loc="upper right")

        # Visualize decision boundaries.
        fig2, (ax2, ax3) = plt.subplots(nrows=1, ncols=2)
        ax2.scatter(drrs, s12, marker="x", label="heart periods")
        x = np.linspace(min(drrs), max(drrs), 1000)
        verts0 = [(min(drrs), max(s12)),
                  (min(drrs), -c1 * min(drrs) - c2),
                  (-1, -c1 * -1 - c2),
                  (-1, max(s12))]
        poly0 = Polygon(verts0, alpha=0.3, facecolor="r", edgecolor=None,
                        label="etopic periods")
        ax2.add_patch(poly0)
        verts1 = [(1, -c1 * 1 + c2),
                  (1, min(s12)),
                  (max(drrs), min(s12)),
                  (max(drrs), -c1 * max(drrs) + c2)]
        poly1 = Polygon(verts1, alpha=0.3, facecolor="r", edgecolor=None)
        ax2.add_patch(poly1)
        ax2.legend(loc="upper right")

        ax3.scatter(drrs, s22, marker="x", label="heart periods")
        verts2 = [(min(drrs), max(s22)),
                  (min(drrs), 1),
                  (-1, 1),
                  (-1, max(s22))]
        poly2 = Polygon(verts2, alpha=0.3, facecolor="r", edgecolor=None,
                        label="short periods")
        ax3.add_patch(poly2)
        verts3 = [(1, -1),
                  (1, min(s22)),
                  (max(drrs), min(s22)),
                  (max(drrs), -1)]
        poly3 = Polygon(verts3, alpha=0.3, facecolor="y", edgecolor=None,
                        label="long periods")
        ax3.add_patch(poly3)
        ax3.legend(loc="upper right")


    # Artifact correction
    #####################
    # The integrity of indices must be maintained if peaks are inserted or
    # deleted: for each deleted beat, decrease indices following that beat in
    # all other index lists by 1; likewise, for each added beat, increment the
    # indices following that beat in all other lists by 1.

    # Delete extra peaks.
    if extra_idcs:
        peaks = np.delete(peaks, extra_idcs)
        # Re-calculate the RR series.
        rr = np.ediff1d(peaks, to_begin=0) / sfreq
#        print('extra: {}'.format(peaks[extra_idcs]))
        # Update remaining indices.
        missed_idcs = update_indices(extra_idcs, missed_idcs, -1)
        etopic_idcs = update_indices(extra_idcs, etopic_idcs, -1)
        longshort_idcs = update_indices(extra_idcs, longshort_idcs, -1)

    # Add missing peaks
    if missed_idcs:
        # Calculate the position(s) of new beat(s).
        prev_peaks = peaks[[i - 1 for i in missed_idcs]]
        next_peaks = peaks[missed_idcs]
        added_peaks = prev_peaks + (next_peaks - prev_peaks) / 2
        # Add the new peaks.
        peaks = np.insert(peaks, missed_idcs, added_peaks)
        # Re-calculate the RR series.
        rr = np.ediff1d(peaks, to_begin=0) / sfreq
#        print('missed: {}'.format(peaks[missed_idcs]))
        # Update remaining indices.
        etopic_idcs = update_indices(missed_idcs, etopic_idcs, 1)
        longshort_idcs = update_indices(missed_idcs, longshort_idcs, 1)

    # Interpolate etopic as well as long or short peaks (important to do this
    # after peaks are deleted and/or added).
    interp_idcs = np.concatenate((etopic_idcs, longshort_idcs)).astype(int)
    if interp_idcs.size > 0:
        interp_idcs.sort(kind='mergesort')
        # Ignore the artifacts during interpolation
        x = np.delete(np.arange(0, rr.size), interp_idcs)
        # Interpolate artifacts
        interp_artifacts = np.interp(interp_idcs, x, rr[x])
        rr[interp_idcs] = interp_artifacts
#        print('interpolated: {}'.format(peaks[interp_idcs]))

    # The rate corresponding to the first peak is set to the mean RR.
    rr[0] = np.mean(rr)

    if return_artifacts:
        artifacts = {"etopic": etopic_idcs, "missed": missed_idcs,
                     "extra": extra_idcs, "longshort": longshort_idcs}

        return peaks.astype(int), rr, artifacts
    else:
        return peaks.astype(int), rr


def ecg_period(peaks, sfreq, nsamp):

    # Get corrected peaks and normal-to-normal intervals
    peaks_clean, nn = ecg_cleanperiod(peaks, sfreq)

    # interpolate rr at the signals sampling rate for plotting
    periodintp = interp_stats(peaks_clean, nn, nsamp)
    rateintp = 60 / periodintp

    return peaks_clean, periodintp, rateintp
