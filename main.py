import asyncio
from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw, Attitude)


class AutoPilot:
    def __init__(self):
        self.drone = System()
        self.altitude = -5.0  # Desired altitude in NED coordinates (negative Down)

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
        await self.drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, self.altitude, 0.0))
        
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

        # Get current position in NED
        async for position in drone.telemetry.position_velocity_ned():
            current_ned_position = position.position
            break  # Get only one value

        new_north = current_ned_position.north_m
        new_east = current_ned_position.east_m + float(meters)
        new_down = current_ned_position.down_m  # Maintain current altitude

        print(f"-- Moving to North: {new_north}, East: {new_east}, Down: {new_down}")
        
        await drone.offboard.set_position_ned(
            PositionNedYaw(new_north, new_east, new_down, 0.0))
        await asyncio.sleep(5)  # Wait for the drone to reach the position
    
    async def moveRight(self, meters):
        print(f"Moving right by {meters} meters")
        drone = self.drone

        # Get current position in NED
        async for position in drone.telemetry.position_velocity_ned():
            current_ned_position = position.position
            break  # Get only one value

        new_north = current_ned_position.north_m
        new_east = current_ned_position.east_m - float(meters)
        new_down = current_ned_position.down_m  # Maintain current altitude

        print(f"-- Moving to North: {new_north}, East: {new_east}, Down: {new_down}")
        
        await drone.offboard.set_position_ned(
            PositionNedYaw(new_north, new_east, new_down, 0.0))
        await asyncio.sleep(5)  # Wait for the drone to reach the position

    async def moveUp(self):
        drone = self.drone
        
        print("-- Going up at 40% thrust")
        await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.4))
        await asyncio.sleep(2)
    
    async def moveDown(self):
        drone = self.drone
        
        print("-- Going down at -40% thrust")
        await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, -0.4))
        await asyncio.sleep(2)


if __name__ == "__main__":
    autopilot = AutoPilot()
    asyncio.run(autopilot.run())
