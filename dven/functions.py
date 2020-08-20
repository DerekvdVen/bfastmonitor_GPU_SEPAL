# module for functions used in the python bfastmonitor GPU
import os
from osgeo import gdal

def test():
    print("hello derp")
    
def set_output_dir(chooser):
    if not chooser.result:
        print("Defaulting to output directory name \"output\" ")
        output_directory = "output"
        if not os.path.exists("output"):
            os.makedirs(output_directory)
    else:
        print("Output directory name:", chooser.result)
        if not os.path.exists(chooser.result):
            os.makedirs(chooser.result)

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

