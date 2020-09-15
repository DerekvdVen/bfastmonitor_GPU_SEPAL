#bfastmonitor_cpu

This github repository contains scripts for using the python bfast algorithm in SEPAL. 

NOTEBOOKS
- bfastmonitor_GPU.ipynb
    This is the main script for running over SEPAL time series tile directories. 
    
- bfastmonitor_GPU_stack.ipynb 
    If you want to run over a big data set in one go, you may run this code on a timeseries data set. 
    
PYTHON FROM TERMINAL
- bfastmonitor_GPU_stack.py -o [output_dir] -t [timeseries_dir]
    If you want to run bfastmonitor over an exceedingly large area, and know what parameters you want to use, this is recommended. 
        
        Example:
        
        You can run bfast_stack.py from the terminal:
        
        python3 bfast_stack.py -o Guyana -t ../../downloads/Time_series_2020-09-09_13-02-40/
        python3 bfast_stack.py -o Australia -t /home/dven/downloads/Time_series_2020-09-09_13-02-40/
    
PYTHON FUNCTIONS
- functions.py
    Contains general functions.

- plotting_funcs.py
    Contains functions for plotting.
    
- time_series.py
    Contains the Timeseries Class.
    
- widgets.py
    Contains the ipy widgets used in the notebooks. 
