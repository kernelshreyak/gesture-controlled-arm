from controller import Robot
import math

def setMotorPosition(motorDeviceName, position_degrees):
    motor = robot.getDevice(motorDeviceName)
    
    # Very high values → almost instant ramp-up and high cruise speed
    motor.setVelocity(100.0)         # was 50 → try 80–200; higher = faster
    motor.setAcceleration(-1.0)      # -1 = infinite acceleration (no ramp limit)
                                     # Alternative: very high number like 500–1000
    motor.setPosition(math.radians(position_degrees))

robot = Robot()
timestep = int(robot.getBasicTimeStep())

# Apply to all motors at once (still non-blocking / parallel)
setMotorPosition('palm_motor', 80)
setMotorPosition('indexfinger_motor0', 90)
setMotorPosition('indexfinger_motor1', 80)

while robot.step(timestep) != -1:
    pass