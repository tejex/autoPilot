import asyncio
import threading  # <-- Added
import tkinter as tk
from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw)
from math import fmod

class AutoPilot:
    def __init__(self):
        self.drone = System()
        self.altitude = -5.0  # In NED coordinates, 5m above ground
        self.yaw_angle = 0.0  # Start by facing true north.

        # Create a new event loop for our application - runs in a new thread, check below
        self.loop = asyncio.new_event_loop()

        # Starting the event loop for our application on a different thread, different from tkinter's thread
        self.loop_thread = threading.Thread(target=self.start_loop, args=(self.loop,))
        self.loop_thread.start()

        # Flag to indicate if the loop is running
        self.loop_running = True

    def start_loop(self, loop):
        asyncio.set_event_loop(loop)
        try:
            loop.run_forever()
        except Exception as e:
            print(f"Asyncio loop exception: {e}")
        finally:
            loop.close()

    def stop_loop(self):
        
        self.loop_running = False
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.loop_thread.join()

    async def setup_drone(self):
        print("Connecting to the drone...")
        await self.drone.connect(system_address="udp://:14540")

        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print("Drone connected successfully!")
                break

        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break

        # Set initial position setpoint
        await self.drone.offboard.set_position_ned(PositionNedYaw(
            0.0, 0.0, self.altitude, self.yaw_angle))

        try:
            await self.drone.offboard.start()
            print("Offboard started")
        except OffboardError as error:
            print(f"Starting offboard mode failed with error code: {error._result.result}")
            print("-- Disarming")
            await self.drone.action.disarm()
            return

    # -------------Take off and landing functions--------------
    async def armAndTakeOff(self):
        print("Arming the drone...")
        await self.drone.action.arm()
        print("Taking off...")
        await self.drone.action.takeoff()
        
        await self.setup_drone()

        # Wait until the drone reaches the desired altitude
        await asyncio.sleep(5)

    async def land(self):
        print("Landing...")
        await self.drone.action.land()
        print("Landed!")

    # -------------Movement related functions--------------
    async def moveLeft(self, meters):
        print(f"Moving left by {meters} meters")
        drone = self.drone

        # Get current position in NED Coordinates
        async for position in drone.telemetry.position_velocity_ned():
            current_ned_position = position.position
            break

        # Calculating New NED Positions for the drone to move to
        new_north = current_ned_position.north_m
        new_east = current_ned_position.east_m + float(meters)
        new_down = current_ned_position.down_m  # Maintain current height / altitude

        print(f"-- Moving to North: {new_north}, East: {new_east}, Down: {new_down}")

        await drone.offboard.set_position_ned(
            PositionNedYaw(new_north, new_east, new_down, self.yaw_angle))
        await asyncio.sleep(5)  # Wait for the drone to reach the position we requested

    async def moveRight(self, meters):
        print(f"Moving right by {meters} meters")
        drone = self.drone

        async for position in drone.telemetry.position_velocity_ned():
            current_ned_position = position.position
            break

        new_north = current_ned_position.north_m
        new_east = current_ned_position.east_m - float(meters)
        new_down = current_ned_position.down_m

        print(f"-- Moving to North: {new_north}, East: {new_east}, Down: {new_down}")

        await drone.offboard.set_position_ned(
            PositionNedYaw(new_north, new_east, new_down, self.yaw_angle))
        await asyncio.sleep(5)

    async def rotateLeft(self, degrees):
        print(f"Rotating left by {degrees} degrees")
        drone = self.drone

        # Updating the yaw angle
        self.yaw_angle = self.normalize_angle(self.yaw_angle - degrees)

        async for position in drone.telemetry.position_velocity_ned():
            current_ned_position = position.position
            break

        # Maintain other positions, just rotate
        new_north = current_ned_position.north_m
        new_east = current_ned_position.east_m
        new_down = current_ned_position.down_m

        print(f"-- Rotating to yaw angle: {self.yaw_angle} degrees")

        await drone.offboard.set_position_ned(
            PositionNedYaw(new_north, new_east, new_down, self.yaw_angle))
        await asyncio.sleep(5)

    async def rotateRight(self, degrees):
        print(f"Rotating right by {degrees} degrees")
        drone = self.drone

        self.yaw_angle = self.normalize_angle(self.yaw_angle + degrees)

        async for position in drone.telemetry.position_velocity_ned():
            current_ned_position = position.position
            break

        new_north = current_ned_position.north_m
        new_east = current_ned_position.east_m
        new_down = current_ned_position.down_m

        print(f"-- Rotating to yaw angle: {self.yaw_angle} degrees")

        await drone.offboard.set_position_ned(
            PositionNedYaw(new_north, new_east, new_down, self.yaw_angle))
        await asyncio.sleep(5)

    def normalize_angle(self, angle):
        """Normalize the angle to be within [-180, 180] degrees."""
        angle = fmod(angle + 180.0, 360.0)
        if angle < 0:
            angle += 360.0
        return angle - 180.0

    # Method to schedule coroutines thread-safely
    def schedule_coroutine(self, coro):
        if self.loop_running:
            asyncio.run_coroutine_threadsafe(coro, self.loop)
        else:
            print("Event loop is not running.")

def main():
    autopilot = AutoPilot()
    root = tk.Tk()
    root.title("Drone Control Interface")

    # Start the drone setup
    autopilot.schedule_coroutine(autopilot.setup_drone())

    # Button commands
    takeOffButton = tk.Button(
        root,
        text="Takeoff",
        command=lambda: autopilot.schedule_coroutine(autopilot.armAndTakeOff())
    )
    takeOffButton.pack(padx=10, pady=10)

    landButton = tk.Button(
        root,
        text="Land",
        command=lambda: autopilot.schedule_coroutine(autopilot.land())
    )
    landButton.pack(padx=10, pady=10)

    moveRightButton = tk.Button(
        root,
        text="Move Right",
        command=lambda: autopilot.schedule_coroutine(autopilot.moveRight(4))
    )
    
    moveRightButton.pack(padx=10, pady=10)
    
    moveLeftButton = tk.Button(
        root,
        text="Move Left",
        command=lambda: autopilot.schedule_coroutine(autopilot.moveLeft(4))
    )
    moveLeftButton.pack(padx=10, pady=10)

    rotateRightButton = tk.Button(
        root,
        text="Rotate Right",
        command=lambda: autopilot.schedule_coroutine(autopilot.rotateRight(90))
    )
    rotateRightButton.pack(padx=10, pady=10)
    
    rotateLeftButton = tk.Button(
        root,
        text="Rotate Left",
        command=lambda: autopilot.schedule_coroutine(autopilot.rotateLeft(90))
    )
    rotateLeftButton.pack(padx=10, pady=10)

    # Handle closing the Tkinter window
    def on_closing():
        print("Closing application...")
        autopilot.stop_loop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
