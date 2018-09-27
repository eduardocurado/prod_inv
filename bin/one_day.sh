#!/bin/bash

echo Getting Values for 86400!

curl 'http://localhost:5000/get_ticker?period=86400'
echo Got Data 86400!

curl 'http://localhost:5000/get_historical_google_trends?period=14400&historical=15'

curl 'http://localhost:5000/get_tas?period=86400'
echo Got TAs 86400!
