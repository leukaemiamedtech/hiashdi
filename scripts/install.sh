#!/bin/bash

PRN="HIAS Historical Data Interface"
FMSG="- $PRN installation terminated"

read -p "? This script will install the $PRN on your device. Are you ready (y/n)? " cmsg

if [ "$cmsg" = "Y" -o "$cmsg" = "y" ]; then
	echo "- Installing $PRN"
	echo "- $PRN installed!"
else
	echo $FMSG;
	exit
fi