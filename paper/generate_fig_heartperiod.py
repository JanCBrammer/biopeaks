# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from biopeaks import heart
from matplotlib.patches import FancyArrowPatch
from matplotlib import rc

# make all text bold
rc('font', weight='bold')

sfreq = 100

signal = np.ravel(pd.read_csv("ecg_snippet.tsv", sep="\t"))

peaks = heart.ecg_peaks(signal, sfreq)

period, _ = heart.heart_stats(peaks, sfreq, signal.size)

minsignal = min(signal)
maxsignal = max(signal)

fig, (ax0, ax1) = plt.subplots(nrows=2, ncols=1, figsize=(7.2, 4.45))

fig.subplots_adjust(hspace=.05)

ax0td = ax0.transData
ax1td = ax1.transData
figtf = fig.transFigure
figtf_inv = figtf.inverted()

ax0.set_frame_on(False)
ax0.set_axis_off()
ax1.set_frame_on(False)

ax0.plot(signal, linewidth=2.5, label="ECG")
ax0.vlines(peaks, ymin=minsignal, ymax=maxsignal, colors="deeppink",
           label="R-peaks", linewidth=3)
ax0.legend(bbox_to_anchor=(0.1, 1.1), fontsize="small")

ax1.plot(period, linewidth=2.5, c="mediumvioletred")
ax1.vlines(peaks, ymin=min(period), ymax=max(period), colors="deeppink",
           linewidth=3, alpha=.2)
ax1.grid(True, axis="y", alpha=.2)
ax1.set_xlabel("Seconds", fontsize="large", fontweight="bold")
ax1.set_ylabel("Heart period (sec)", fontsize="large", fontweight="bold")
sec = np.rint((ax1.get_xticks() / sfreq)).astype(int)
ax1.set_xticklabels(sec)
ax1.tick_params(axis="both", which="major", labelsize="medium")

ax0.text(ax0.get_xbound()[-1], ax0.get_ybound()[-1], "A", fontsize="large",
         fontweight="medium")
ax1.text(ax1.get_xbound()[-1], ax1.get_ybound()[-1], "B", fontsize="large",
         fontweight="medium")

fig.canvas.draw()    # important to synchronize transData of axes

for i in np.arange(1, peaks.size):

    text_base = peaks[i] - ((peaks[i] - peaks[i - 1]) * .5)
    ax0.text(text_base, maxsignal + 40, f"{period[peaks[i]]:.2f}", ha="center",
             fontsize="medium")

    period_beg = figtf_inv.transform(ax0td.transform((peaks[i - 1],
                                                      maxsignal)))
    period_end = figtf_inv.transform(ax0td.transform((peaks[i], maxsignal)))
    period_arrow = FancyArrowPatch(period_beg, period_end, transform=figtf,
                                   arrowstyle="<->", mutation_scale=10,
                                   color="k")
    fig.patches.append(period_arrow)

    arrow_base = figtf_inv.transform(ax0td.transform((text_base, maxsignal)))
    arrow_head = figtf_inv.transform(ax1td.transform((peaks[i],
                                                      period[peaks[i]])))
    arrow = FancyArrowPatch(arrow_base, arrow_head, transform=figtf,
                            arrowstyle="->", mutation_scale=10, color="k")
    fig.patches.append(arrow)

plt.savefig("fig_heartperiod.png", dpi=600, transparent=False,
            bbox_inches="tight")    # tight to remove extra whitespace around figure
plt.show()
