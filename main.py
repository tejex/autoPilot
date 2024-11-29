import asyncio
from mavsdk import System

async def run():
    # Create a System object
    drone = System()
    
    # Connect to the drone
    print("Connecting to the drone...")
    await drone.connect(system_address="udp://:14540")  # Adjust port if necessary
    
    # Wait for the drone to be connected
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected successfully!")
            break

    # Arm the drone
    print("Arming the drone...")
    await drone.action.arm()
    
    # Take off
    print("Taking off...")
    await drone.action.takeoff()
    
    # Hover for 10 seconds
    await asyncio.sleep(40)
    
    # Land
    print("Landing...")
    await drone.action.land()
    print("Landed!")

if __name__ == "__main__":
    asyncio.run(run())
