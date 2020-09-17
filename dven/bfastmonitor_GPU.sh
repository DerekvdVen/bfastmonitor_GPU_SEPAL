# learning rate

# Essential parameters
o="MyCountry2"
t="/home/dven/downloads/Time_series_2020-09-14_13-57-37_Jamaica/"
start_monitor="2015-01-01"
end_monitor="2020-01-01"
start_history="2012-01-01"

# Parameters to 
k="3"
freq="365"
trend="False"
hfrac="0.25"
level="0.05"
backend="opencl"
blocksize="512"


# run bfastmonitor_GPU
echo run bfastmonitor with your parameters of interest
# 
# python3 bfastmonitor_GPU_stack.py -o $o -t $t -start_m $start_monitor -end_m $end_monitor -start_h $start_history

python3 bfastmonitor_GPU_stack_bash.py -o $o -t $t -k $k -f $freq -tr $trend -hfrac $hfrac -l $level -b $backend -bs $blocksize -start_m $start_monitor -end_m $end_monitor -start_h $start_history