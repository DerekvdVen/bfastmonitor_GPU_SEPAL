import ipywidgets as widgets
from ipywidgets import Layout


def g(i):
    return(i)

def get_widgets():
    layout = widgets.Layout(width='500px', height='auto')
    style = {'description_width': 'initial'}

    output_directory_chooser = widgets.interactive(g, 
        i=widgets.Text(
            description="Output storage name:", 
            placeholder = "output",
            style = {'description_width': 'initial'},))
    
    k_chooser = widgets.interactive(g, 
        i=widgets.Dropdown(
            options=[1,2,3,4,5,6],
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
            value = True, 
            description= "add trend",
            style = style, layout=layout,))

    hfrac_chooser = widgets.interactive(g,
        i=widgets.FloatSlider(
            value = 0.25,min=0,max=1,step=0.01,
            description= "Bandwith relative to sample size",
            style = style, layout=layout,))

    level_chooser = widgets.interactive(g,
        i=widgets.FloatSlider(
            value = 0.25,
            description= "Significance level of the monitoring",
            style = style,
            layout = layout, ))

    backend_chooser = widgets.interactive(g, 
        i=widgets.Dropdown(
            options=['opencl','python'],
            value='opencl',
            description='backend',
            style = style, layout = layout,))
    
    return(output_directory_chooser,k_chooser,freq_chooser,trend_chooser,hfrac_chooser,level_chooser,backend_chooser)


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