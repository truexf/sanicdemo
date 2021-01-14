#!/bin/bash

cat uhrs.pid
echo killing...
kill `cat uhrs.pid`
sleep 1
echo ok