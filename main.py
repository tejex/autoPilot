import asyncio
from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw, VelocityNedYaw,Attitude)


class AutoPilot:
    def __init__(self):
        self.drone = System()

    async def run(self):
        # Connect to the drone
        print("Connecting to the drone...")
        await self.drone.connect(system_address="udp://:14540")
        
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print("Drone connected successfully!")
                break
        await self.armAndTakeOff()
        
        
        await asyncio.sleep(5)
        #Executing more complex movements like moving forward
        await self.moveForward()
        
        # await asyncio.sleep(20)
        # await self.land()

    async def armAndTakeOff(self):
        print("Arming the drone...")
        await self.drone.action.arm()
        
        print("Taking off...")
        await self.drone.action.takeoff()

    async def land(self):
        print("Landing...")
        await self.drone.action.land()
        print("Landed!")
    
    async def moveForward(self):
        drone = self.drone
        
        async for health in drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break
        
        print("-- Setting initial setpoint")
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
        
        print("-- Starting offboard")
        try:
            await drone.offboard.start()
        except OffboardError as error:
            print(f"Starting offboard mode failed \
                    with error code: {error._result.result}")
            print("-- Disarming")
            await drone.action.disarm()
            return

        print("-- Go up at 70% thrust")
        await drone.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.3))
        await asyncio.sleep(2)
        

        print("-- Go 5m North, 0m East, 0m Down within local coordinate system")
        await drone.offboard.set_position_ned(
                PositionNedYaw(5.0, 0.0, 0.0, 0.0))
        await asyncio.sleep(3)
        
        print("-- Turn 180")
        await drone.offboard.set_position_ned(
                PositionNedYaw(0.0, 0.0, 0.0, 180.0))
        await asyncio.sleep(3)
        
        print("-- Go 5m North, 0m East, 0m Down within local coordinate system")
        await drone.offboard.set_position_ned(
                PositionNedYaw(5.0, 0.0, 0.0, 0.0))
        await asyncio.sleep(3)

        await self.land()


if __name__ == "__main__":
    autopilot = AutoPilot()
    asyncio.run(autopilot.run())
