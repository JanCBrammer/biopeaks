# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 10:14:36 2018

@author: U117148
"""

import numpy as np
import matplotlib.pyplot as plt

def rpeaks(signal, sfreq):

    def inflection_nonzero(signal):
        pos = signal > 0    # disregard indices where slope equals zero
        npos = ~pos
        return ((pos[:-1] & npos[1:]) | (npos[:-1] & pos[1:])).nonzero()[0]
    
    def sieving(signal, direction, center, extend):
        # direction: search to only right side of center ('right'), or search
        # on both sides of the center ('both')
        # center: center of search range
        # extend: extend of search range (unilaterally), expressed as fraction 
        # of paid
        
        sieve_range_pos = np.int(np.ceil(center + extend))
        sieve_range_neg = np.int(np.ceil(center - extend))
        
        if direction == 'right':
            candidate = signal[:,[i for i, element in enumerate(signal[1,:])
                            if element > sieve_range_pos]]
             
        elif direction == 'both':
            candidate = signal[:,[i for i, element in enumerate(signal[1,:])
                            if sieve_range_neg <= element <= sieve_range_pos]]
                    
        return candidate
            
    # set free parameters
    # in samples; sufficiently small such that no two R-peaks can occur in the
    # same window
    window_size = np.ceil(0.28 * sfreq)
    window_overlap = 2
    # amount of samples the window is shifted on each iteration
    stride = np.int(window_size - window_overlap)
    # weight for R-peak threshold for post-training phase  
    Rthreshold = 0.7 
    # determines after how many beats the parameters are adapted     
    pmax_adopt = 100 
    paid_adopt = 100 
    # duration training in seconds
    dur_train = 15    
    
    # initiate stuff
    training_data = np.zeros([2,1])
    bpm = [0]
    Rpeaks = []
    block = 0
    signal = np.ravel(signal)
    
    while block * stride + window_size <= len(signal):
        block_indices = np.arange(block * stride, block * stride + window_size, 
                                  dtype = int)
        
        x = signal[block_indices]
        
        first_diff = x[1:] - x[:-1]
    
        inflect = inflection_nonzero(first_diff)
        # first row: voltage, second row: index (timestamp), '+1' makes the
        # inflection point coincide with the actual peak, since
        # 'inflection_nonzero()' returns the index -1 to the actual peak
        candidateR = np.stack( (np.abs(x[inflect + 1] - np.median(x)), 
                                block_indices[inflect + 1] ))   
    
        if candidateR.shape[1] > 0:
        
            # training
            if block_indices[-1] <= dur_train * sfreq:
       
                training_data = np.column_stack([training_data, candidateR])
                
                trainingRthreshold = Rthreshold * np.max(training_data[0,:])
                above_threshold = training_data[0,:] > trainingRthreshold
                training_data = training_data[:, above_threshold]
                
                pmax = np.mean(training_data[0,:])
                # only consider those R-peaks that are not closer than 0.18 sec
                # to each other
                
                paid = np.median(np.diff(training_data[1,:])
                                [np.diff(training_data[1,:]) > 0.18 * sfreq])    
                
                # initiate Rpeaks for first post-training window
                Rpeaks = np.column_stack((np.zeros([2,1]),
                                          training_data[:,-1]))
            
            # post-training
            else:
                
                # exclude candidate peaks that are within 0.5*paid of last
                # detected peak
                sieve_a = sieving(candidateR, 'right', Rpeaks[1,-1], 0.5*paid)
               
                if sieve_a.shape[1] == 0: 
                    block += 1
                    continue
                
                elif sieve_a.shape[1] > 0:
                    
                    # exclude candidate peaks that are below threshold
                    pmaxR = sieve_a[:, sieve_a[0,:] >= pmax * Rthreshold]
                
                    if pmaxR.shape[1] == 0: 
                        block += 1
                        continue
                        
                    elif pmaxR.shape[1] == 1:
                        Rpeaks = np.column_stack([Rpeaks, pmaxR])
                    
                    elif pmaxR.shape[1] > 1: 
        
                        # give first priority to canidate peaks that are within
                        # -/+ 0.1 * paid of last detected peak + paid
                        sieve_b = sieving(pmaxR,
                                          'both',
                                          Rpeaks[1,-1]+paid,
                                          0.1*paid)
                        
                        if sieve_b.shape[1] > 0:
                            pmaxR = sieve_b[:,sieve_b[0,:].argmax()]
                            Rpeaks = np.column_stack([Rpeaks, pmaxR])
                        # if no peaks are found, extend the sieve range
                        else:
                            
                            # give second priority to canidate peaks that are
                            # within -/+ 0.2 * paid of last detected peak +
                            # paid
                            sieve_c = sieving(pmaxR,
                                              'both',
                                              Rpeaks[1,-1]+paid,
                                              0.2*paid)
                        
                            if sieve_c.shape[1] > 0:
                                pmaxR = sieve_c[:,sieve_c[0,:].argmax()]
                                Rpeaks = np.column_stack([Rpeaks, pmaxR])
                            else:    
                            
                                # give third priority to candidate peaks that
                                # are within -/+ 0.3 * paid of last detected
                                # peak + paid
                                sieve_d = sieving(pmaxR,
                                                  'both',
                                                  Rpeaks[1,-1]+paid,
                                                  0.3*paid)
                        
                                if sieve_d.shape[1] > 0:
                                    pmaxR = sieve_d[:,sieve_d[0,:].argmax()]
                                    Rpeaks = np.column_stack([Rpeaks, pmaxR])
                                else:   
                                    
                                   # ignore segment
                                   block += 1
                                   continue
        
                beatdiff = np.diff(Rpeaks[1,:])
                hrinst = np.int(60. / (beatdiff[-1]
                                                / sfreq))
                bpm.append(hrinst)
                
                # update parameters
                if np.mod(Rpeaks.shape[1], pmax_adopt) == 0:
                    pmax = np.mean(Rpeaks[0,:])
                    
                if np.mod(Rpeaks.shape[1], paid_adopt) == 0:
                    paid = np.median(np.abs(np.diff(Rpeaks[1,:])))
    
            block += 1
            
        else:
            block += 1
            continue
   
    return Rpeaks, bpm