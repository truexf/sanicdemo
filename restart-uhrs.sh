#!/bin/bash

echo restarting...
kill `cat uhrs.pid`
sleep 1
python3 uhrs.py
echo ok
