# module for functions used in the python bfastmonitor GPU
import base64
import copy

import folium
from folium.plugins import FloatImage

import json

from matplotlib import cm
import matplotlib.pyplot as plt
import matplotlib as mpl

import numpy as np
import os
from osgeo import gdal
from PIL import Image

from time_series import Timeseries

def set_base_output_dir(chooser):

    '''takes an ipywidget chooser as input, creates the base output directory, and returns it
    
    input:
    chooser(ipy widget)
    
    output:
    save_location(string)
    '''
    
    if not chooser.result:
        print("Defaulting to output directory name: stored_time_series/output")
        save_location = "stored_time_series/output"
        if not os.path.exists(save_location):
            os.makedirs(save_location)
        return(save_location)
    else:
        print("Output directory name:", "stored_time_series/" + chooser.result)
        save_location = "stored_time_series/" + chooser.result
        if not os.path.exists(save_location):
            os.makedirs(save_location)
        return(save_location)
    
def set_output_dir(chooser, timeseries_dir):

    '''
    Takes an ipywidget chooser and the timeseries directory as input.
    Creates output directories based on which timeseries directory you are in, and returns it
    
    input:
    chooser(ipy widget)
    timeseries_dir(string)
    
    output:
    save_location(string)
    '''
    
    if not chooser.result:
        save_location = "stored_time_series/output/" + timeseries_dir[-2]
    else:    
        save_location = "stored_time_series/" +  chooser.result + "/" + timeseries_dir[-2]
        
    if not os.path.exists(save_location):
            os.makedirs(save_location)
    return(save_location)

def set_paths(timeseries_directory,save_location=None,check_existing=False):

    '''
    Takes the timeseries directory path and creates Timeseries wrapper classes for every tile in the dir. 
    Set check_existing to True if your run crashed
    Returns a list of the Timeseries classes tiles
    
    
    
    input:
    timeseries_directory(string)
    check_existing(bool)
    output:
    data_list(list), holds Timeseries class tiles
    
    '''
    
    dates_path = os.path.join(timeseries_directory, "dates.csv")
    data_list=[]
    tile_paths = []
    
    # check for tiles
    file_list = os.listdir(timeseries_directory)
    file_list.sort()
    for file in file_list:
        if file.startswith('tile'):
            time_series_path =  timeseries_directory + file + "/"
            
            if check_existing == False:
                tile_paths.append(time_series_path)
            else:
                output_path = file + "_meta_data.txt"
                
                if os.path.exists(save_location):
                    if output_path in os.listdir(save_location):
                        print("output for "+ file + " already found, skipping")
                        skipped_files=True
                    else:
                        tile_paths.append(time_series_path)
                else:
                    tile_paths.append(time_series_path)

    # Create Timeseries wrapper for every tile
    if not tile_paths and skipped_files == False:
        print("No tiles, setting up data as one tile")
        ts_data = Timeseries(timeseries_directory, dates_path)
        data_list.append(ts_data)
    else:
        print("Data consists of tiles, setting up tiles in 'data_list' ")
        for time_series_path in tile_paths:
            
            #print("time_series_path" + time_series_path)
            ts_data = Timeseries(time_series_path, dates_path)
            data_list.append(ts_data)
    return data_list
            

def get_data_dict(time_series_path):

    '''Deprecated'''
    tile_dict = {}
    
    time_series = gdal.Open(time_series_path)
    tile_dict["name"] = time_series_path
    geotransform = time_series.GetGeoTransform()
    tile_dict["xpixelsize"] = geotransform[1]
    tile_dict['ypixelsize'] = geotransform[5]
    tile_dict["latitude"] = geotransform[3]
    tile_dict["longitude"] = geotransform[0]
    tile_dict['ncols'] = time_series.RasterXSize
    tile_dict["nrows"] = time_series.RasterYSize
    tile_dict['projection'] = time_series.GetProjection()
    tile_dict["raster_stack"] = time_series.ReadAsArray()
    return(tile_dict)

def _find_index_date(dates, t):
    
    
    '''Returns the index of the first date larger than t'''
    
    for i in range(len(dates)):
        if t < dates[i]:
            return i
    
    return len(dates)
                
def merge_tiles(tile_list, output_dir_name = 'my_data'):
    
    '''Merges the data_list of Timeseries classes tiles, saves and returns them
    
    input:
    tile_list(list)
    output_dir_name(string)
    
    output(all arrays):
    big_means_array 
    big_breaks_array
    
    '''
    
    x_locs = []
    y_locs = []
    x_tiles = []
    y_tiles = []
    data_list = tile_list
    
    for tile in data_list:
        loc_index = tile.dir.find("tile-")
        tile_loc = tile.dir[loc_index+5:-1].split("-")
        
        if tile_loc[1] not in x_locs:
            x_locs.append(tile_loc[1])
            x_tiles.append(tile)
        else:
            x_locs = []
            x_locs.append(tile_loc[1])
            y_tiles.append(x_tiles)
            x_tiles = []
            x_tiles.append(tile)
    y_tiles.append(x_tiles)
            
    firstx=True

    for tile_list in y_tiles:
        firsty = True

        for tile in tile_list:
            if firsty == True:
                means_array = tile.means_array
                breaks_array = tile.breaks_array
                firsty = False
            else:
                means_array = np.concatenate((means_array, tile.means_array), axis = 1)
                breaks_array = np.concatenate((breaks_array, tile.breaks_array), axis = 1)

        if firstx==True:
            big_means_array = means_array
            big_breaks_array = breaks_array
            firstx=False
        else:
            big_means_array = np.concatenate((big_means_array, means_array),axis = 0)
            big_breaks_array = np.concatenate((big_breaks_array, breaks_array),axis = 0)
    
        save_location = output_dir_name + "/numpy_arrays"
    
    if not os.path.exists(save_location):
        os.makedirs(save_location)
    
    save_means_dir = save_location + "/magnitudes.npy"
    save_breaks_dir = save_location + "/breaks.npy"
    print(save_means_dir)
    print(save_breaks_dir)
    np.save(save_means_dir, big_means_array)
    np.save(save_breaks_dir, big_breaks_array)

    print("arrays saved in " +  save_location)
    return(big_means_array, big_breaks_array)

def normalize(array): 

    '''Normalizes an array
    
    input and output: array (array)
    '''
    
    max_n = np.nanmax(array)
    min_n = np.nanmin(array)
    array = (array - min_n)/(max_n - min_n)
    return(array)


def get_julian_dates(dates_array, breaks_array):
    
    '''Calculates julian dates from index and dates arrays
    
    input(all arrays)
    dates_array
    breaks_array
    
    output:
    breaks_array (array)
    
    '''
    
    years_array = copy.deepcopy(breaks_array)
    for i in range(len(dates_array)):
        date = dates_array[i]
        tt = date.timetuple()
        julian_date = tt.tm_year * 1000 + tt.tm_yday
        year_date = tt.tm_year
        breaks_array[breaks_array == i] = julian_date
        years_array[years_array == i] = year_date
        
    return(breaks_array, years_array)


def select_negatives(means,breaks):
    
    '''Takes means and breaks and returns specific arrays:
    
    input (all arrays):
    means 
    breaks 
    
    output (all arrays):
    
    means: magnitudes but only negatives
    breaks: all index breaks
    breaks_neg: all index breaks of negative magnitudes
    binary_breaks: binary output of break presence
    negative_binary_breaks: binary output of negative break presence'''
    
    no_breaks_indices = (breaks == -1) # no -2 used by fabian
    no_break_lacking_data_indices = (breaks == -2) 
    means[no_breaks_indices] = np.nan
    means[no_break_lacking_data_indices] = np.nan
    means[means > 0] = 0 # only want negative mean changes

    breaks = breaks.astype(np.float)
    breaks[breaks == -2] = np.nan
    breaks[breaks == -1] = np.nan
    
    binary_breaks = np.invert(np.isnan(breaks))
    breaks_neg = copy.deepcopy(breaks)
    breaks_neg[means >= 0] = np.nan
    negative_binary_breaks = np.invert(np.isnan(breaks_neg))
    
    means[means == 0] = np.nan
    return(means, breaks, breaks_neg, binary_breaks, negative_binary_breaks)

