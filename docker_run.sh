SLACK_WEB_HOOK=$(gcloud secrets versions access 1 --secret SLACK_WEB_HOOK_CHART_DOWNLOADER)

us_searchtime_start=$(date "+%Y-%m-%d 09:00:00")
us_searchtime_end=$(date "+%Y-%m-%d 15:59:59")
datenow=$(date "+%Y-%m-%d %H:%M:%S")

country="None"
if [[ "$us_searchtime_start" < "$datenow" ]] && [[ "$us_searchtime_end" > "$datenow" ]]; then
    country="us"
fi

echo $country
filename_chart="chart.pkl"
bucket="stock-dwh-lake"
directory="stock-batch"
destination="gs://$bucket/$directory/$country/"

if [ "$country" != "None" ]; then
    sudo docker run --rm -it --name chart_downloader \
    --env SLACK_WEB_HOOK=$SLACK_WEB_HOOK \
    -v $PWD:/home \
    chart_downloader:latest --filename_chart $filename_chart 
    gsutil cp $(cd $(dirname ${BASH_SOURCE:-$0}); pwd)/requirements.txt  $destination
    gsutil cp $(cd $(dirname ${BASH_SOURCE:-$0}); pwd)/$filename_chart  $destination
fi


