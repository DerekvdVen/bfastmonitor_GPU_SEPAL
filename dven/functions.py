# module for functions used in the python bfastmonitor GPU
import os
import numpy as np
from osgeo import gdal

def test():
    print("hello derp")
    
def set_output_dir(chooser):
    if not chooser.result:
        print("Defaulting to output directory name \"output\" ")
        save_location = "stored_time_series/output"
        if not os.path.exists(save_location):
            os.makedirs(save_location)
    else:
        print("Output directory name:", chooser.result)
        save_location = "stored_time_series/" + chooser.result
        if not os.path.exists(save_location):
            os.makedirs(save_location)

def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size

def get_data_dict(time_series_path):
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

    for i in range(len(dates)):
        if t < dates[i]:
            return i
    
    return len(dates)
                
def merge_tiles(tile_list, output_dir_name = 'my_data'):
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
    
    save_location = "stored_time_series"
    
    save_means_dir = save_location + "/" + output_dir_name + '/' + "all_means.npy"
    save_breaks_dir = save_location + "/" + output_dir_name + '/' + "all_breaks.npy"
    print(save_means_dir)
    print(save_breaks_dir)
    np.save(save_means_dir, big_means_array)
    np.save(save_breaks_dir, big_breaks_array)

    return(big_means_array, big_breaks_array)
