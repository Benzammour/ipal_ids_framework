#!/usr/bin/env bash

./ipal-iids --log DEBUG --train.state ~/projects/rwth/lecture-material/Exercises/03-intrusion-detection/warmup-train.state --config misc/configs/MinMaxChange.config --live.state ~/projects/rwth/lecture-material/Exercises/03-intrusion-detection/warmup-live.state --output ./output.txt
