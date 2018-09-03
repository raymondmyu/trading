#!/bin/bash

gcloud compute instances start "datascience-main" --zone "us-east1-b"
sleep 30s
gcloud compute --project "datascience-rayyu-gc" ssh --zone "us-east1-b" "datascience-main" --command 'cd /home/ray/Projects/trading/intrinio && /home/ray/anaconda3/bin/python run_api_daily.py'
# gcloud compute --project "datascience-rayyu-gc" ssh --zone "us-east1-b" "datascience-main" --command 'cd /home/ray/Projects/trading/intrinio/mongo && ./requests_to_longform.sh'
gcloud compute instances stop "datascience-main" --zone "us-east1-b"