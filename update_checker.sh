#!/bin/bash

# Get 2 Dates
latest_update=$(gsutil ls -l gs://stock-dwh-lake/stock-batch/us/chart.pkl | grep -oP '\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?Z?')
checkpoint_datetime=$(date --date "5 hours ago" +%Y-%m-%dT%H:%M:%SZ)
# Convert to unixtime
latest_update=$(date --date $latest_update +%s)
checkpoint_datetime=$(date --date $checkpoint_datetime +%s)
# Comparision
if [ $latest_update -lt $checkpoint_datetime ];
then
    exit 1
fi