#!/bin/bash

echo Getting Values for 14400!

curl 'http://localhost:5000/get_ticker?period=14400'
echo Got Data 14400!

curl 'http://localhost:5000/get_historical_google_trends?period=14400&historical=15'
echo Got Google Trend

curl 'http://localhost:5000/get_tas?period=14400'
echo Got TAs 14400!

curl 'http://localhost:5000/make_prediction?period=14400'
echo Making Predictions 14400!
