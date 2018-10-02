#!/bin/bash

echo Setting Up Data Base!

<<<<<<< Updated upstream
curl 'http://localhost:5000/get_historical_tickers?period=86400&historical=400'
=======
curl 'http://localhost:5000/get_historical_tickers?period=86400&historical=8'
>>>>>>> Stashed changes
echo Got Historical Data 86400!
curl 'http://localhost:5000/get_historical_tickers?period=14400&historical=8'
echo Got Historical Data 14400!

<<<<<<< Updated upstream
curl 'http://localhost:5000/get_historical_google_trends?period=14400&historical=10'
=======
curl 'http://localhost:5000/get_historical_google_trends?period=14400&historical=15'
>>>>>>> Stashed changes
echo Got Google Trends

curl 'http://localhost:5000/get_historical_tas?period=86400&historical=8'
echo Got Historical TAs 86400!
<<<<<<< Updated upstream
curl 'http://localhost:5000/get_historical_tas?period=14400&historical=3'
=======
curl 'http://localhost:5000/get_historical_tas?period=14400&historical=8'
>>>>>>> Stashed changes
echo Got Historical TAs 14400!
