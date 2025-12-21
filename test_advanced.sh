#!/bin/bash
cd /Users/earchibald/scratch/006-mats

# Test advanced scripting features
{
    echo "admin"
    sleep 1
    echo "teleport lobby"
    sleep 1
    echo "get crystal gem"
    sleep 1
    echo "inventory"
    sleep 1
    echo "quit"
} | nc localhost 8888
