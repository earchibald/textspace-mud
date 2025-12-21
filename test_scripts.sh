#!/bin/bash
cd /Users/earchibald/scratch/006-mats

# Test scripting system
{
    echo "admin"
    sleep 1
    echo "east"
    sleep 1
    echo "script teacher_schedule"
    sleep 8
    echo "quit"
} | nc localhost 8888
