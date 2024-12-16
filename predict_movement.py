import csv
import joblib
import pandas as pd
import numpy as np
import os
import signal
from djitellopy import tello
from serial import Serial, SerialException  
from serial.tools.list_ports import comports 

# Configuration settings
csv_file = "imu_data.csv"
model_file = "drone_svm_model.pkl"
baud_rate = 115200
timeout = 1

# Gestures to drone API commands translation
gesture_actions = {
    "up": lambda drone: drone.move_up(30),
    "down": lambda drone: drone.move_down(30),
    "left": lambda drone: drone.move_left(30),
    "right": lambda drone: drone.move_right(30),
    "roll": lambda drone: drone.flip("l"),
    "rotate": lambda drone: drone.rotate_counter_clockwise(180),
    "neutral": lambda drone: print("Neutral detected, holding."),
}

drone = None

def classify_imu_data(port):
    """Classifies IMU data from ESP32"""
    global drone
    drone = tello.Tello()
    drone.connect()
    drone.takeoff()
    try:
        with Serial(port, baudrate=baud_rate, timeout=timeout) as ser:
            print(f"Connected to ESP32 on port {port}.")
            ser.reset_input_buffer()  # Clear any stale data

            while True:
                print("\nWaiting for START signal from ESP32...\n")
                
                # **Wait for START signal**
                while True:
                    try:
                        signal_line = ser.readline().decode("utf-8", errors="ignore").strip()
                    except UnicodeDecodeError:
                        continue

                    if signal_line == "START":
                        print("START signal detected. Beginning data collection...")
                        break

                # **Start recording data only after START is received**
                with open(csv_file, mode="w", newline="") as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow(["time", "acce_x", "acce_y", "acce_z", "gyro_x", "gyro_y", "gyro_z"])
                    print(f"File {csv_file} created, now recording IMU data...")

                    while True:
                        try:
                            data_line = ser.readline().decode("utf-8", errors="ignore").strip()
                        except UnicodeDecodeError:
                            continue

                        if data_line == "END":
                            print("END signal detected. Stopping data collection.")
                            break

                        if data_line and data_line.count(",") == 6:
                            csv_writer.writerow(data_line.split(","))
                            print(f"Data received: {data_line}")
                            csvfile.flush()

                if os.path.exists(csv_file):
                    predicted_label = classify_data(csv_file, model_file)
                    print(f"\nPredicted Gesture: {predicted_label}\n")
                    execute_drone_action(drone, predicted_label)
                else:
                    print("Error: Data file not found for classification.")

                reset_csv_file(csv_file)

    except SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if drone:
            try:
                drone.land()
                print("Drone has landed safely.")
            except Exception as e:
                print(f"Error while landing the drone: {e}")


def classify_data(data_file, model_path):
    model = joblib.load(model_path)
    data = pd.read_csv(data_file)

    max_length = 401  
    if len(data) > max_length:
        data = data.iloc[:max_length]

    processed_data = np.pad(data.to_numpy(), ((0, max_length - len(data)), (0, 0)), mode="constant")
    reshaped_data = processed_data.reshape(1, -1)

    try:
        prediction = model.predict(reshaped_data)[0]
        print(f"Prediction: {prediction}")
        return prediction
    except Exception as e:
        print(f"Error while predicting: {e}")
        return "Unknown"


def execute_drone_action(drone, action):
    if action in gesture_actions:
        try:
            gesture_actions[action](drone)
            print(f"Executed action: {action}")
        except Exception as e:
            print(f"Error executing action {action}: {e}")
    else:
        print(f"Unknown action: {action}")


def reset_csv_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

    with open(file_path, mode="w", newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["time", "acce_x", "acce_y", "acce_z", "gyro_x", "gyro_y", "gyro_z"])


def handle_exit_signal(signum, frame):
    """Handle Ctrl+C signal for safe drone landing."""
    global drone
    if drone is not None:
        print("\nCtrl+C detected. Landing the drone...")
        try:
            drone.land()
        except Exception as e:
            print(f"Error during landing: {e}")
        print("Drone has landed. Exiting program.")
    exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit_signal)

    ports = list(comports())
    if not ports:
        print("No ports found. Please check if your ESP32 is connected.")
    else:
        for port in ports:
            print(f" - {port.device}")

    selected_port = input("Enter the port that the ESP32 is attached to: ")
    if selected_port:
        classify_imu_data(selected_port)
    else:
        print("No port selected. Exiting program.")
