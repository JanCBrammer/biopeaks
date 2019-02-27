# -*- coding: utf-8 -*-
"""
Created on Thu Dec 20 11:23:25 2018

@author: U117148
"""

import numpy as np
import pandas as pd
import scipy as sp
import matplotlib.pyplot as plt
from scipy.signal import welch, medfilt, argrelextrema, find_peaks, peak_prominences, hilbert
from filters import butter_bandpass_filter, butter_lowpass_filter
from sklearn.cluster import KMeans, SpectralClustering, DBSCAN
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.svm import LinearSVC, SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KernelDensity
import seaborn as sns


def peaks_signal_dev(signal, sfreq):
    
    signal_filt = butter_bandpass_filter(signal,
                                         .8,
                                         30,
                                         sfreq,
                                         order=3)    

    # build features for clustering
    
    # select only positive peaks
    peaks = argrelextrema(signal_filt, np.greater)[0]
    
    # first feature is simply amplitude of peaks (attenuate outliers with log10), in order to be able to use log, make all values positive 
    height = np.log10(signal_filt[peaks] + 2 * np.abs(min(signal_filt[peaks])))
    
    # second feature is surrounding slope:
    # for each peak p, get the average slope (absolute value) of the PPG in a window beginning at the peak preceding p, extending to the peak following p
    slope = np.zeros(np.size(peaks))
    firstdiff = np.abs(np.diff(signal_filt))
    for p in range(np.size(peaks)):
        
        if p == 0:
            rightpeak = peaks[p+1]
            slope[p] = np.mean(firstdiff[peaks[p]:rightpeak])
        elif p == np.size(peaks)-1:
            leftpeak = peaks[p-1]
            slope[p] = np.mean(firstdiff[leftpeak:peaks[p]])
        elif 0 < p < np.size(peaks)-1:
            leftpeak = peaks[p-1]
            rightpeak = peaks[p+1]
            slope[p] = np.mean(firstdiff[leftpeak:rightpeak])
     
    # the third feature is prominence, basically how much does the peak stand out compared to its immediate neighbours
    prominence = peak_prominences(signal_filt, peaks)[0]
    
    # combine features
    features = np.column_stack((height,
                                prominence,
                                slope))
        
    # scale features
    scaler = MinMaxScaler()
    features = scaler.fit_transform(features)
    
    # reduce dimensionality features
    pca = PCA(n_components=2, svd_solver='full')
    features = pca.fit_transform(features)
    
    
    # remove outliers (only highcut needed)
    for f in range(features.shape[1]):
        
        feature = features[:, f]
        meanf = np.mean(feature)
        stdf = np.std(feature)
        cut = meanf + 3 * stdf
        outliers = np.where(feature > cut)[0]
        # remove outliers from all arrays that are (potentially) used in the following
        features = np.delete(features, outliers, axis=0)
        height = np.delete(height, outliers)
        slope = np.delete(slope, outliers)
        prominence = np.delete(prominence, outliers)
        peaks = np.delete(peaks, outliers)
    
    kde = KernelDensity(bandwidth=0.06, kernel='gaussian')
    kde.fit(height.reshape(-1, 1))
    x_d = np.linspace(min(height)-np.std(height), max(height)+np.std(height), 1000)
    logprob = kde.score_samples(x_d.reshape(-1, 1))
    
    kdepeaks = find_peaks(logprob)[0]
    n_components = np.size(kdepeaks)


    # use clustering to identify peaks, initialize means with kmeans clustering, this gives clear separation with margin (no enclosed cases) and then fine-tune with GMM to detect irregularities; i.e. best of both worlds
    clustering = GaussianMixture(n_components=n_components,
                                 random_state=42,
                                 covariance_type='full',
                                 init_params='kmeans',
                                 tol=1e-3,
                                 reg_covar=1e-4)
    clustering.fit(features)
    labels = clustering.predict(features)

#    if n_components > 1:
#        # now use regularized supervised classification to get a less overfitted decision boundary in case of more than one class   
#        clf = SVC(C=1)
#        clf.fit(features, labels)
#        labels = clf.predict(features)
    
    
    label_counts = np.unique(labels, return_counts=True)
    
    # selecting the cluster containing the peaks based on height works only in absence of outliers
    medheight = []
    for i in label_counts[0]:
        
        height_i = height[labels == i]
        medheight_i = np.median(height_i)
        medheight = np.append(medheight, medheight_i)
    
    peak_label = np.argmax(medheight)
    peak_label_idcs = np.where(labels == peak_label)[0]
    selected_peaks = peaks[peak_label_idcs]

    plt.figure()
    plt.subplot(1,3,1)
    plt.scatter(features[:, 0], features[:, 1])
    plt.scatter(features[peak_label_idcs, 0], features[peak_label_idcs, 1], c='g')
   
#    plt.subplot(1,2,2)
#    sns.kdeplot(features[:, 0], features[:, 1], bw=0.35)
#    plt.subplot(1,3,2)
#    plt.plot(logprob)
#    plt.scatter(n_heights, np.exp(logprob)[n_heights])    
#    plt.fill_between(x_d1, np.exp(logprob1), alpha=0.5)
    
    plt.subplot(1,3,2)
#    plt.plot(logprob)
#    plt.scatter(kdepeaks, np.exp(logprob)[kdepeaks])    
    plt.fill_between(x_d, np.exp(logprob), alpha=0.5)
    
#    sns.jointplot(x=feat1, y=feat2, data=pd.DataFrame(features))

    plt.subplot(1,3,3)
    plt.plot(signal_filt)
    
    # now, for each pair of peaks, check if they're closer than 0.5 * the estimated IBI from each other,
    # if this is the case, first check if both of the peaks are members of the labeled cluster,
    # if this is not the case throw the unlabeled peak out; if both peaks are members of the labeled cluster,
    # throw out the one that has the lowest probability of belonging to the cluster
    
#    probability = probability[peak_label_idcs, peak_label]    # select the probabilities associated with each labeled peak
#    n_peaks = np.size(selected_peaks)
#    ibi_est = np.median(np.sort(np.diff(selected_peaks))[n_peaks / 2:])    # estimate this from labeled peaks, since frequency estimate can be wrong
#    remove_p = []
#    
#    for p in np.arange(1, np.size(selected_peaks)):
#        
#        pair = selected_peaks[p-1:p+1]
#        peakdiff = np.diff(pair)
#        
#        if peakdiff < .6 * ibi_est:
#            
#            prob = probability[np.in1d(peaks[peak_label_idcs], pair)]    # select the probabilities associated with these labeled peaks
#            
#            if len(np.unique(prob)) == 1:    # if both are equally likely to be labeled as peaks correctly
#                continue    # keep both
#            
#            else:
#                remove = np.argmin(prob)
#                remove_p = np.append(remove_p, [p-1, p][remove])
#                remove_p = np.unique(remove_p.astype(int))
#         
#    fppeaks = selected_peaks[remove_p]
#    selected_peaks = np.delete(selected_peaks, remove_p)
            
    plt.scatter(selected_peaks, signal_filt[selected_peaks], c='g')
#    plt.scatter(fppeaks, signal[fppeaks], c='r')

#    return selected_peaks
    


def peaks_signal(signal, sfreq):
    
    N = np.size(signal)
    
    signal_filt = butter_bandpass_filter(signal,
                                         .8,
                                         30,
                                         sfreq,
                                         order=3)    

    # build features for clustering
    
    # select only positive peaks that exceed zero
    peaks = argrelextrema(signal_filt, np.greater)[0]
    peaks = np.intersect1d(peaks, np.where(signal_filt > 0)[0])
    peaks = peaks.astype(int)
    
    # first feature is simply amplitude of peaks
    height = signal_filt[peaks]
    
    # second feature is surrounding slope:
    # for each peak p, get the average slope (absolute value) of the ECGs slope from preceding peaks to p and from p to subsequent peak
    slope = np.zeros(np.size(peaks))
    firstdiff = np.abs(np.diff(signal_filt))
    for p in range(np.size(peaks)):
        
        if p == 0:
            rightpeak = peaks[p+1]
            slope[p] = np.mean(firstdiff[peaks[p]:rightpeak])
        elif p == np.size(peaks)-1:
            leftpeak = peaks[p-1]
            slope[p] = np.mean(firstdiff[leftpeak:peaks[p]])
        elif 0 < p < np.size(peaks)-1:
            leftpeak = peaks[p-1]
            rightpeak = peaks[p+1]
            slope[p] = np.mean(firstdiff[leftpeak:rightpeak])
     
    # the third feature is prominence, basically how much does the peak stand out compared to its immediate neighbours
    prominence = peak_prominences(signal_filt, peaks)[0]
    
    # the fourth feature is instantaneous frequency
    hilb = hilbert(signal_filt)
    # extract the phase angle time series
    instphase = np.angle(hilb)
    # frequency sliding is defined as the temporal derivative of the phase angle time series (using the sampling rate s and 2π to scale the result to frequencies in hertz)
    instfreq = (np.diff(np.unwrap(instphase)) / (2.0 * np.pi) * sfreq)
    instfreq = instfreq[peaks]
    
    # the fifth feature is the difference in amplitude of each peak to the standard deviation of the amplitude all peaks
    stddiff = signal_filt[peaks] - np.std(signal_filt[peaks])
    
    # combine features
    features = np.column_stack((height,
                                stddiff,
                                prominence,
                                instfreq,
                                slope))
        
    # scale features
    scaler = MinMaxScaler()
    features = scaler.fit_transform(features)
    
    # reduce dimensionality features
    pca = PCA(n_components=2, svd_solver='full')
    features = pca.fit_transform(features)
    
    
    # get an initial estimate of dominant heart rate and corresponding IBI
    # assume BPM ranging from 50 to 150
    fmin, fmax = .8, 2.5
    f, powden = welch(signal_filt**2, sfreq, nperseg=N)    # squaring is important, gives more accurate results!
    f_range = np.logical_and(f>=fmin, f<=fmax)
    f = f[f_range]
    powden = powden[f_range]
    pow_peaks = find_peaks(powden)[0]
    max_pow = pow_peaks[np.argmax(powden[pow_peaks])]
    freq_est = f[max_pow]
    
#    plt.figure()
#    plt.semilogy(f, powden)
#    plt.axvline(x=freq_est, c='r')
#    plt.xlim([fmin, fmax])
#    plt.ylim([min(powden[f < fmax]), max(powden[f < fmax])])
#    plt.xlabel('frequency [Hz]')
    
    # lenght data in seconds
    scds = N / sfreq
    # expected number of peaks over length of data in seconds
    expNpeaks = scds * freq_est
#    print expNpeaks
    
    # use clustering to identify peaks, initialize means with kmeans clustering, this gives clear separation with margin (no enclosed cases) and then fine-tune with GMM to detect irregularities; i.e. best of both worlds
    clustering = GaussianMixture(n_components=2,
                                 random_state=42,
                                 covariance_type='full',
                                 init_params='kmeans')
    clustering.fit(features)
    labels = clustering.predict(features)
    probability = clustering.predict_proba(features)
    
    
    label_counts = np.unique(labels, return_counts=True)
    # make sure these variables are calculated irrespective of number of labels
    diffexpNpeaks = 1 / (np.abs(label_counts[1] - expNpeaks) + 1)   # smaller difference results in larger value, + 1 to avoid potential division by zero
    
    medheight = []
    for i in label_counts[0]:
        
        height_i = height[labels == i]
        medheight_i = np.median(height_i)
        medheight = np.append(medheight, medheight_i)
    medheight = np.log10(medheight)    # give less weight to extreme values
    
    # diffexpNpeaks will be 1 if the difference is 0 and progressively smaller as the difference grows,
    # therefore, it gives progressively smaller weight to medheight as the difference increases
    criterion = medheight * diffexpNpeaks 
    
    peak_label = np.argmax(criterion)
    peak_label_idcs = np.where(labels == peak_label)[0]
    
    
    plt.figure()
    plt.subplot(1,2,1)
    plt.scatter(features[:, 0], features[:, 1])
    

    if ((min(np.abs(label_counts[1] - expNpeaks)) > 0.4 * expNpeaks) or 
        min(label_counts[1]) < .2 * max(label_counts[1])):
        # throw out potential false positives by cluster label (and then by probability if needed)
        selected_peaks = peaks
        
    else:
        selected_peaks = peaks[peak_label_idcs]
        # throw out potential false positives by probability
        
        plt.scatter(features[peak_label_idcs, 0], features[peak_label_idcs, 1], c='g')
    
    plt.subplot(1,2,2)
    plt.plot(signal)
        
        
    # now, for each pair of peaks, check if they're closer than 0.5 * the estimated IBI from each other,
    # if this is the case, first check if both of the peaks are members of the labeled cluster,
    # if this is not the case throw the unlabeled peak out; if both peaks are members of the labeled cluster,
    # throw out the one that has the lowest probability of belonging to the cluster
    
    probability = probability[peak_label_idcs, peak_label]    # select the probabilities associated with each labeled peak
    n_peaks = np.size(selected_peaks)
    ibi_est = np.median(np.sort(np.diff(selected_peaks))[n_peaks / 2:])    # estimate this from labeled peaks, since frequency estimate can be wrong
    remove_p = []
    
    for p in np.arange(1, np.size(selected_peaks)):
        
        pair = selected_peaks[p-1:p+1]
        peakdiff = np.diff(pair)
        
        if peakdiff < .6 * ibi_est:
            # check if any of the two peaks is not labeled, if so remove
            remove = np.in1d(pair, peaks[peak_label_idcs])    # returns [true, true] if both are labeled peaks etc.
            
            if np.all(remove):    # if all peaks are labeled
                prob = probability[np.in1d(peaks[peak_label_idcs], pair)]    # select the probabilities associated with these labeled peaks
                
                if len(np.unique(prob)) == 1:    # if both are equally likely to be labeled as peaks correctly
                    continue    # keep both
                
                else:
                    remove = np.argmin(prob)
                    remove_p = np.append(remove_p, [p-1, p][remove])
                    remove_p = np.unique(remove_p.astype(int))
            
            else:
                remove_p = np.append(remove_p, np.array([p-1, p])[~remove])
                remove_p = np.unique(remove_p.astype(int))

    fppeaks = selected_peaks[remove_p]
    selected_peaks = np.delete(selected_peaks, remove_p)
            
            
    
    plt.scatter(selected_peaks, signal[selected_peaks], c='g')
    plt.scatter(fppeaks, signal[fppeaks], c='r')


    return selected_peaks
