import serial
import time

SERIAL_PORT = 'COM6'
BAUD_RATE = 9600
TIMEOUT = 1

def calculate_bcc(data_bytes):
    bcc = 0
    for b in data_bytes:
        bcc ^= b
    return bcc

def build_command(command_bytes):
    length = len(command_bytes)
    full_command = [0x01, length] + command_bytes
    bcc = calculate_bcc(full_command[1:])
    full_command.append(bcc)
    return bytes(full_command)

def parse_response(data):
    if len(data) < 4:
        return None
    start = data[0]
    length = data[1]
    payload = data[2:-1]
    bcc = data[-1]
    if calculate_bcc(data[1:-1]) != bcc:
        return None
    return payload.hex().upper()

def main():
    last_tag = None
    last_time = 0
    tag_display_interval = 5  # seconds

    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
            command = build_command([0x08, 0xC8])  # 200 ms burst

            while True:
                ser.write(command)
                time.sleep(0.1)
                if ser.in_waiting:
                    data = ser.read(ser.in_waiting)
                    tag = parse_response(data)
                    now = time.time()
                    if tag:
                        if tag != last_tag or (now - last_time) > tag_display_interval:
                            print(f"Tag detected: {tag}")
                            last_tag = tag
                            last_time = now
                time.sleep(0.4)
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()
