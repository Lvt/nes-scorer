#!/bin/bash

limit=50

cnt=$(ls -1 population | tail -n ${limit} | wc -l)
a=$(( RANDOM % (cnt * cnt) ))
a=$(echo "sqrt($a)" | bc -l | sed 's:[.].*::')
