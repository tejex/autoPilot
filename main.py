import asyncio
from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw, Attitude)
from math import fmod

class AutoPilot:
    def __init__(self):
        self.drone = System()
        self.altitude = -5.0  #In NED coordinates, this is 5m above ground, we will maintain this throughout the "mission"
        self.yaw_angle = 0.0  #Start by facing true north.

    async def run(self):
        # Connect to the drone
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
        
        await self.armAndTakeOff()
        
        await asyncio.sleep(5)
        
        print("-- Starting offboard")
        
        # Set initial position setpoint
        await self.drone.offboard.set_position_ned(PositionNedYaw(
            0.0, 0.0, self.altitude, self.yaw_angle))
        
        try:
            await self.drone.offboard.start()
        except OffboardError as error:
            print(f"Starting offboard mode failed with error code: {error._result.result}")
            print("-- Disarming")
            await self.drone.action.disarm()
            return
        
        await asyncio.sleep(5)
        
        await self.moveLeft(4)
        
        await asyncio.sleep(5)
        
        await self.rotateLeft(90)  #Rotating left by 90 degrees, can specify whatever
        
        await asyncio.sleep(5)
        
        await self.rotateRight(90) #Rotating right by 90 degrees, can specify whatever
        
        await asyncio.sleep(5)
        
        await self.moveRight(4)
        
        await asyncio.sleep(5)
        
        await self.land()

    #-------------Take off and landing functions--------------
    async def armAndTakeOff(self):
        print("Arming the drone...")
        await self.drone.action.arm()
        
        print("Taking off...")
        await self.drone.action.takeoff()

    async def land(self):
        print("Landing...")
        await self.drone.action.land()
        print("Landed!")
    #-------------Movement related functions--------------
    async def moveLeft(self, meters):
        print(f"Moving left by {meters} meters")
        drone = self.drone

        #Get current position in NED Coordinates
        async for position in drone.telemetry.position_velocity_ned():
            current_ned_position = position.position
            break 
        
        #Calculating New Ned Positions for the drone to move to
        new_north = current_ned_position.north_m
        new_east = current_ned_position.east_m + float(meters)
        new_down = current_ned_position.down_m  #Maintain current height / altitude

        print(f"-- Moving to North: {new_north}, East: {new_east}, Down: {new_down}")
        
        await drone.offboard.set_position_ned(
            PositionNedYaw(new_north, new_east, new_down, self.yaw_angle))
        await asyncio.sleep(5)  #Sleeping because we need to wait for the drone to reach the position and kinda "stabilize"
    
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

        # Updating the yaw angle, this is kinda responsible for the rotations we can perform with the drone
        self.yaw_angle = self.normalize_angle(self.yaw_angle - degrees)


        async for position in drone.telemetry.position_velocity_ned():
            current_ned_position = position.position
            break

        #we wanna maintain all other current positions, and just rotate the drone
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

if __name__ == "__main__":
    autopilot = AutoPilot()
    asyncio.run(autopilot.run())
