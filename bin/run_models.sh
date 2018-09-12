#!/bin/bash

echo Getting Values for 14400!

curl 'http://localhost:5000/train_models?period=14400&historical=400'
echo Got Data 14400!
