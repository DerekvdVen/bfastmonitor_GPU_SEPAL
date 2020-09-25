
output_array=(test1 test2)                              # minimum confidence for predicting 
#timeseries_array=(0.2 0.2 0.2)                             # non maximal supression iou

# Essential parameters
o="MyCountry2"
t="/home/dven/downloads/Time_series_2020-09-09_13-02-40_Australia_small/"
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

for x in 0 1
do
o="${output_array[$x]}"
#t="${timeseries_array[$x]}"


python3 bfastmonitor_GPU_stack_bash.py -o $o -t $t -k $k -f $freq -tr $trend -hfrac $hfrac -l $level -b $backend -bs $blocksize -start_m $start_monitor -end_m $end_monitor -start_h $start_history


done