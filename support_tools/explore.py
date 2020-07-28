"""
@author: Prince Okoli
"""

import pandas as pd
import numpy as np

def local_periodicity(df):
    """
    Generate the local periodicity of each datapoint. Local periodicity is the time gap between 
    a given datapoint and the next.
    
    Parameters
    ----------
    df :
        a `pd.DataFrame` instance with columns named "id" and "time", among possibly others.
    Returns
    -------
    a `pd.DataFrame` instance with only three columns named "id", "time" and "local_periodicity".
    The row index from the original argument `df` is maintained.
    """
    all_local_p = pd.DataFrame()
    all_ids = df.loc[:, "id"].unique()
    for id_ in all_ids:
        mask_id = (df["id"]==id_)
        # difference between each timestamp and the next.
        shift_down = 1
        dt = df.loc[mask_id, "time"].diff(periods=shift_down)
        dt.name="local_periodicity"
        # Ensure each time value retains its original row index;
        # Prepend NaN to the index and drop the last element. NaN value will have NaN index.
        orig_index = np.concatenate([[np.NaN], dt.index.to_numpy()[:-shift_down]])
        
        temp = [pd.DataFrame(np.repeat(id_, len(dt.index)), columns=["id"], index = orig_index),
                df.loc[mask_id, "time"].shift(periods=shift_down).set_axis(orig_index, axis = 0, inplace=False),
                dt.set_axis(orig_index, axis=0, inplace=False)]
        
        local_periodicity = pd.concat(temp, axis=1)
        all_local_p = all_local_p.append(local_periodicity)
    all_local_p.dropna(inplace=True)
    # reset dtype of the index to int. NaN may have forced an upcast to float.
    all_local_p.set_axis(all_local_p.index.astype("int"), inplace= True)
    return all_local_p

def get_all_contiguous_spans(data, largest_acceptable_gap):
    """
    Generate information (starting row index, start-time, and duration) for a span 
    of the time series deemed to be contigous. A segment of the time series is 
    deemed contiguous if the gap between each timestamp and the next (local periodicity) is less than 
    the specified `largest_acceptable_gap`.
    
    Parameters
    ----------
    data :
        A `pd.DataFrame` with columns named "id" and "time", among possibly others.
    largest_acceptable_gap :
        The largest gap in time to not consider a break in the timeseries. 
        Must be in the same unit and format as the time field in `data`.

    Returns
    -------
    all_contiguous_spans:
        A `pd.DataFrame` holding info of all contiguous spans.

    """
    # Get all local periodicity and mask.
    
    all_local_p = local_periodicity(df=data)
    mask = all_local_p["local_periodicity"]>largest_acceptable_gap

    # get the starting index of all contigous spans.
    
    columns = ["id", "start_index", "end_index", "start_time", "end_time", "duration"]
    all_contiguous_spans = pd.DataFrame(columns=columns)
    ## Undo the automatic alphabethical sorting of columns.
    all_contiguous_spans = all_contiguous_spans[columns]
    
    all_contiguous_spans["id"] = all_local_p.loc[mask,"id"] # retains original index
    
    ## Set the starting index of all contigous spans except the first for each id.
    all_contiguous_spans["start_index"] = all_local_p.loc[mask,:].index + 1
    ## Plus 1 is because the spans starts after the datapoint with the 
    ## unacceptable local periodicity.
    
    ## Include the starting index for the first contiguous span of each id.
    ## This is same as the starting index of each id.
    all_ids = data.loc[:, "id"].unique()
    for id_ in all_ids:
        start_index = data.loc[(data["id"]==id_), "id"].index[0]
        # Build a one-row df.
        temp = [[id_, start_index]+([np.NaN]*4)]
        first_contiguous_span = pd.DataFrame(temp, columns=columns, index = [start_index])
        
        all_contiguous_spans = all_contiguous_spans.append(first_contiguous_span)
        
    all_contiguous_spans.set_axis(all_contiguous_spans["start_index"].to_numpy(), 
                                  inplace=True, axis=0)  
    all_contiguous_spans.sort_values(by="start_index", inplace=True)

    # Include the start time of all contiguous spans.
    
    locs_start_times = all_contiguous_spans["start_index"].to_numpy()
    all_contiguous_spans["start_time"] = all_local_p.loc[locs_start_times, "time"].to_numpy()    
    
    # Include the end index of all contiguous spans.  
    
    for id_ in all_contiguous_spans["id"].unique():
        
        # Get the end index for all spans of the id except the last.
        mask_id = (all_contiguous_spans["id"]==id_)
        end_ind_span = all_contiguous_spans.loc[mask_id, "start_index"]-1
        
        all_contiguous_spans.loc[mask_id, "end_index"] = end_ind_span.shift(-1)
        
        # Get the end index of the last span of the id. 
        # This is also the end index of the id.
        end_index_last = data.loc[(data["id"]==id_), "id"].index[-1]
        ## Get the start index of the last span.
        start_index_last = all_contiguous_spans.loc[mask_id, :].index[-1]
        ## Input the end index the last span.
        all_contiguous_spans.loc[start_index_last, "end_index"] =  end_index_last
        
    # Include the end time of the span.
    
    locs_end_times = all_contiguous_spans["end_index"].to_numpy()
    all_contiguous_spans["end_time"] = data.loc[locs_end_times, "time"].to_numpy()           
    
    # Include duration of the contiguous span.   
     
    all_contiguous_spans["duration"] = \
        all_contiguous_spans["end_time"] - all_contiguous_spans["start_time"]
    
    # Ensure dtype of the index is int.
    all_contiguous_spans.set_axis(all_contiguous_spans.index.astype("int"), inplace= True)
    return all_contiguous_spans