#!/bin/sh
# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# AMPS i2s slave address
left_slave_addr=0x3A
right_slave_addr=0x38

# Left channel init sequence - slave address 0x3A
max98388_left_init_sequence="
    0x2000 0x0000
    0x2001 0x0000
    0x2002 0x0000
    0x2004 0x0006
    0x2005 0x0000
    0x2020 0x000A
    0x2031 0x0058
    0x2032 0x0008  # nominal speaker load resistance: 4 ohm, default
    0x2033 0x0002  # speaker mon duration: 50ms, default
    0x2037 0x0001
    0x2040 0x0061  # PCM Mode Config: 16bit, TDM mode 1 (1 BCLK delay from LRCLK)
    0x2041 0x0014  # PCM Clock Setup (PCM_BSEL): 64, falling edge
    0x2042 0x0088  # PCM Sample Rate Setup: 48kHz I/V, 48kHz Playback
    0x2044 0x0004  # PCM Tx Control 1 (Voltage)
    0x2045 0x0006  # PCM Tx Control 2 (Current)
    0x2050 0x00FF  # PCM_TX_SLOT_HIZ 1
    0x2051 0x00FF  # PCM_TX_SLOT_HIZ 2
    0x2052 0x00FF
    0x2053 0x00FF
    0x2054 0x00FF
    0x2055 0x00FF
    0x2056 0x00FF
    0x2057 0x00FF
    0x2058 0x0000  # PCM Rx Source 1: output of mono mixer is Channel 0
    0x2059 0x0000  # PCM Rx Source 2: downmixer ch1/0 source: PCM input channel 0/0
    0x205C 0x0001
    0x205D 0x0003  # PCM Tx Source Enables: Enable current/voltage feedback
    0x205E 0x0001  # PCM Rx Enable: Enable
    0x205F 0x0001  # PCM Tx Enable: Enable
    0x2090 0x0000  # Speaker Channel Volume Control: 0dB
    0x2091 0x0000  # Speaker Channel Configuration
    0x2092 0x0003  # Speaker Amplifier Output Configuration: peak output RMS +6dB, +12dB
    0x2093 0x0001
    0x2094 0x0000
    0x209E 0x0000  # Speaker Channel Pink Noise Enable: disabled
    0x209F 0x0001  # Speaker Channel and Amp Enable: enabled
    0x20A0 0x0003
    0x20A7 0x0003  # IV Data Enables: Current/Voltage enabled
    0x20E0 0x000F  # Brownout Protection ALC Threshold: 2.5V / 5V
    0x20E1 0x0020
    0x20E2 0x0006
    0x20E3 0x0002
    0x20E4 0x0033
    0x20EE 0x0000
    0x20EF 0x0000
    0x210E 0x0008
    0x210F 0x0001  # Global Enable: power up
"

# Right channel init sequence - slave address 0x38
max98388_right_init_sequence="
    0x2000 0x0000
    0x2001 0x0000
    0x2002 0x0000
    0x2004 0x0006
    0x2005 0x0000
    0x2020 0x000A
    0x2031 0x0058
    0x2032 0x0008  # nominal speaker load resistance: 4 ohm, default
    0x2033 0x0002  # speaker mon duration: 50ms, default
    0x2037 0x0001
    0x2040 0x0061  # PCM Mode Config: 16bit, TDM mode 1 (1 BCLK delay from LRCLK)
    0x2041 0x0014  # PCM Clock Setup (PCM_BSEL): 64, falling edge
    0x2042 0x0088  # PCM Sample Rate Setup: 48kHz I/V, 48kHz Playback
    0x2044 0x0000  # PCM Tx Control 1 (Voltage)
    0x2045 0x0002  # PCM Tx Control 2 (Current)
    0x2050 0x00FF  # PCM_TX_SLOT_HIZ 1
    0x2051 0x00FF  # PCM_TX_SLOT_HIZ 2
    0x2052 0x00FF
    0x2053 0x00FF
    0x2054 0x00FF
    0x2055 0x00FF
    0x2056 0x00FF
    0x2057 0x00FF
    0x2058 0x0000  # PCM Rx Source 1: output of mono mixer is Channel 0
    0x2059 0x0001  # PCM Rx Source 2: downmixer ch1/0 source: PCM input channel 0/1
    0x205C 0x0001
    0x205D 0x0003  # PCM Tx Source Enables: Enable current/voltage feedback
    0x205E 0x0001  # PCM Rx Enable: Enable
    0x205F 0x0001  # PCM Tx Enable: Enable
    0x2090 0x0000  # Speaker Channel Volume Control: 0dB
    0x2091 0x0000  # Speaker Channel Configuration
    0x2092 0x0003  # Speaker Amplifier Output Configuration: peak output RMS +6dB, +12dB
    0x2093 0x0001
    0x2094 0x0000
    0x209E 0x0000  # Speaker Channel Pink Noise Enable: disabled
    0x209F 0x0001  # Speaker Channel and Amp Enable: enabled
    0x20A0 0x0003
    0x20A7 0x0003  # IV Data Enables: Current/Voltage enabled
    0x20E0 0x000F  # Brownout Protection ALC Threshold: 2.5V / 5V
    0x20E1 0x0020
    0x20E2 0x0006
    0x20E3 0x0002
    0x20E4 0x0033
    0x20EE 0x0000
    0x20EF 0x0000
    0x210E 0x0008
    0x210F 0x0001  # Global Enable: power up
"

# Function: max98388_setup
# Usage: max98388_setup <slave_addr> <init_sequence>
# Args:
#   $1 - slave address (e.g., 0x3A)
#   $2 - init sequence data string
max98388_setup() {
    slave_addr=$1
    init_sequence=$2

    echo "$init_sequence" | awk 'NF >= 2 { print $1, $2 }' | while read -r reg_addr value; do
        res=$(mst com_port -t i2c -b 2 -d $slave_addr -w 16 -r $reg_addr -x $value)
        if [ "$res" = "" ]; then
            echo "Write Fail: slave=$slave_addr reg=$reg_addr value=$value"
            return 1
        fi
    done
}

# Initialize Left Channel
echo "MAX98388 Left Channel Initialization ($left_slave_addr)"
max98388_setup $left_slave_addr "$max98388_left_init_sequence"
if [ $? -ne 0 ]; then
    exit 1
fi

# Initialize Right Channel
echo "MAX98388 Right Channel Initialization ($right_slave_addr)"
max98388_setup $right_slave_addr "$max98388_right_init_sequence"
if [ $? -ne 0 ]; then
    exit 1
fi

echo "Initialization complete."
