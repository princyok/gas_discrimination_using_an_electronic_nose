"""
@author: Prince Okoli
"""
import numpy as np

def segment_and_resample(data, segment_dur, index_time_field, enforce_contiguity=False):
    """
    Resample time series data via averaging of equal-duration segments.
    
    Parameters
    ----------
    data :
         A 2D `np.ndarray` instance.
         
    segment_dur :
        Duration (in same unit and format as the time in  the`data`) of each segment. 
        E.g. if 5 seconds, then all values in each 5-second segment will be resampled to 1.
        
    index_time_field :
        Index of the time field in the data. The time field must be in axis 1 (column) of the data.

    `enforce_contiguity`: Boolean.
        Whether to ignore time gaps in the input `data` that are greater than 
        the specified `segment_dur`. If False, ignore. The default is False.
    
    Returns
    -------
    Resampled `np.ndarray`.

    """
    resampled_data = []
    mean_abs_dev_resampled_data = []
    
    len_data=len(data)
    start_ind = 0
    while(start_ind < len_data):
        # generate a mask for the segment and extract the segment.
        segment_mask = (data[:, index_time_field] < data[start_ind, index_time_field]+segment_dur)
        segment_mask[:start_ind] = False
        segment = data[segment_mask]
       
        # update start index for the next segment.
        start_ind += segment.shape[0]
        
        if (enforce_contiguity==True) and (start_ind < len_data):
            # time difference between end of segment and start of next.
            time_diff = data[start_ind, index_time_field] - segment[-1, index_time_field]             
            # verify time difference is not larger than the specified segment duration.
            if  time_diff >= segment_dur:
                msg = "The gap in time between index "+ str(start_ind-1) + " and " + \
                    str(start_ind) + \
                    " is greater than the specified segment duration. " + \
                        "Set enforce_contiguity to False to bypass this check."
                raise ValueError(msg)
        
        # average all values in the selected segment and designate that the resampled value.        
        resampled_val = np.mean(segment, axis=0)
        resampled_data.append(resampled_val)
        
        # calculate the variability (mean abs deviation) associated with each resampled value.
        mean_abs_dev = np.mean(np.abs(segment - resampled_val), axis=0)
        mean_abs_dev_resampled_data.append(mean_abs_dev)
    return np.array(resampled_data), np.array(mean_abs_dev_resampled_data)

#%%
def fold_into_overlapping_sequences(data, seq_len, fields_to_zero_tare=None):
    """
    Formal Parameters
    -----------------
    `data`: 
        A 2D `np.ndarray` instance, where first axis tracks steps (not yet grouped into sequences).
    
    `seq_len`: 
        length of sequence. All sequences will have same length.
    
    `fields_to_zero_tare`: list, tuple, array-like. 
        Specifies which fields to tare to zero for all sequences. Must have
        same number of axes as data. E.g. To tare field 4 of 
        axis 1, use `[None, 4]`.
        
    Returns
    -----------------
    A numpy array that has the shape: (number of sequences, seq_len, outer axis of original).
    
    Note that the length of the first axis of the original data is equal to the length of 
    the reshaped data plus the `seq_len` minus 1.
    """

    new_data = []
    
    end_index_inp = data.shape[0]+1 
        
    for i in range(seq_len, end_index_inp):
        indices = range(i-seq_len, i)
        seq = data[indices]
        
        if fields_to_zero_tare is not None:
            # prepare the object to be used for indexing and 
            # also make a copy (`temp`), except with its first element as 0.
            fields_to_zero_tare = list(fields_to_zero_tare)
            temp=[]
            for i, ind in enumerate(fields_to_zero_tare):
                if ind is None:
                    # slice(None) is equivalent to colon in numpy indexing.
                    fields_to_zero_tare[i]=slice(None)
                if i == 0:
                    temp.append(i)
                else:
                    temp.append(ind)
            # select the first value as the tare value.
            loc_first_elem_seq = tuple(temp)
            tare = seq[loc_first_elem_seq]
            # apply the tare value.
            fields_to_zero_tare = tuple(fields_to_zero_tare)
            seq[fields_to_zero_tare]=seq[fields_to_zero_tare]-tare
            
        new_data.append(seq)
    return np.array(new_data)
#%%
class MinMaxRescaler:
    def __init__(self):
        self.old_min = None
        self.new_min = None
        self.old_max = None
        self.new_max = None
        self.is_initialized = False    
    def rescale(self, data, old_range, new_range=[0, 1]):
        """
        Rescales data.

        Parameters
        ----------
        data : 
            A `pd.Datafarame` or a 2D `np.ndarray`.
            
        old_range : 
            list or tuple of two numbers or two `np.ndarray`. The first element 
            must be the minimum values and the second is the maximum values.
            
        new_range : TYPE, optional
            list or tuple of two numbers or two `np.ndarray`. The first element 
            must be the minimum values and the second is the maximum values. 
            The default is [0, 1].

        Returns
        -------
        rescaled_data : TYPE
            The rescaled data. Same data type as input (`pd.Datafarame` or `np.ndarray`).
        """
        self.old_min, self.old_max = old_range
        self.new_min, self.new_max = new_range
        rescaled_data = ((self.new_max-self.new_min)*
                         ((data-self.old_min)/(self.old_max-self.old_min)))+self.new_min
        self.is_initialized = True
        return rescaled_data
    def reverse_scale(self, data):
        if self.is_initialized ==  False:
            raise ValueError("The ranges have not been initialized.")
        rescaled_data = self.rescale(data, old_range = [self.new_min, self.new_max], 
                     new_range=[self.old_min, self.old_max])
        return rescaled_data