# The collection of widgets used in the notebooks

import ipywidgets as widgets
from ipywidgets import Layout


def g(i):
    return(i)

def get_widgets():
    layout = widgets.Layout(width='500px', height='auto')
    style = {'description_width': 'initial'}

    output_directory_chooser = widgets.interactive(g, 
        i=widgets.Text(
            description="Output storage name: (country/location name, e.g. \"Guyana\")", 
            placeholder = "output",
            style = style, layout =layout,))
    
    k_chooser = widgets.interactive(g, 
        i=widgets.Dropdown(
            options=[3,4,5,6,7,8,9,10],
            value=3,
            description='k, harmonic terms',
            style = style, layout= layout,))

    freq_chooser = widgets.interactive(g, 
        i=widgets.IntSlider(
            value = 365,min=1,max=365,step=1,
            description='freq, frequency of seasonal model (days)',
            style = style, layout=layout,))

    trend_chooser = widgets.interactive(g,
        i=widgets.Checkbox(
            value = False, 
            description= "add trend",
            style = style, layout=layout,))

    hfrac_chooser = widgets.interactive(g,
        i=widgets.FloatSlider(
            value = 0.25,min=0,max=1,step=0.01,
            description= "Bandwith relative to sample size",
            style = style, layout=layout,))

    level_chooser = widgets.interactive(g,
        i=widgets.SelectionSlider(
            description= "Significance level of the monitoring",
            options = [0.95 , 0.951, 0.952, 0.953, 0.954, 0.955, 0.956, 0.957, 0.958,
       0.959, 0.96 , 0.961, 0.962, 0.963, 0.964, 0.965, 0.966, 0.967,
       0.968, 0.969, 0.97 , 0.971, 0.972, 0.973, 0.974, 0.975, 0.976,
       0.977, 0.978, 0.979, 0.98 , 0.981, 0.982, 0.983, 0.984, 0.985,
       0.986, 0.987, 0.988, 0.989, 0.99 , 0.991, 0.992, 0.993, 0.994,
       0.995, 0.996, 0.997, 0.998, 0.999],
            style = style,
            layout = layout, ))

    
    backend_chooser = widgets.interactive(g, 
        i=widgets.Dropdown(
            options=['opencl','python'],
            value='opencl',
            description='backend',
            style = style, layout = layout,))
    
    load_chooser = widgets.interactive(g,
        i=widgets.Checkbox(
            value = False, 
            description= "load tiles",
            style = style, layout=layout,))
    
    block_size_chooser = widgets.interactive(g, 
        i=widgets.Dropdown(
            options=[128,256,512,1024],
            value=512,
            description='block size, bigger is generally faster, but may result in memory issues',
            style = style, layout = layout,))
    
    plot_display_data_chooser = widgets.interactive(g, 
        i=widgets.Dropdown(
            options=['magnitudes','magnitudes_negative'],
            value='magnitudes',
            description='data to plot',
            style = style, layout = layout,))
    
    
    return(output_directory_chooser,k_chooser,freq_chooser,trend_chooser,hfrac_chooser,level_chooser,backend_chooser, load_chooser, block_size_chooser, plot_display_data_chooser)


def get_dates_widgets(options, index):
    monitoring_period_chooser = widgets.interactive(g,
         i=widgets.SelectionRangeSlider(
            options=options,
            index=index,
            description='Select the monitoring date range: ',
            style = {'description_width': 'initial'},
            orientation='horizontal',
            layout={'width': '800px',"height":"50px"}))

    history_period_chooser = widgets.interactive(g, 
         i=widgets.SelectionSlider(
            description="Start history period:", 
            options = options,
            style = {'description_width': 'initial'}))
    return monitoring_period_chooser, history_period_chooser