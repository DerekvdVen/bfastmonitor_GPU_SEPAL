import os
from os.path import expanduser

import wget
import numpy as np
from datetime import datetime
import copy
import matplotlib
import matplotlib.pyplot as plt

import json

from bfast import BFASTMonitor
from bfast.utils import crop_data_dates

import csv
from shutil import copyfile
import pandas as pd
from osgeo import gdal, gdal_array, osr

import time
from tqdm import tqdm

import ipywidgets as widgets
from ipywidgets import Layout
from ipyfilechooser import FileChooser
import folium

from PIL import Image
from matplotlib import cm

# import functions from functions.py
from functions import set_base_output_dir, set_output_dir, get_data_dict, merge_tiles, set_paths, _find_index_date, normalize, select_negatives, get_julian_dates
from plotting_funcs import save_plot, merge_plots, classify_output, plot_output_matplotlib, set_corners, export_GTiff, classify_magnitudes

# Import the Timeseries class from time_series.py
from time_series import Timeseries
print(Timeseries.__doc__)

start = time.time()


import argparse
parser = argparse.ArgumentParser(description='set dirs')
parser.add_argument('-o', default="output", type=str, help='output name')
parser.add_argument('-t', default= None, type = str, help='where your timeseries is located')

args = parser.parse_args()

base_output_dir = "stored_time_series/" + args.o
timeseries_directory = args.t
if not timeseries_directory:
    raise Exception("Make sure to select your timeseries_directory with -t ../../downloads/[time_series], or -t home/yourusername/downloads/[time_series]")

# set path to dates file
run_dict = {}
for directory in os.listdir(timeseries_directory):
    
    segment_location = timeseries_directory + directory + "/"
    
    data_list = set_paths(timeseries_directory = segment_location)
    
    run_dict[directory] = data_list
    
    for tile in data_list:
        print(tile)
        

# Set parameters

dates = data_list[0].dates
start_date = dates[0].date()
end_date = dates[-1].date()

print("\n ### \n\nfill in dates,you must choose dates between: ", start_date, " and ", end_date, "\n")

start_monitor = str(input("start monitoring period yyyy-mm-dd: ")) #"2016-09-02"
end_monitor = str(input("end monitoring period yyyy-mm-dd, press enter to run till most recent data ") or end_date) #"2020-08-27"
start_history = str(input("start history period yyyy-mm-dd, press enter to use all data ") or start_date) #"2012-01-1"

#print("\n ### \n\n Give parameter input, press enter to resort to standard parameter. \n")
k = int(input("set k, harmonic term, choose 1,2,3,4,5 (default = 3):  ") or 3)
freq = int(input("set frequency of seasonal model in days (default = 365): ") or 365)
trend = bool(input("set trend True or False (default = False): ") or False)
hfrac =float(input(" set bandwidth relative to sample size (default = 0.25): ") or 0.25)
level = float(input("set level of significance 0.001 - 0.05 (default = 0.05): ") or 1-0.95)
backend = str(input("choose opencl or python (default = opencl): ") or 'opencl')
verbose = 1
device_id = 0

x_block = y_block = int(input("choose block size 128, 256, 512, 1024 (default = 512): ") or 512)

start_monitor = datetime.strptime(start_monitor, "%Y-%m-%d") 
end_monitor = datetime.strptime(end_monitor, "%Y-%m-%d") 
start_hist = datetime.strptime(start_history, "%Y-%m-%d") 



for data_list in run_dict:
    # loading bar
    with tqdm(total=len(run_dict)) as pbar1:
        
        
        save_location = base_output_dir + "/" + data_list
        if not os.path.exists(save_location):
            os.makedirs(save_location)
        

        # loop over tile(s) in the data_list
        for counter, tile in enumerate(run_dict[data_list]):
            pbar1.set_description("Processing tile %s out of %s" % (counter+1, len(run_dict[data_list])) )

            tile.set_bfast_parameters(start_monitor = start_monitor, 
                                         end_monitor = end_monitor,
                                         start_hist = start_hist,
                                         freq = freq,
                                         k = k,
                                         hfrac = hfrac,
                                         trend = trend,
                                         level = level,
                                         backend=backend,
                                         verbose=verbose,
                                         device_id=device_id)

            tile.get_bfast_parameters()

            tile.loop_blocks(x_block_size = x_block,
                                y_block_size = y_block)

            tile.log_all_output(output_dir_name=save_location)
            
            # delete tile from memory and replace with a placeholder zero to keep the list at same length 
            run_dict[data_list][counter] = '0'
            del(tile)
            
            pbar1.update(counter)

    pbar1.close()

# load in all npy tiles
run_dict = {}
for directory in os.listdir(timeseries_directory):
    
    segment_location = timeseries_directory + directory + "/"
    dates_location =  timeseries_directory + directory + "/dates.csv"
    
    data_list = set_paths(timeseries_directory = segment_location)
    
    run_dict[directory] = data_list
    
    for tile in data_list:
        print(tile)
        
        tile.start_monitor = start_monitor 
        tile.end_monitor = end_monitor
        tile.start_hist = start_hist
        
        tile.crop_dates(tile.dates)
        tile.load_breaks_means_arrays_from_file(output_dir_name =base_output_dir + "/" +  directory)
    
    
for data_list in run_dict:
    save_location = base_output_dir + "/" + data_list
    tiles_data = run_dict[data_list]
    
    for tile in tiles_data:
        tile.check_arrays(min_perc_lacking_data = 50)
    
    if len(tiles_data) > 1:
        means_orig, breaks_orig = merge_tiles(tiles_data,output_dir_name = save_location)
    else:
        means_orig = tiles_data[0].means_array
        breaks_orig = tiles_data[0].breaks_array
    
    save_plot(means_orig, save_location, save_name = "all_magnitudes")
    export_GTiff(tiles_data, output_dir = save_location, array = means_orig, output_name = "magnitudes_" + timeseries_directory[-2] + ".tif")
    export_GTiff(tiles_data, output_dir = save_location, array = breaks_orig, output_name = "breaks_indexed_" + timeseries_directory[-2] + ".tif")
    
    
    classified_means = classify_magnitudes(means_orig)
    export_GTiff(tiles_data, output_dir = save_location, array = classified_means, output_name = "magnitudes_classified" +  timeseries_directory[-2] + ".tif")
    
    
    # select only negative magnitudes
    means_neg, breaks_indexed, breaks_indexed_neg, binary_breaks, negative_binary_breaks = select_negatives(means_orig, breaks_orig)
    save_plot(means_neg, output_dir = save_location, save_name = "all_negative_magnitudes")

    # save negative means and breaks
    export_GTiff(tiles_data, output_dir = save_location, array = means_neg ,output_name = "magnitudes_negative_" + timeseries_directory[-2] + ".tif")
    export_GTiff(tiles_data, output_dir = save_location, array = binary_breaks ,output_name = "breaks_binary_" + timeseries_directory[-2] + ".tif")
    export_GTiff(tiles_data, output_dir = save_location, array = negative_binary_breaks ,output_name = "breaks_binary_negative_" + timeseries_directory[-2] + ".tif")

    dates_monitor = []
    dates = tiles_data[0].cropped_dates

    # collect dates for monitor period
    for i in range(len(dates)):
        if start_monitor <= dates[i]:
            dates_monitor.append(dates[i])
    dates_array = np.array(dates_monitor) # dates_array is the dates that are in the monitoring period
    
    # julian_date output
    julian_breaks = get_julian_dates(dates_array,breaks_indexed)
    negative_julian_breaks = get_julian_dates(dates_array,breaks_indexed_neg)

    # save negative means and breaks
    export_GTiff(tiles_data, output_dir = save_location, array = julian_breaks ,output_name = "breaks_julian_" + timeseries_directory[-2] + ".tif")
    export_GTiff(tiles_data, output_dir = save_location, array = negative_julian_breaks ,output_name = "breaks_julian_negative_" + timeseries_directory[-2] + ".tif")

end = time.time()
print("this took so long: ", end - start)

