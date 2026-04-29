import serial
import serial.tools.list_ports
import time
import threading

class ArduinoController:
    def __init__(self, simulate=True, baudrate=9600, timeout=1):
        self.simulate = simulate
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.lock = threading.Lock()
        
        if not self.simulate:
            self.connect()

    def connect(self):
        """Attempts to auto-detect and connect to the Arduino."""
        if self.simulate:
            return

        ports = serial.tools.list_ports.comports()
        arduino_port = None
        
        # Simple heuristic to find Arduino (CH340 or Arduino in description)
        for port in ports:
            if "Arduino" in port.description or "CH340" in port.description:
                arduino_port = port.device
                break
        
        # Fallback to the first available port if we couldn't identify it by description
        if not arduino_port and len(ports) > 0:
            arduino_port = ports[0].device
            
        if arduino_port:
            try:
                self.serial_conn = serial.Serial(arduino_port, self.baudrate, timeout=self.timeout)
                time.sleep(2) # Wait for Arduino to reset after connection
                print(f"[Arduino] Connected to {arduino_port}")
            except Exception as e:
                print(f"[Arduino Error] Could not connect to {arduino_port}: {e}")
                self.serial_conn = None
        else:
            print("[Arduino Error] No serial ports found. Running in simulation mode.")
            self.simulate = True

    def send_command(self, command):
        """Sends a command to the Arduino."""
        with self.lock:
            if self.simulate:
                print(f"[Arduino Sim] Sent: {command}")
                return True
                
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.write(f"{command}\n".encode('utf-8'))
                    return True
                except Exception as e:
                    print(f"[Arduino Error] Failed to send command: {e}")
                    # Try to reconnect on next attempt
                    self.serial_conn.close()
                    self.serial_conn = None
                    return False
            else:
                # Try to reconnect
                self.connect()
                if self.serial_conn and self.serial_conn.is_open:
                    return self.send_command(command)
                return False

    def get_status(self):
        """Requests status from the Arduino and reads the response."""
        with self.lock:
            if self.simulate:
                return "STATUS: SIMULATED"
                
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.write(b"STATUS\n")
                    response = self.serial_conn.readline().decode('utf-8').strip()
                    return response
                except Exception as e:
                    print(f"[Arduino Error] Failed to read status: {e}")
                    return "ERROR: Connection lost"
            return "ERROR: Not connected"

    def indicate_scan(self):
        """Triggered when any plate is scanned (Pin 8)."""
        self.send_command("SCAN")

    def indicate_authorized(self):
        """Triggered when an authorized plate is scanned (Pin 12)."""
        self.send_command("AUTHORIZED")

    def close(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("[Arduino] Connection closed.")
