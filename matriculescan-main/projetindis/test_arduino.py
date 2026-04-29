from arduino_controller import ArduinoController
import time

def test_arduino():
    print("--- ALPR Arduino Test Script ---")
    
    # Try real connection first, fallback to simulation
    arduino = ArduinoController(simulate=False)
    
    if arduino.simulate:
        print("[!] Running in SIMULATION mode.")
    else:
        print("[+] Arduino connected and ready.")

    try:
        print("\n1. Testing SCAN LED (Pin 8)...")
        arduino.indicate_scan()
        time.sleep(2)
        
        print("2. Testing AUTHORIZED LED (Pin 12)...")
        arduino.indicate_authorized()
        time.sleep(4) # Wait for the 3s ON time in Arduino sketch
        
        print("3. Testing STATUS request...")
        status = arduino.get_status()
        print(f"Arduino Response: {status}")
        
        print("\n4. Testing manual commands...")
        arduino.send_command("SCAN")
        time.sleep(1)
        arduino.send_command("AUTHORIZED")
        time.sleep(3)

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    finally:
        arduino.close()
        print("\n--- Test Finished ---")

if __name__ == "__main__":
    test_arduino()
