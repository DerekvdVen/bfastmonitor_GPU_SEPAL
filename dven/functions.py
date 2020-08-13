# module for functions used in the python bfastmonitor GPU
import os

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
