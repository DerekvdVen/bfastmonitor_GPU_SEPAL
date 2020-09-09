# module for functions used in the python bfastmonitor GPU
import os
import numpy as np
import json

import folium
from folium.plugins import FloatImage
import base64

from osgeo import gdal
from matplotlib import cm
import matplotlib.pyplot as plt
import matplotlib as mpl

from datetime import datetime
import copy

from time_series import Timeseries

from PIL import Image

from functions import normalize

def save_plot(array, output_dir, save_name,color_code = cm.Spectral):
    #plotting.py
    array_norm = normalize(array)
    
    im = Image.fromarray(np.uint8(color_code(array_norm)*255))
    
    imga = im.convert("RGBA")
    
    imga.save(output_dir + "/" + save_name +  ".png","PNG")
    

    
    fig, ax = plt.subplots(figsize=(6, 1))
    fig.subplots_adjust(bottom=0.5)

    cmap = mpl.cm.Spectral
    norm = mpl.colors.Normalize(np.nanmin(array), np.nanmax(array))

    cb1 = mpl.colorbar.ColorbarBase(ax, cmap=cmap,
                                    norm=norm,
                                    orientation='horizontal')
    cb1.set_label(save_name)
    
  
    plt.savefig(output_dir + "/" + "testcolorbar.png",bbox_inches='tight')
    
    print("saved in " + output_dir + "/" + save_name + ".png")
    
def merge_plots(base_output_dir = "output", plot_name = "all_means.png"):
    #plotting.py
    basemap = False
    for directory in os.listdir(base_output_dir):
        if not directory.startswith('.'):
            print(directory)
            try:
                with open(base_output_dir + "/" + directory + "/corners.json","r") as f:
                    corner_dict = json.load(f)
                min_lat = corner_dict["min_lat"]
                min_lon = corner_dict["min_lon"]
                max_lat = corner_dict["max_lat"]
                max_lon = corner_dict["max_lon"]


                if basemap == False:
                    m = folium.folium.Map(location = (min_lat,min_lon), tiles = "Stamen Terrain",zoom_start=9)
                    basemap = True

                folium.raster_layers.ImageOverlay(
                    image = base_output_dir + "/" + directory +"/" + plot_name,
                    bounds=[[min_lat, min_lon], [max_lat, max_lon]],
                ).add_to(m)
            except:
                print(directory + " does not have this data output stored")

    return(m)

def classify_output(start_monitor,end_monitor,breaks_plot,dates_array):
    #plotting.py
    idx_starts = {}

    # this gives the index of all the data points in the year and after
    for year in range(start_monitor.year,end_monitor.year+1):
        idx_starts[year] = np.argmax((dates_array >= datetime(year, 1, 1)) > False) 
    print(idx_starts)

    breaks_plot_years = copy.deepcopy(breaks_plot)


    #classifying for plotting
    ticklist=[]
    for idx, year in enumerate(idx_starts):
        ticklist.append(str(year))

        # if we're at the last year
        if idx == len(idx_starts)-1:
            breaks_plot_years[np.where(idx_starts[year] < breaks_plot)] = len(idx_starts)-1 
            continue

        # if we're at the first year
        if idx == 0:
            breaks_plot_years[breaks_plot <= idx_starts[year+1]] = 0
            continue

        # all other years in between
        breaks_plot_years[np.where(np.logical_and(idx_starts[year] < breaks_plot, breaks_plot <= idx_starts[year+1]))] = idx
    
    return breaks_plot_years, idx_starts, ticklist

def plot_output_matplotlib(idx_starts,breaks_plot_years, ticklist):

    bins = len(idx_starts)

    cmap = plt.get_cmap("Spectral")
    cmaplist = [cmap(i) for i in range(cmap.N)]
    cmap = cmap.from_list('Custom cmap', cmaplist, cmap.N)

    bounds = np.linspace(0, bins-1, bins) #third number is the amount of bins in the colorbar 0=0, 6 = ncolors, 7= nyears
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(50, 50))

    #norm doesn't work with bins = 2 or less... now the colorbar is ugly, fix it later

    if bins == 1:
        im = axes.imshow(breaks_plot_years,cmap=cmap,vmin=0,vmax=bins)
    if bins == 2:
        im = axes.imshow(breaks_plot_years,cmap=cmap,vmin=0,vmax=bins)
    else:
        im = axes.imshow(breaks_plot_years, cmap=cmap, vmin=0, vmax=bins, norm=norm)

    fig.subplots_adjust(right=0.8)
    cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
    fig.colorbar(im, cax=cbar_ax, ticks=range(bins))
    labels = cbar_ax.set_yticklabels(ticklist)

    plt.show()
    
    
def export_GTiff(data_list, output_dir, array, output_name = "test_raster.tif"):
    
    total_ncols = array.shape[1]
    total_nrows = array.shape[0]
        
    if array.dtype == "int32":
        etype = gdal.GDT_Int32
    else:
        etype = gdal.GDT_Float32
        
    geotransform = data_list[0].geotransform
    projection = data_list[0].projection
    
    save_location = output_dir + "/geotifs"
    if not os.path.exists(save_location):
        os.makedirs(save_location)
    
    dst_ds = gdal.GetDriverByName('GTiff').Create(save_location + "/" + output_name, 
                                                  xsize = total_ncols, 
                                                  ysize = total_nrows, 
                                                  bands = 1,
                                                  eType = etype)

    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(projection)
    dst_ds.GetRasterBand(1).WriteArray(array)
    dst_ds.FlushCache()
    del dst_ds
    print("saved in " + save_location + "/" + output_name)

def set_corners(output_dir, data_list):

    # set corners
    min_lat = data_list[0].latitude
    max_lat = data_list[0].latitude
    min_lon = data_list[0].longitude
    max_lon = data_list[0].longitude

    for i in range(len(data_list)):
        if data_list[i].latitude > min_lat:
            min_lat = data_list[i].latitude
        if data_list[i].longitude < min_lon:
            min_lon = data_list[i].longitude

        if data_list[i].latitude < max_lat:
            max_lat = data_list[i].latitude - data_list[i].nrows*data_list[i].xpixelsize
        if data_list[i].longitude > max_lon:
            max_lon = data_list[i].longitude + data_list[i].ncols*data_list[i].xpixelsize

    print("min_lat " , min_lat)
    print("max_lat " , max_lat)
    print("min_lon " , min_lon)
    print("max_lon " , max_lon)
    corner_dict = {"min_lat": min_lat,"max_lat": max_lat,"min_lon": min_lon,"max_lon": max_lon}


    with open(output_dir + "/" + "corners.json","w") as f:
        json.dump(corner_dict, f)
    print("saved in " + output_dir + "/" + "corners.json")
     