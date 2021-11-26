# chart_downloader
dailyでチャートを最新情報に更新して収集

構成はminervini_screeningを踏襲している

## 準備

1. GCSの株価データ保存用のBucketを用意．src/docker_run.sh内のbucket名を書き換える
1. Secret Managerで以下を設定
  - SLACK_WEB_HOOK_CHART_DOWNLOADER: Slackにログを投稿するためのIncoming Webhook URL
1. GCP Compute Engine Instance作成
  - startup script設定欄に, src/startup_script.txt内のコマンドを入力
1. Cloud Runに定期実行設定
  - EndpointのURLは作成したInstanceに対応したものを指定