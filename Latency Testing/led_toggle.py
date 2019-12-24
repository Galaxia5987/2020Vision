import RPi.GPIO as GPIO


def __init__():
    GPIO.setmode(GPIO.BCM) 
    GPIO.setwarnings(False)
    GPIO.cleanup(18) 
    GPIO.setup(18, GPIO.OUT)

def on():
    print("LED on")
    GPIO.output(18, GPIO.HIGH)


def off():
    print("LED off")
    GPIO.output(18, GPIO.LOW)

