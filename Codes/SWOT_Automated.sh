#!/bin/bash

source ~/miniconda3/etc/profile.d/conda.sh 

conda activate /home/skhan7/miniconda3/envs/swot_env  
cd /water3/skhan7/SWOT_BD_Tripura/Codes  

python Download_SWOT_Data.py
python Create_SWOT_Image.py
python Create_SWOT_Mosaicked_Image.py
python Calendar_Dates.py
python Upload_Images.py

rm -rf /water3/skhan7/SWOT_BD_Tripura/Downloaded_Data/*
rm -rf /water3/skhan7/SWOT_BD_Tripura/Filtered_Data/*