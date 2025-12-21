#!/bin/bash
# Test messaging system with two users

# Start user 1 in background
(sleep 1 && echo -e "alice\nsay Hello everyone!\nquit") | nc localhost 8888 > /tmp/user1.txt &

# Start user 2
(sleep 2 && echo -e "bob\nsay Hi Alice!\nwhisper alice This is a secret\nquit") | nc localhost 8888 > /tmp/user2.txt &

# Wait for both to complete
sleep 5

echo "=== User 1 (Alice) ==="
cat /tmp/user1.txt
echo ""
echo "=== User 2 (Bob) ==="
cat /tmp/user2.txt

rm /tmp/user1.txt /tmp/user2.txt
