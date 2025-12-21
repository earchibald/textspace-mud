#!/bin/bash
cd /Users/earchibald/scratch/006-mats

# Test complete system
{
    echo "admin"
    sleep 1
    echo "help"
    sleep 1
    echo "teleport garden"
    sleep 1
    echo "look"
    sleep 1
    echo "broadcast Welcome to the Text Space everyone!"
    sleep 1
    echo "script garden_guide_welcome"
    sleep 5
    echo "teleport library"
    sleep 1
    echo "say Hello Ms. Teacher!"
    sleep 2
    echo "quit"
} | nc localhost 8888
