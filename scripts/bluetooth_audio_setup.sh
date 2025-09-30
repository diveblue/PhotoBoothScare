#!/bin/bash
# bluetooth_audio_setup.sh - Auto-connect Bluetooth speaker

# Replace with your speaker's MAC address
SPEAKER_MAC="XX:XX:XX:XX:XX:XX"

echo "Connecting to Bluetooth speaker..."
bluetoothctl << EOF
power on
connect $SPEAKER_MAC
exit
EOF

# Wait a moment for connection
sleep 3

# Set as default audio output
echo "Setting Bluetooth as default audio output..."
pactl set-default-sink bluez_sink.$(echo $SPEAKER_MAC | tr : _).a2dp_sink

echo "Bluetooth audio setup complete!"