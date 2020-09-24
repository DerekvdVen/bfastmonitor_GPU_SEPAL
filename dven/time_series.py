from osgeo import gdal

import os

import matplotlib.pyplot as plt

import numpy as np
from numpy import nan
from numpy import isnan

from bfast import BFASTMonitor
from bfast.utils import crop_data_dates

import pyopencl
import inspect

import time
from datetime import datetime

from tqdm import tqdm

import warnings
warnings.filterwarnings('always')

#from functions import _find_index_date

import json

class Timeseries:
    '''
    The timeseries class is a wrapper for using SEPAL timeseries data with bfast. 
    It wraps together a data tile with associated dates file and metadata. 
    It also allows for saving and loading the output rasters in a specified directory. 
    '''
    
    def __init__(self, time_series_path, dates_path):
        '''
        Initializes the Timeseries class. 
        
        Parameters
        -----------
        time_series_path: string, a location for the time series data. 
        for example: 'home/usr/downloads/Time_seriesxxx/1/'
        
        dates_path: string, a location for the time series dates.csv file
        for example: 'home/usr/downloads/Time_seriesxxx/1/dates.csv'
        '''
        
        # Store name of vrt location and the associated dir
        self.name = time_series_path + "stack.vrt"
        self.dir = time_series_path
        
        # Open the timeseries to extract geo-metadata
        self.time_series = gdal.Open(self.name)
        self.geotransform = self.time_series.GetGeoTransform()
        
        # Store geo-metadata
        self.xpixelsize = self.geotransform[1]
        self.ypixelsize = self.geotransform[5]
        self.latitude = self.geotransform[3]
        self.longitude = self.geotransform[0]
        self.ncols = self.time_series.RasterXSize
        self.nrows = self.time_series.RasterYSize
        self.projection = self.time_series.GetProjection()
        self.nbands = self.time_series.RasterCount
        
        # Get gdal's recommended block size
        band = self.time_series.GetRasterBand(1)
        self.gdal_recommended_block_size = band.GetBlockSize()
        
        # Set a time dictionary for testing runtimes
        self.time_dict = {}
        
        self.date = str(datetime.now())
        try:
            self.device = pyopencl.get_platforms()[0].get_devices()
        except:
            self.device = "cpu"
            
        
        # self.raster_stack_orig = time_series.ReadAsArray()
        # This takes really long and will likely cause memory issues when running on large countries, so don't use it
        # Use blocks and base block size on what gdal sets or on ram calculation 
        
        # Store dates_file
        with open(dates_path) as f:
            dates_list = f.read().split('\n')
            self.dates = [datetime.strptime(d, '%Y-%m-%d') for d in dates_list if len(d) > 0]
        
    def __str__(self):
        return("Timeseries class holding {} dates, sized {} by {}.".format(self.nbands,
                                                                        self.ncols,
                                                                        self.nrows))
    def __repr__(self):
            return("Timeseries: {} ".format(self.name))

    def run_bfast(self, block):
        '''Runs bfastmonitor over the give timeseries with the parameters set in self.set_parameters
        
        parameters:
        -----------
        
        block: numpy array, 3D numpy array to run bfast upon
        '''
        
        data, self.cropped_dates = crop_data_dates(block, self.dates, self.start_hist, self.end_monitor)

        # only apply on a small subset
        #data = data[:,:80,:80]
        
        # change nans to a number bfastmonitor-GPU can work with
        where_are_NaNs = isnan(data)
        data[where_are_NaNs] = -32768

        # fit model
        self.model.fit(data, self.cropped_dates, nan_value = -32768) 
        
        # save breaks and mean magnitudes
        breaks = self.model.breaks # index of date that has a break in dates
        means = self.model.means # magnitudes of breaks
        
        return(breaks,means)
    
    def loop_blocks(self,x_block_size,y_block_size):
        
        '''Loops over a tile array in smaller set block sizes
        
        parameters
        ----------
        
        x_block_size: int, n cols block size
        y_block_size: int, n rows block size
        '''
        start_time = time.time()
        
        if not x_block_size:
            x_block_size = self.gdal_recommended_block_size[0]
        else:
            self.x_block_size = x_block_size
        if not y_block_size:
            y_block_size = self.gdal_recommended_block_size[1]
        else:
            self.y_block_size = y_block_size

        print("rastersize: ",self.ncols,self.nrows)
        print("The natural block size is the block size that is most efficient for accessing the format, gdal found blocksize: ",self.gdal_recommended_block_size)
        print("set blocksize explicitly: ",x_block_size,", " ,y_block_size)
        print("start monitor: ", self.start_monitor)
        print("end monitor: ", self.end_monitor)
        print("start history: ", self.start_hist)
        
        
        first_verstack=True

        # loop over yblocks
        with tqdm(total=round((self.ncols/x_block_size)*(self.nrows/y_block_size))) as pbar2:
            pbar2.set_description("Processing blocks of tile:")
                    
                
            for i in range(0, self.nrows, y_block_size):
                
                
                first_horstack = True
                if i + y_block_size < self.nrows:
                    rows = y_block_size
                else:
                    rows = self.nrows - i

                # Loop over xblocks
                for j in range(0, self.ncols, x_block_size):
                    
                    
                    if j + x_block_size < self.ncols:
                        cols = x_block_size
                    else:
                        cols = self.ncols - j

                    print(j,i,cols,rows)

                    # first step creates the array
                    pbar2.update(1)
                    
                    if first_horstack==True:
                        data = self.time_series.ReadAsArray(j, i, cols, rows).astype("int16")
                        breaks,means = self.run_bfast(data)
                        breaks_array = breaks
                        means_array = means
                        first_horstack=False

                    # after that add to array
                    else:                    
                        data = self.time_series.ReadAsArray(j, i, cols, rows).astype("int16")
                        breaks,means = self.run_bfast(data)
                        breaks_array = np.concatenate((breaks_array,breaks),axis = 1)
                        means_array = np.concatenate((means_array,means),axis = 1)
                
                
                # first step create new object verstack for the data
                if first_verstack == True:
                    stack_breaks_array = breaks_array
                    stack_means_array = means_array
                    first_verstack = False
                
                # all other times that add new array to verstack
                else:
                    stack_breaks_array = np.concatenate((stack_breaks_array,breaks_array),axis=0)
                    stack_means_array = np.concatenate((stack_means_array,means_array),axis=0)

            # store output arrays
            self.breaks_array = stack_breaks_array
            self.means_array = stack_means_array
            
            # save times
            pbar2.close()
            end_time = time.time()
            print("Fitting model over all blocks took {} seconds.".format(end_time - start_time))
            self.time_dict[self.name] = str(end_time - start_time) + " seconds"

    def set_bfast_parameters(self, start_monitor, end_monitor, start_hist,freq,k,hfrac,trend,level,backend='opencl',verbose=1,device_id=0):
        '''Set parameters, see bfast for what they do.. okay we should say this here
        
        parameters:
        -----------
        
        start_monitor : datetime object
        A datetime object specifying the start of 
        the monitoring phase.
        
        end_monitor: datetime object
        A datetime object specifying the end of 
        the monitoring phase.
        
        start_hist: datetime object
        A datetime object specifying the start of
        the history phase.
        
        freq : int, default 365
            The frequency for the seasonal model.

        k : int, default 3
            The number of harmonic terms.

        hfrac : float, default 0.25
            Float in the interval (0,1) specifying the 
            bandwidth relative to the sample size in 
            the MOSUM/ME monitoring processes.

        trend : bool, default True
            Whether a tend offset term shall be used or not

        level : float, default 0.05
            Significance level of the monitoring (and ROC, 
            if selected) procedure, i.e., probability of 
            type I error.
            
        
        backend : string, either 'opencl' or 'python'
            Chooses what backend to use. opencl uses the GPU
            implementation, which is much faster. 
        
        verbose : int, optional (default=0)
            The verbosity level (0=no output, 1=output)
        '''
        
        self.start_monitor = start_monitor
        self.end_monitor = end_monitor
        self.start_hist = start_hist
        self.freq = freq
        self.k = k
        self.hfrac = hfrac
        self.trend = trend
        self.level = level
        self.backend = backend
        self.verbose = verbose
        self.device_id = device_id
        
        self.model = BFASTMonitor(
                    self.start_monitor,
                    freq=freq, # add these
                    k=k,
                    hfrac=hfrac,
                    trend=trend,
                    level=level,
                    backend=backend,
                    verbose=verbose,
                    device_id=device_id,
                    )
        
        try:
            print("device: ", pyopencl.get_platforms()[0].get_devices())
        except:
            print("You selected  openCL, but no device was found, are you sure you set up a gpu session?")

    
    def get_bfast_parameters(self):
        '''
        Prints the set parameters in set_bfast_parameters()
        '''
        print("Monitoring starts at: ", self.start_monitor)
        print("Monitoring ends at: ", self.end_monitor)
        print("Dataset history starts at: ", self.start_hist)
        print("frequency: ", self.freq)
        print("harmonic term: ", self.k)
        print("Hfrac: Float in the interval (0,1) specifying the bandwidth relative to the sample size in the MOSUM/ME monitoring processes.: ", self.hfrac)
        print("Trend: Whether a tend offset term shall be used or not: ", self.trend)
        print("Level: Significance level of the monitoring (and ROC, if selected) procedure, i.e., probability of type I error: ", self.level)
        print("backend: GPU opencl or CPU python: ", self.backend)
        print("verbose: The verbosity level (0=no output, 1=output): ", self.verbose)
        
    
    def check_arrays(self, min_perc_lacking_data = 20,print_output=False):
        '''
        Checks the means and breaks arrays for amount of breaks, and means values. 
        '''
        minus1count = np.count_nonzero(self.breaks_array == -1) # no break found
        minus2count = np.count_nonzero(self.breaks_array == -2) # not enough data for output
        total_count = self.nrows*self.ncols
        
        if print_output:
            print("minus2s: ", minus2count)
            print("minus1s: ", minus1count)
            print("total", total_count)

        perc_lacking_data = minus2count/total_count*100
        perc_breaks = (total_count - (minus1count + minus2count))/total_count * 100
        #nans_in_means = np.count_nonzero(np.isnan(self.means_array))
        if print_output:
            print("percentage cells that lacked enough data for finding means or breaks: " + str(perc_lacking_data))
            print("percentage cells where breaks were found: " + str(perc_breaks))
            #print("amount of nans in means: ", nans_in_means)

        if perc_lacking_data > min_perc_lacking_data:
            return(warnings.warn("Warning: More than {} percent of the pixels in this tile lack sufficient data, resulting in NaNs. Consider selecting a longer monitoring period or a larger area.".format(min_perc_lacking_data)))
        return(minus2count,minus1count,perc_lacking_data,perc_breaks)
    
    
    def log_all_output(self,output_dir_name = 'stored_time_series/output'):
        
        '''Logs the Timeseries output of the respective tile'''
        
        if not os.path.exists(output_dir_name):
            os.makedirs(output_dir_name)
        if not os.path.exists(output_dir_name):
            os.makedirs(output_dir_name)
        
        # Set save_dir name
        tile_name = self.name.split('/')[-2]
        if not 'tile' in tile_name:
            tile_name = 'single_tile'
        
        # metadata
        save_name = output_dir_name + "/" + tile_name  + "_meta_data.txt"
        
        attributes = inspect.getmembers(self, lambda a:not(inspect.isroutine(a)))
        with open(save_name, "w") as f:
            for a in attributes:
                if not(a[0].startswith('__') and a[0].endswith('__')):
                    f.write(str(a))
                    f.write("\n")
        
        # arrays
        save_means_name = output_dir_name + '/' + tile_name + "_means.npy"
        save_breaks_name = output_dir_name + '/' + tile_name + "_breaks.npy"
        try:
            np.save(save_means_name, self.means_array)
            np.save(save_breaks_name, self.breaks_array)
        except:
            print("No arrays are currently loaded")
    
    def load_breaks_means_arrays_from_file(self, output_dir_name = 'stored_time_series/output',print_output = False):
        '''
        Loads the locally saved means and breaks arrays from log_breaks_means_arrays() method
        '''
        
        
        tile_name = self.name.split('/')[-2]
        if not 'tile' in tile_name:
            tile_name = 'single_tile'
        
        load_means_name = output_dir_name + '/' + tile_name + "_means.npy"
        load_breaks_name = output_dir_name + '/' + tile_name + "_breaks.npy"
        
        if print_output:
            print(load_means_name)
            print(load_breaks_name)

        self.means_array = np.load(load_means_name)
        self.breaks_array = np.load(load_breaks_name)
    

    def _find_index_date(self, dates, t):
        '''Returns the index of the first date larger than t'''
        for i in range(len(dates)):
            if t < dates[i]:
                return i

            return len(dates)

    def crop_dates(self, dates):
        """ Crops the input data and the associated
        dates w.r.t. the provided start and end 
        datetime object.

        Parameters
        ----------
        data: ndarray of shape (N, W, H)
            Here, N is the number of time 
            series points per pixel and W 
            and H are the width and the height 
            of the image, respectively.
        dates : list of datetime objects
            Specifies the dates of the elements
            in data indexed by the first axis
            n_chunks : int or None, default None
        start : datetime
            The start datetime object
        end : datetime
            The end datetime object

        Returns
        -------
        Returns: data, dates
            The cropped data array and the 
            cropped list. Only those images 
            and dates that are with the start/end
            period are contained in the returned
            objects.
        """
        
        from functions import _find_index_date
        start = self.start_hist
        end = self.end_monitor
        
        start_idx = _find_index_date(dates, start)
        end_idx = _find_index_date(dates, end)

        dates_cropped = list(np.array(dates)[start_idx:end_idx])
        self.cropped_dates = dates_cropped



      