# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from biopeaks import resp
from matplotlib.patches import FancyArrowPatch
from matplotlib.lines import Line2D
from matplotlib import rc

# make all text bold
rc('font', weight='bold')

sfreq = 1000

signal = np.ravel(pd.read_csv("breathing_snippet.tsv", sep="\t"))[40685:87150]

extrema = resp.resp_extrema(signal, sfreq)
_, _, amp = resp.resp_stats(extrema, signal, sfreq)

peaks = extrema[1::2]
troughs = extrema[0::2]

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

ax0.plot(signal, linewidth=2.5, label="breathing signal")
ax0.scatter(peaks, signal[peaks], c="deeppink", marker="^", zorder=3, s=125,
            label="inhalation peaks")
ax0.scatter(troughs, signal[troughs], c="deeppink", marker="v", zorder=3,
            s=125, label="exhalation troughs")
ax0.legend(fontsize="small", markerscale=.75, bbox_to_anchor=(0.15, 1.1),
           handlelength=.6)

ax1.plot(amp, linewidth=2.5, c="mediumvioletred")
ax1.vlines(peaks, ymin=min(amp), ymax=max(amp), colors="deeppink", linewidth=3,
           alpha=.2)
ax1.grid(True, axis="y", alpha=.2)
ax1.set_xlabel("Time (sec)", fontsize="large", fontweight="bold")
ax1.set_ylabel("Inhalation amplitude (a.u.)", fontsize="large",
               fontweight="bold")

ax0.set_xlim(right=40000)
ax1.set_xlim(right=40000)

sec = np.rint((ax1.get_xticks() / sfreq)).astype(int)
ax1.set_xticklabels(sec)
ax1.tick_params(axis="both", which="major", labelsize="medium")

ax0.text(ax0.get_xbound()[-1], ax0.get_ybound()[-1], "a", fontsize="large",
         fontweight="medium")
ax1.text(ax1.get_xbound()[-1], ax1.get_ybound()[-1], "b", fontsize="large",
         fontweight="medium")

fig.canvas.draw()

for i in np.arange(0, peaks.size):

    halfamp = signal[troughs[i]] + .5 * (signal[peaks[i]] - signal[troughs[i]])
    ax0.text(peaks[i] + 300, halfamp, f"{amp[peaks[i]]:.0f}", va="center")

    ampmin = (peaks[i], signal[troughs[i]])
    ampmax = (peaks[i], signal[peaks[i]])
    amp_arrow = FancyArrowPatch(ampmin, ampmax, arrowstyle="<->",
                                mutation_scale=20, zorder=4, linewidth=2)
    ax0.add_patch(amp_arrow)

    troughline = Line2D([peaks[i], troughs[i]],
                        [signal[troughs[i]], signal[troughs[i]]],
                        linestyle=":", linewidth=2, c="k")
    ax0.add_line(troughline)

    arrow_head = figtf_inv.transform(ax1td.transform((peaks[i],
                                                      amp[peaks[i]])))
    arrow_base = figtf_inv.transform(ax0td.transform((peaks[i] + 1500,
                                                      halfamp - 20)))
    arrow = FancyArrowPatch(arrow_base, arrow_head, transform=figtf,
                            arrowstyle="->", mutation_scale=10, color="k",
                            connectionstyle="arc3,rad=-0.2")
    fig.patches.append(arrow)

plt.savefig("fig_breathingamplitude.svg", dpi=600, transparent=False,
            bbox_inches="tight")    # tight to remove extra whitespace around figure
plt.show()
