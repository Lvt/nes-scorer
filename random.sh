#!/bin/bash

file="tmp/${RANDOM}.fm2"
./generator.py --random "${file}"
./run.py -g smb3.nes -m "${file}" -c population/
rm "${file}"
