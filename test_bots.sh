#!/bin/bash
cd /Users/earchibald/scratch/006-mats

# Test bot interaction
{
    echo "student"
    sleep 1
    echo "east"
    sleep 1
    echo "look"
    sleep 1
    echo "say hello"
    sleep 3
    echo "say math"
    sleep 3
    echo "quit"
} | nc localhost 8888
