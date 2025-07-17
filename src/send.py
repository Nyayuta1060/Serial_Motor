import sys
import serial

if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} <serial_port> <value>")
    print("  <value>: -25000~25000, or 'i', or 'o'")
    sys.exit(1)

port = sys.argv[1]
value = sys.argv[2]

ser = serial.Serial(port, 115200, timeout=1)

if value == 'i' or value == 'o':
    ser.write(value.encode())
else:
    try:
        v = int(value)
        if -25000 <= v <= 25000:
            ser.write(f"{v}\n".encode())
        else:
            print("Value out of range")
    except ValueError:
        print("Invalid value")
ser.close()
