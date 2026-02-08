#!/bin/bash

INTERFACE="wlan0"
AP_NAME="AP"
TIMEOUT=20

# Wait for NetworkManager to start
sleep 5

# Try to autoconnect known Wi-Fi networks
nmcli device wifi connect "$INTERFACE" 2>/dev/null

# Wait for connection to succeed
for i in $(seq 1 $TIMEOUT); do
    STATE=$(nmcli -t -f DEVICE,STATE dev | grep "^$INTERFACE:" | cut -d: -f2)
    if [ "$STATE" == "connected" ]; then
        exit 0
    fi
    sleep 1
done

# No Wi-Fi after timeout, bring up AP
nmcli con up "$AP_NAME"
