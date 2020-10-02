
output_array=(CS1 CS2 CS3 CS4)                              # minimum confidence for predicting 
#timeseries_array=(0.2 0.2 0.2)                             # non maximal supression iou
blocksize_array=(128 512 1024 2048)

# Essential parameters
o="MyCountry2"
t="/home/dven/downloads/Time_series_2020-09-17_14-47-37_CostaRica/"
start_monitor="2018-01-01"
end_monitor="2020-01-01"
start_history="2016-01-01"

# Parameters to 
k="3"
freq="365"
trend="False"
hfrac="0.25"
level="0.05"
backend="opencl"
#blocksize="512"

for x in 0 1 2 3
do
o="${output_array[$x]}"
#t="${timeseries_array[$x]}"
blocksize="${blocksize_array[$x]}"

python3 bfastmonitor_GPU_stack_bash.py -o $o -t $t -k $k -f $freq -tr $trend -hfrac $hfrac -l $level -b $backend -bs $blocksize -start_m $start_monitor -end_m $end_monitor -start_h $start_history

done