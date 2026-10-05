import paho.mqtt.client as mqtt
import time
import json
import random
import uuid
import sys
from datetime import datetime, timezone
import argparse
import os

# Configuration
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "aura_mqtt")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "changeme_mqtt_password")

class AuraSimulator:
    def __init__(self, robot_id: str, mode: str):
        self.robot_id = robot_id
        self.mode = mode
        
        # Initial State
        self.battery = 100.0
        self.temperature = 22.0
        self.gas_level = 5.0
        self.distance = 100.0
        self.speed = 0.0
        self.is_moving = False
        
        # Setup MQTT
        self.client = mqtt.Client(client_id=f"sim_{robot_id}", protocol=mqtt.MQTTv5)
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"[{self.robot_id}] Connected to MQTT broker (rc={rc})")
        # Subscribe to commands
        self.client.subscribe(f"robot/{self.robot_id}/command", qos=1)
        
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            command = payload.get("command")
            print(f"[{self.robot_id}] Received command: {command}")
            
            if command == "MOVE_FORWARD":
                self.is_moving = True
                self.speed = payload.get("speed", 50)
            elif command == "STOP":
                self.is_moving = False
                self.speed = 0.0
            elif command == "EMERGENCY_STOP":
                self.is_moving = False
                self.speed = 0.0
                self.mode = "EMERGENCY"
                
        except Exception as e:
            print(f"Error parsing command: {e}")

    def generate_telemetry(self) -> dict:
        """Simulate realistic sensor drift."""
        # Battery drains faster when moving
        drain = 0.05 if self.is_moving else 0.01
        self.battery = max(0.0, self.battery - drain)
        
        # Temperature fluctuates
        self.temperature += random.uniform(-0.1, 0.1)
        
        # Distance (mock an obstacle appearing)
        if self.is_moving:
            self.distance = max(5.0, self.distance - random.uniform(1.0, 5.0))
            if self.distance < 20.0 and self.mode != "EMERGENCY":
                # Local safety - auto stop
                print(f"[{self.robot_id}] OBSTACLE DETECTED! Auto-stopping.")
                self.is_moving = False
                self.speed = 0.0
                self.publish_alert("OBSTACLE_DETECTED", "WARNING", "Stopped due to obstacle at 20cm")
        else:
            # Distance randomly changes slightly when stopped (noise)
            self.distance += random.uniform(-1.0, 1.0)
            
        return {
            "robot_id": self.robot_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "battery": round(self.battery, 2),
            "temperature": round(self.temperature, 2),
            "humidity": 45.0 + random.uniform(-2, 2),
            "gas_level": round(self.gas_level, 2),
            "distance": round(self.distance, 2),
            "speed": self.speed,
            "cpu_usage": random.uniform(10.0, 40.0),
            "memory_usage": random.uniform(30.0, 60.0),
        }

    def publish_alert(self, alert_type: str, severity: str, message: str):
        payload = {
            "robot_id": self.robot_id,
            "type": alert_type,
            "severity": severity,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.client.publish(f"robot/{self.robot_id}/alert", json.dumps(payload), qos=2)

    def run(self):
        try:
            self.client.connect(MQTT_HOST, MQTT_PORT, 60)
            self.client.loop_start()
            
            print(f"Starting AURA Simulator for {self.robot_id}...")
            
            counter = 0
            while True:
                # 1. Publish Telemetry (1 Hz)
                telemetry = self.generate_telemetry()
                self.client.publish(f"robot/{self.robot_id}/telemetry", json.dumps(telemetry), qos=0)
                
                # 2. Publish Heartbeat (every 5 seconds)
                if counter % 5 == 0:
                    heartbeat = {
                        "robot_id": self.robot_id,
                        "status": "ONLINE",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    self.client.publish(f"robot/{self.robot_id}/heartbeat", json.dumps(heartbeat), qos=0)
                
                # 3. Simulate specific modes
                if self.mode == "HIGH_GAS" and counter == 10:
                    self.gas_level = 80.0
                    print("Simulating HIGH GAS emergency...")
                    self.publish_alert("HIGH_GAS", "CRITICAL", "Dangerous gas levels detected!")
                    
                counter += 1
                time.sleep(1.0)
                
        except KeyboardInterrupt:
            print("\nShutting down simulator...")
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AURA Robot Simulator")
    parser.add_argument("--robot-id", default="AURA-001", help="Device ID")
    parser.add_argument("--mode", default="NORMAL", help="Simulation scenario")
    args = parser.parse_args()
    
    sim = AuraSimulator(args.robot_id, args.mode)
    sim.run()
