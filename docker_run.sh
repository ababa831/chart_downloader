SLACK_WEB_HOOK=$(gcloud secrets versions access 1 --secret SLACK_WEB_HOOK_CHART_DOWNLOADER)

curl -X POST -H 'Content-type: application/json' --data '{"text":"Execute docker_run.sh"}' $SLACK_WEB_HOOK

us_searchtime_start=$(date "+%Y-%m-%d 09:00:00")
us_searchtime_end=$(date "+%Y-%m-%d 15:59:59")
datenow=$(date "+%Y-%m-%d %H:%M:%S")

country="None"
if [[ "$us_searchtime_start" < "$datenow" ]] && [[ "$us_searchtime_end" > "$datenow" ]]; then
    country="us"
fi

msg="Target country:  $country"
curl -X POST -H 'Content-type: application/json' --data "{\"text\": \"$(echo $msg)\"}" $SLACK_WEB_HOOK

filename_chart="chart.pkl"
bucket="stock-dwh-lake"
directory="stock-batch"
destination="gs://$bucket/$directory/$country/"

if [ "$country" != "None" ]; then
    sudo docker run --rm --name chart_downloader \
    --env SLACK_WEB_HOOK=$SLACK_WEB_HOOK \
    -v $PWD:/home \
    chart_downloader:latest --filename_chart $filename_chart

    postdata="{\"text\": \"Upload requirements.txt and $filename_chart to $destination\"}"
    curl -X POST -H 'Content-type: application/json' --data "$(echo $postdata)" $SLACK_WEB_HOOK
    gsutil cp $(cd $(dirname ${BASH_SOURCE:-$0}); pwd)/requirements.txt  $destination
    gsutil cp $(cd $(dirname ${BASH_SOURCE:-$0}); pwd)/$filename_chart  $destination
else
    curl -X POST -H 'Content-type: application/json' --data '{"text":"Out of the collection time"}' $SLACK_WEB_HOOK
fi


