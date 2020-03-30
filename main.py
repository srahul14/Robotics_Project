#
# This file is the one run on the ItsyBitsy. Only put main (final production) code here
#

from time import sleep
import board
import digitalio
import pulseio
from adafruit_motor import servo
import displayio
import terminalio
from adafruit_st7735r import ST7735R
import adafruit_imageload
import random

row0 = digitalio.DigitalInOut(board.A0)
row0.direction = digitalio.Direction.INPUT
row0.pull = digitalio.Pull.UP

row1 = digitalio.DigitalInOut(board.A1)
row1.direction = digitalio.Direction.INPUT
row1.pull = digitalio.Pull.UP

row2 = digitalio.DigitalInOut(board.A2)
row2.direction = digitalio.Direction.INPUT
row2.pull = digitalio.Pull.UP

col0 = digitalio.DigitalInOut(board.D9)
col0.direction = digitalio.Direction.OUTPUT
col0.value = 1

col1 = digitalio.DigitalInOut(board.D7)
col1.direction = digitalio.Direction.OUTPUT
col1.value = 1

col2 = digitalio.DigitalInOut(board.D5)
col2.direction = digitalio.Direction.OUTPUT
col1.value = 1

mic1 = digitalio.DigitalInOut(board.D3)
mic1.direction = digitalio.Direction.INPUT

mic2 = digitalio.DigitalInOut(board.D4)
mic2.direction = digitalio.Direction.INPUT

# create a PWMOut object on Pin D10.
pwm10 = pulseio.PWMOut(board.D10, duty_cycle=2 ** 15, frequency=50)
# create a PWMOut object on Pin D11.
pwm11 = pulseio.PWMOut(board.D11, duty_cycle=2 ** 15, frequency=50)
# create a PWMOut object on Pin D12.
pwm12 = pulseio.PWMOut(board.D12, duty_cycle=2 ** 15, frequency=50)
# create a PWMOut object on Pin D13.
pwm13 = pulseio.PWMOut(board.D13, duty_cycle=2 ** 15, frequency=50)

# Create 4 servo objects
lfoot = servo.Servo(pwm11)
rfoot = servo.Servo(pwm12)
lhole = servo.Servo(pwm10)
rhole = servo.Servo(pwm13)

lfoot_initial_angle = 85
rfoot_initial_angle = 96
lhole_initial_angle = 139
rhole_initial_angle = 45

# for lcd
group = displayio.Group(scale=2, max_size=1)
pics = [["/gifs/dance1.bmp", "/gifs/laugh.bmp", "/gifs/kiss.bmp", "/gifs/laugh.bmp", "/gifs/kiss.bmp"],
        ["/gifs/dance2.bmp", "/gifs/angel.bmp", "/gifs/laugh.bmp", "/gifs/angel.bmp", "/gifs/laugh.bmp"],
        ["/gifs/march.bmp", "/gifs/kiss.bmp", "/gifs/march.bmp", "/gifs/kiss.bmp", "/gifs/march.bmp"],
        ["/gifs/retreat.bmp", "/gifs/sweat.bmp", "/gifs/retreat.bmp", "/gifs/sweat.bmp", "/gifs/retreat.bmp"],
        ["/gifs/jmp.bmp", "/gifs/laugh.bmp", "/gifs/jmp.bmp", "/gifs/laugh.bmp", "/gifs/jmp.bmp"],
        ["/gifs/twerk.bmp", "/gifs/angel.bmp", "/gifs/twerk.bmp", "/gifs/angel.bmp", "/gifs/twerk.bmp"]]

# music setup
piezo = pulseio.PWMOut(board.D2, duty_cycle=0, frequency=440, variable_frequency=True)


# lcd functions
# lcd functions
def setup_display():
    displayio.release_displays()

    spi = board.SPI()
    tft_cs = board.A5
    tft_dc = board.A3

    displayio.release_displays()
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.A4)

    return ST7735R(display_bus, width=128, height=128, colstart=2, rowstart=1, rotation=180)


display = setup_display()
groupc = 0


def drawEmoji(text):
    global group
    global groupc

    bitmap = displayio.Bitmap(128, 128, 1)
    # try make a 9 grid version
    bitmap, palette = adafruit_imageload.load(text,
                                              bitmap=displayio.Bitmap,
                                              palette=displayio.Palette)

    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)

    if groupc is 0:
        group.append(tile_grid)
    else:
        group.pop()
        group.append(tile_grid)

    groupc = 1


# for keypad

def scan_keypad():
    for i in range(0, 3):
        interrupted, pinStr = check_pin(i)
        if interrupted:
            return pinStr
    return "False"  # Check here


def check_pin(pinNum):
    char = "bla"
    switch = 0
    if pinNum == 0:
        # Send a low to check which row is on
        col0.value = 0
        rowNum = scan_rows()
        if rowNum < 0:
            switch = 1
            # Do nothing
        elif rowNum == 0:
            char = "1"
        elif rowNum == 1:
            char = "2"
        elif rowNum == 2:
            char = "3"
            # Key pressed is col0 rowNum
        col0.value = 1
    elif pinNum == 1:
        col1.value = 0
        rowNum = scan_rows()
        if rowNum < 0:
            switch = 1
            # Do nothing
        elif rowNum == 0:
            char = "4"
        elif rowNum == 1:
            char = "5"
        elif rowNum == 2:
            char = "6"
        col1.value = 1
    elif pinNum == 2:
        col2.value = 0
        rowNum = scan_rows()
        if rowNum < 0:
            switch = 1
            # Do nothing
        elif rowNum == 0:
            char = "7"
        elif rowNum == 1:
            char = "8"
        elif rowNum == 2:
            char = "9"
            # Key pressed is col2 rowNum
        col2.value = 1
    if not switch:
        print(char)
    return [not switch, char]


def scan_rows():
    if row0.value == 0:
        return 0
    elif row1.value == 0:
        return 1
    elif row2.value == 0:
        return 2
    else:
        return -1


# Records the current state that the program is in so that it can pause and resume operation as needed.
current_mode = "none"
maintain_move = False
use_sound_sensors = False
play_audio = False

# Each dance move should be stored in the list and broken into individual movements in the inner list.
dance_moves = [
    [  # moves for the first dance
        [('lfoot', lfoot_initial_angle + 70), ('lhole', lhole_initial_angle + 15), ('rfoot', rfoot_initial_angle - 70),
         ('rhole', rhole_initial_angle - 15)],
        [('lfoot', lfoot_initial_angle + 60), ('lhole', lhole_initial_angle + 5), ('rfoot', rfoot_initial_angle - 60),
         ('rhole', rhole_initial_angle - 5)],
        [('lfoot', lfoot_initial_angle + 50), ('lhole', lhole_initial_angle - 5), ('rfoot', rfoot_initial_angle - 50),
         ('rhole', rhole_initial_angle + 5)],
        [('lfoot', lfoot_initial_angle + 40), ('lhole', lhole_initial_angle - 15), ('rfoot', rfoot_initial_angle - 40),
         ('rhole', rhole_initial_angle + 15)],
        [('lfoot', lfoot_initial_angle + 30), ('lhole', lhole_initial_angle - 25), ('rfoot', rfoot_initial_angle - 30),
         ('rhole', rhole_initial_angle + 25)],
        [('lfoot', lfoot_initial_angle + 20), ('lhole', lhole_initial_angle - 35), ('rfoot', rfoot_initial_angle - 20),
         ('rhole', rhole_initial_angle + 35)],
        [('lfoot', lfoot_initial_angle + 10), ('lhole', lhole_initial_angle - 45), ('rfoot', rfoot_initial_angle - 10),
         ('rhole', rhole_initial_angle + 45)],
        [('lfoot', lfoot_initial_angle + 0), ('lhole', lhole_initial_angle - 55), ('rfoot', rfoot_initial_angle - 0),
         ('rhole', rhole_initial_angle + 55)],
        [('lfoot', lfoot_initial_angle - 10), ('lhole', lhole_initial_angle - 65), ('rfoot', rfoot_initial_angle + 10),
         ('rhole', rhole_initial_angle + 65)],

        [('lfoot', lfoot_initial_angle - 4), ('lhole', lhole_initial_angle - 67), ('rfoot', rfoot_initial_angle + 4),
         ('rhole', rhole_initial_angle + 67)],
        [('lfoot', lfoot_initial_angle + 2), ('lhole', lhole_initial_angle - 69), ('rfoot', rfoot_initial_angle - 2),
         ('rhole', rhole_initial_angle + 69)],
        [('lfoot', lfoot_initial_angle + 8), ('lhole', lhole_initial_angle - 71), ('rfoot', rfoot_initial_angle - 8),
         ('rhole', rhole_initial_angle + 71)],
        [('lfoot', lfoot_initial_angle + 14), ('lhole', lhole_initial_angle - 73), ('rfoot', rfoot_initial_angle - 14),
         ('rhole', rhole_initial_angle + 73)],
        [('lfoot', lfoot_initial_angle + 20), ('lhole', lhole_initial_angle - 75), ('rfoot', rfoot_initial_angle - 20),
         ('rhole', rhole_initial_angle + 75)],
        [('lfoot', lfoot_initial_angle + 26), ('lhole', lhole_initial_angle - 77), ('rfoot', rfoot_initial_angle - 26),
         ('rhole', rhole_initial_angle + 77)],
        [('lfoot', lfoot_initial_angle + 32), ('lhole', lhole_initial_angle - 79), ('rfoot', rfoot_initial_angle - 32),
         ('rhole', rhole_initial_angle + 79)],
        [('lfoot', lfoot_initial_angle + 38), ('lhole', lhole_initial_angle - 81), ('rfoot', rfoot_initial_angle - 38),
         ('rhole', rhole_initial_angle + 81)],
        [('lfoot', lfoot_initial_angle + 44), ('lhole', lhole_initial_angle - 83), ('rfoot', rfoot_initial_angle - 44),
         ('rhole', rhole_initial_angle + 83)],

        [('lfoot', lfoot_initial_angle + 50), ('lhole', lhole_initial_angle - 85), ('rfoot', rfoot_initial_angle - 50),
         ('rhole', rhole_initial_angle + 85)],

        [('lfoot', lfoot_initial_angle + 44), ('lhole', lhole_initial_angle - 83), ('rfoot', rfoot_initial_angle - 44),
         ('rhole', rhole_initial_angle + 83)],
        [('lfoot', lfoot_initial_angle + 38), ('lhole', lhole_initial_angle - 81), ('rfoot', rfoot_initial_angle - 38),
         ('rhole', rhole_initial_angle + 81)],
        [('lfoot', lfoot_initial_angle + 32), ('lhole', lhole_initial_angle - 79), ('rfoot', rfoot_initial_angle - 32),
         ('rhole', rhole_initial_angle + 79)],
        [('lfoot', lfoot_initial_angle + 26), ('lhole', lhole_initial_angle - 77), ('rfoot', rfoot_initial_angle - 26),
         ('rhole', rhole_initial_angle + 77)],
        [('lfoot', lfoot_initial_angle + 20), ('lhole', lhole_initial_angle - 75), ('rfoot', rfoot_initial_angle - 20),
         ('rhole', rhole_initial_angle + 75)],
        [('lfoot', lfoot_initial_angle + 14), ('lhole', lhole_initial_angle - 73), ('rfoot', rfoot_initial_angle - 14),
         ('rhole', rhole_initial_angle + 73)],
        [('lfoot', lfoot_initial_angle + 8), ('lhole', lhole_initial_angle - 71), ('rfoot', rfoot_initial_angle - 8),
         ('rhole', rhole_initial_angle + 71)],
        [('lfoot', lfoot_initial_angle + 2), ('lhole', lhole_initial_angle - 69), ('rfoot', rfoot_initial_angle - 2),
         ('rhole', rhole_initial_angle + 69)],
        [('lfoot', lfoot_initial_angle - 4), ('lhole', lhole_initial_angle - 67), ('rfoot', rfoot_initial_angle + 4),
         ('rhole', rhole_initial_angle + 67)],

        [('lfoot', lfoot_initial_angle - 10), ('lhole', lhole_initial_angle - 65), ('rfoot', rfoot_initial_angle + 10),
         ('rhole', rhole_initial_angle + 65)],
        [('lfoot', lfoot_initial_angle + 0), ('lhole', lhole_initial_angle - 55), ('rfoot', rfoot_initial_angle - 0),
         ('rhole', rhole_initial_angle + 55)],
        [('lfoot', lfoot_initial_angle + 10), ('lhole', lhole_initial_angle - 45), ('rfoot', rfoot_initial_angle - 10),
         ('rhole', rhole_initial_angle + 45)],
        [('lfoot', lfoot_initial_angle + 20), ('lhole', lhole_initial_angle - 35), ('rfoot', rfoot_initial_angle - 20),
         ('rhole', rhole_initial_angle + 35)],
        [('lfoot', lfoot_initial_angle + 30), ('lhole', lhole_initial_angle - 25), ('rfoot', rfoot_initial_angle - 30),
         ('rhole', rhole_initial_angle + 25)],
        [('lfoot', lfoot_initial_angle + 40), ('lhole', lhole_initial_angle - 15), ('rfoot', rfoot_initial_angle - 40),
         ('rhole', rhole_initial_angle + 15)],
        [('lfoot', lfoot_initial_angle + 50), ('lhole', lhole_initial_angle - 5), ('rfoot', rfoot_initial_angle - 50),
         ('rhole', rhole_initial_angle + 5)],
        [('lfoot', lfoot_initial_angle + 60), ('lhole', lhole_initial_angle + 5), ('rfoot', rfoot_initial_angle - 60),
         ('rhole', rhole_initial_angle - 5)],
        [('lfoot', lfoot_initial_angle + 70), ('lhole', lhole_initial_angle + 15), ('rfoot', rfoot_initial_angle - 70),
         ('rhole', rhole_initial_angle - 15)]
    ],
    [  # moves for the second dance
        [('lfoot', lfoot_initial_angle + 15), ('lhole', lhole_initial_angle - 105), ('rfoot', rfoot_initial_angle - 15),
         ('rhole', rhole_initial_angle - 15)],
        [('lfoot', lfoot_initial_angle + 22.5), ('lhole', lhole_initial_angle - 90),
         ('rfoot', rfoot_initial_angle - 22.5), ('rhole', rhole_initial_angle)],
        [('lfoot', lfoot_initial_angle + 30), ('lhole', lhole_initial_angle - 75), ('rfoot', rfoot_initial_angle - 30),
         ('rhole', rhole_initial_angle + 15)],
        [('lfoot', lfoot_initial_angle + 37.5), ('lhole', lhole_initial_angle - 60),
         ('rfoot', rfoot_initial_angle - 37.5), ('rhole', rhole_initial_angle + 30)],
        [('lfoot', lfoot_initial_angle + 45), ('lhole', lhole_initial_angle - 45), ('rfoot', rfoot_initial_angle - 45),
         ('rhole', rhole_initial_angle + 45)],
        [('lfoot', lfoot_initial_angle + 52.5), ('lhole', lhole_initial_angle - 30),
         ('rfoot', rfoot_initial_angle - 52.5), ('rhole', rhole_initial_angle + 60)],
        [('lfoot', lfoot_initial_angle + 60), ('lhole', lhole_initial_angle - 15), ('rfoot', rfoot_initial_angle - 60),
         ('rhole', rhole_initial_angle + 75)],
        [('lfoot', lfoot_initial_angle + 67.5), ('lhole', lhole_initial_angle), ('rfoot', rfoot_initial_angle - 67.5),
         ('rhole', rhole_initial_angle + 90)],

        [('lfoot', lfoot_initial_angle + 75), ('lhole', lhole_initial_angle + 15), ('rfoot', rfoot_initial_angle - 75),
         ('rhole', rhole_initial_angle + 105)],

        [('lfoot', lfoot_initial_angle + 67.5), ('lhole', lhole_initial_angle), ('rfoot', rfoot_initial_angle - 67.5),
         ('rhole', rhole_initial_angle + 90)],
        [('lfoot', lfoot_initial_angle + 60), ('lhole', lhole_initial_angle - 15), ('rfoot', rfoot_initial_angle - 60),
         ('rhole', rhole_initial_angle + 75)],
        [('lfoot', lfoot_initial_angle + 52.5), ('lhole', lhole_initial_angle - 30),
         ('rfoot', rfoot_initial_angle - 52.5), ('rhole', rhole_initial_angle + 60)],
        [('lfoot', lfoot_initial_angle + 45), ('lhole', lhole_initial_angle - 45), ('rfoot', rfoot_initial_angle - 45),
         ('rhole', rhole_initial_angle + 45)],
        [('lfoot', lfoot_initial_angle + 37.5), ('lhole', lhole_initial_angle - 60),
         ('rfoot', rfoot_initial_angle - 37.5), ('rhole', rhole_initial_angle + 30)],
        [('lfoot', lfoot_initial_angle + 30), ('lhole', lhole_initial_angle - 75), ('rfoot', rfoot_initial_angle - 30),
         ('rhole', rhole_initial_angle + 15)],
        [('lfoot', lfoot_initial_angle + 22.5), ('lhole', lhole_initial_angle - 90),
         ('rfoot', rfoot_initial_angle - 22.5), ('rhole', rhole_initial_angle)],
        [('lfoot', lfoot_initial_angle + 15), ('lhole', lhole_initial_angle - 105), ('rfoot', rfoot_initial_angle - 15),
         ('rhole', rhole_initial_angle - 15)]
    ],
    [  # moves for walking forward
        [("lfoot", lfoot_initial_angle), ("rfoot", rfoot_initial_angle), ("lhole", lhole_initial_angle),
         ("rhole", rhole_initial_angle)],
        [("lhole", lhole_initial_angle - 65)],
        [("lfoot", lfoot_initial_angle + 50)],
        [("lfoot", lfoot_initial_angle), ("rfoot", rfoot_initial_angle), ("lhole", lhole_initial_angle),
         ("rhole", rhole_initial_angle)],
        [("rhole", rhole_initial_angle + 65)],
        [("rfoot", rfoot_initial_angle - 50)]
    ],
    [  # moves for walking backward
        [("lfoot", lfoot_initial_angle + 50), ("rfoot", rfoot_initial_angle), ("lhole", lhole_initial_angle),
         ("rhole", rhole_initial_angle + 90)],
        [("lhole", lhole_initial_angle - 10), ("rhole", rhole_initial_angle + 80)],
        [("lhole", lhole_initial_angle - 20), ("rhole", rhole_initial_angle + 70)],
        [("lhole", lhole_initial_angle - 30), ("rhole", rhole_initial_angle + 60)],
        [("lhole", lhole_initial_angle - 40), ("rhole", rhole_initial_angle + 50)],
        [("lhole", lhole_initial_angle - 50), ("rhole", rhole_initial_angle + 40)],
        [("lhole", lhole_initial_angle - 60), ("rhole", rhole_initial_angle + 30)],
        [("lhole", lhole_initial_angle - 70), ("rhole", rhole_initial_angle + 20)],
        [("lhole", lhole_initial_angle - 80), ("rhole", rhole_initial_angle + 10)],
        [("lhole", lhole_initial_angle - 90), ("rhole", rhole_initial_angle + 0)],

        [("lfoot", lfoot_initial_angle), ("rfoot", rfoot_initial_angle - 50)],
        [("lhole", lhole_initial_angle - 80), ("rhole", rhole_initial_angle + 0)],
        [("lhole", lhole_initial_angle - 70), ("rhole", rhole_initial_angle + 10)],
        [("lhole", lhole_initial_angle - 60), ("rhole", rhole_initial_angle + 20)],
        [("lhole", lhole_initial_angle - 50), ("rhole", rhole_initial_angle + 30)],
        [("lhole", lhole_initial_angle - 40), ("rhole", rhole_initial_angle + 40)],
        [("lhole", lhole_initial_angle - 30), ("rhole", rhole_initial_angle + 50)],
        [("lhole", lhole_initial_angle - 20), ("rhole", rhole_initial_angle + 60)],
        [("lhole", lhole_initial_angle - 10), ("rhole", rhole_initial_angle + 70)],
        [("lhole", lhole_initial_angle - 0), ("rhole", rhole_initial_angle + 80)],
    ],
    [  # moves for jumping
        [("lfoot", lfoot_initial_angle), ("rfoot", rfoot_initial_angle), ("lhole", lhole_initial_angle),
         ("rhole", rhole_initial_angle)],
        [("lfoot", lfoot_initial_angle - 50), ("rfoot", rfoot_initial_angle + 50)]
    ],
    [  # moves for rocking
        [("lfoot", lfoot_initial_angle + 10), ("rfoot", rfoot_initial_angle - 10), ("lhole", lhole_initial_angle - 90),
         ("rhole", rhole_initial_angle + 90)],
        [("lfoot", lfoot_initial_angle + 20), ("rfoot", rfoot_initial_angle - 20)]
    ]

]  # Stored as dance_moves = [index_cur_action[index_cur_movement[(servo, angle)]]].
index_cur_action = 0  # NOTE: Each movement is stored as a list of tuples (servo, angle) specifying all servo
index_cur_movement = 0  # movements needed to be performed for the single movement.
move_delay = [
    3,
    4,
    2,
    1,
    1,
    4
]
cur_delay = 0

# Scores are organized (note, length)
scores = [
    [
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'dh'), ('r', 'h'), ('r', 'q'), ('d5', 'q'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'dh'), ('r', 'w'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('r', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 'e'), ('r', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('r', 'e'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('r', 'e'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('e4', 't'), ('f4', 't'),
        ('fs4', 't'), ('g4', 't'), ('gs4', 't'), ('a4', 't'), ('as4', 't'), ('b4', 't'), ('c5', 't'), ('cs5', 't'),
        ('d5', 't'), ('ds5', 't'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('e5', 's'), ('e5', 's'),
        ('e5', 's'), ('e5', 's'), ('e5', 's'), ('e5', 's'), ('e5', 'e'), ('d5', 's'), ('d5', 's'), ('d5', 's'),
        ('d5', 's'), ('d5', 's'), ('d5', 's'), ('d5', 'e'), ('a4', 's'), ('a4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 'e'), ('e5', 's'), ('e5', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'),
        ('e5', 's'), ('e5', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('e5', 's'), ('e5', 's'),
        ('e5', 's'), ('e5', 's'), ('e5', 's'), ('e5', 's'), ('e5', 'e'), ('d4', 's'), ('d4', 's'), ('d4', 's'),
        ('d4', 's'), ('d4', 's'), ('d4', 's'), ('d4', 'e'), ('a4', 's'), ('a4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 'e'), ('e5', 's'), ('e5', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'),
        ('e5', 's'), ('e5', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('e5', 's'), ('e5', 's'),
        ('e5', 's'), ('e5', 's'), ('e5', 's'), ('e5', 's'), ('e5', 'e'), ('d5', 's'), ('d5', 's'), ('d5', 's'),
        ('d5', 's'), ('d5', 's'), ('d5', 's'), ('d5', 'e'), ('a4', 's'), ('a4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 'e'), ('e5', 's'), ('e5', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'),
        ('e5', 's'), ('e5', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('e5', 's'), ('e5', 's'),
        ('e5', 's'), ('e5', 's'), ('e5', 's'), ('e5', 's'), ('e5', 'e'), ('d5', 's'), ('d5', 's'), ('d5', 's'),
        ('d5', 's'), ('d5', 's'), ('d5', 's'), ('d5', 'e'), ('a4', 's'), ('a4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 'e'), ('e5', 's'), ('e5', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'),
        ('e5', 's'), ('e5', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('e5', 's'), ('e5', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('d5', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('b4', 's'), ('b4', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'),
        ('d5', 'e'), ('d5', 'e'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('b4', 's'),
        ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 's'), ('b4', 'e'), ('e5', 's'), ('e5', 's'),
        ('e5', 's'), ('e5', 's'), ('e5', 's'), ('e5', 's'), ('e5', 'e'), ('d5', 's'), ('d5', 's'), ('d5', 's'),
        ('d5', 's'), ('d5', 's'), ('d5', 's'), ('d5', 'e'), ('a4', 's'), ('a4', 's')
    ],
    [
        ('e4', 'h'), ('g4', 'q'), ('g4', 'q'), ('c4', 'dh'), ('d4', 'q'), ('e4', 'q'), ('f4', 'q'), ('g4', 'q'),
        ('a4', 'q'), ('d4', 'dh'), ('r', 'q'), ('e4', 'h'), ('fs4', 'dq'), ('fs4', 'e'), ('g4', 'dh'), ('a4', 'q'),
        ('b4', 'q'),
        ('b4', 'q'), ('a4', 'q'), ('a4', 'q'), ('g4', 'dh'), ('d4', 'e'), ('e4', 'e'), ('f4', 'dq'), ('e4', 'e'),
        ('d4', 'q'), ('e4', 'e'), ('f4', 'e'), ('g4', 'dq'), ('f4', 'e'), ('e4', 'q'), ('f4', 'e'), ('g4', 'e'),
        ('a4', 'q'), ('g4', 'q'), ('f4', 'q'), ('e4', 'q'), ('d4', 'dh'), ('d4', 'e'), ('e4', 'e'), ('f4', 'dq'),
        ('e4', 'e'), ('d4', 'q'), ('e4', 'e'), ('f4', 'e'), ('g4', 'dq'), ('f4', 'e'), ('e4', 'q'), ('e4', 'q'),
        ('d4', 'q'), ('g4', 'q'), ('g4', 'e'), ('fs4', 'e'), ('e4', 'e'), ('fs4', 'e'), ('g4', 'w'), ('e4', 'h'),
        ('g4', 'dq'), ('g4', 'e'), ('c4', 'w'), ('f4', 'h'), ('a4', 'dq'), ('a4', 'e'), ('d4', 'w'), ('g4', 'h'),
        ('gs4', 'dq'), ('gs4', 'e'), ('a4', 'q'), ('f4', 'q'), ('e4', 'q'), ('d4', 'q'), ('c4', 'h'), ('d4', 'h'),
        ('e4', 'w'), ('g4', 'h'), ('c5', 'dq'), ('c5', 'e'), ('a4', 'q'), ('f4', 'q'), ('e4', 'q'), ('d4', 'q'),
        ('g4', 'h'), ('b3', 'h'), ('c4', 'w')
    ],
    [
        ('f4', 'dq'), ('g4', 'dq'), ('c4', 'q'), ('g4', 'dq'), ('a4', 'dq'), ('c5', 's'), ('as4', 's'), ('a4', 'e'),
        ('f4', 'dq'), ('g4', 'dq'), ('c4', 'he'), ('r', 'q'), ('c4', 's'), ('c4', 's'), ('d4', 's'), ('e4', 'e'),
        ('f4', 's'), ('f4', 'dq'), ('g4', 'dq'), ('c4', 'q'), ('g4', 'dq'), ('a4', 'dq'), ('c5', 's'), ('as4', 's'),
        ('a4', 'e'), ('f4', 'dq'), ('g4', 'dq'), ('c4', 'q'), ('e4', 'e'), ('f4', 'e'), ('f4', 'q'), ('r', 'q'),
        ('f4', 's'), ('f4', 'e'), ('f4', 's'), ('r', 'q'), ('d4', 'e'), ('e4', 'e'), ('f4', 'e'), ('f4', 'e'),
        ('g4', 'e'), ('e4', 'de'), ('d4', 's'), ('c4', 'he'), ('r', 'dq'), ('d4', 'e'), ('d4', 'e'), ('e4', 'e'),
        ('f4', 'e'), ('d4', 'q'), ('c4', 'e'), ('c5', 'e'), ('r', 'e'), ('c5', 'e'), ('g4', 'h'), ('r', 'q'),
        ('d4', 'e'), ('d4', 'e'), ('e4', 'e'), ('f4', 'e'), ('d4', 'e'), ('f4', 'e'), ('g4', 'e'), ('r', 'e'),
        ('e4', 'e'), ('d4', 'e'), ('c4', 'dq'), ('r', 'dq'), ('d4', 'e'), ('d4', 'e'), ('e4', 'e'), ('f4', 'e'),
        ('d4', 'e'), ('c4', 'q'), ('g4', 'e'), ('g4', 'e'), ('g4', 'e'), ('a4', 'e'), ('g4', 'q'), ('r', 'q'),
        ('f4', 'he'), ('g4', 'e'), ('a4', 'e'), ('f4', 'e'), ('g4', 'e'), ('g4', 'e'), ('g4', 'e'), ('a4', 'e'),
        ('g4', 'q'), ('c4', 'q'), ('r', 'h'), ('d4', 'e'), ('e4', 'e'), ('f4', 'e'), ('d4', 'e'), ('r', 'e'),
        ('g4', 'e'), ('a4', 'e'), ('g4', 'dq'), ('c4', 's'), ('d4', 's'), ('f4', 's'), ('d4', 's'), ('a4', 'de'),
        ('a4', 'de'), ('g4', 'dq'), ('c4', 's'), ('d4', 's'), ('f4', 's'), ('d4', 's'), ('g4', 'de'), ('g4', 'de'),
        ('f4', 'de'), ('e4', 's'), ('d4', 'e'), ('c4', 's'), ('d4', 's'), ('f4', 's'), ('d4', 's'), ('f4', 'q'),
        ('g4', 'e'), ('e4', 'de'), ('d4', 's'), ('c4', 'q'), ('c4', 'e'), ('g4', 'q'), ('f4', 'h'), ('c4', 's'),
        ('d4', 's'), ('f4', 's'), ('d4', 's'), ('a4', 'de'), ('a4', 'de'), ('g4', 'dq'), ('c4', 's'), ('d4', 's'),
        ('f4', 's'), ('d4', 's'), ('c5', 'q'), ('e4', 'e'), ('f4', 'de'), ('e4', 's'), ('d4', 'e'), ('c4', 's'),
        ('d4', 's'), ('f4', 's'), ('d4', 's'), ('f4', 'q'), ('g4', 'e'), ('e4', 'de'), ('d4', 's'), ('c4', 'q'),
        ('c4', 'e'), ('g4', 'q'), ('f4', 'h')
    ]
]
# Ensure that the index of the BPM values are the same as the index of the score in the scores list
score_BPM = [
    140,
    120,
    114
]
freq = {"c3": 130.81,
        "cs3": 138.59,
        "d3": 146.83,
        "ds3": 155.56,
        "e3": 164.81,
        "f3": 174.61,
        "fs3": 185.00,
        "g3": 196.00,
        "gs3": 207.65,
        "a3": 220.00,
        "as3": 233.08,
        "b3": 246.94,
        "c4": 261.63,
        "cs4": 277.18,
        "d4": 293.66,
        "ds4": 311.13,
        "e4": 329.63,
        "f4": 349.23,
        "fs4": 369.99,
        "g4": 392.00,
        "gs4": 415.30,
        "a4": 440.00,
        "as4": 466.16,
        "b4": 493.88,
        "c5": 523.25,
        "cs5": 554.37,
        "d5": 587.37,
        "ds5": 622.25,
        "e5": 659.25,
        "f5": 698.46,
        "fs5": 739.99,
        "g5": 783.99,
        "gs5": 830.61,
        "a5": 880.00,
        "as5": 932.33,
        "b5": 987.77,
        "c6": 1046.50
        }

noteLen = {"dw": 6,  # dotted whole note length value
           "w": 4,  # whole note length value
           "dh": 3,  # dotted half note length value
           "h": 2,  # half note length value
           "he": 2.5,  # half note + eigth note length value (used in RickRoll score)
           "dq": 1.5,  # dotted quarter note length value
           "q": 1,  # quarter note length value
           "de": 0.75,  # dotted eigth note length value
           "e": 0.5,  # eigth note length value
           "ds": 0.375,  # dotted sixteeth note length value
           "t": 0.333,  # triplet note length value
           "s": 0.25  # sixteeth note length value
           }


# Controls the servo motors and performs a dance move
#
# As earlier specified, move will be a list containing tuples (servo, angle) specifying all servo movements required
def perform_movement(move):
    global lfoot, rfoot, lhole, rhole

    # parsing the moves to assign the correct angles for each servos
    for servo_actions in move:
        if servo_actions[0] == "lfoot":
            lfoot.angle = servo_actions[1]
        elif servo_actions[0] == "rfoot":
            rfoot.angle = servo_actions[1]
        elif servo_actions[0] == "lhole":
            lhole.angle = servo_actions[1]
        else:
            rhole.angle = servo_actions[1]

# Counts the number of iterations of the current move for random moves
move_iterations = 0
cur_random = False


# Controls the performance of the dance moves
#
# Each dance move needs to be broken up into individual parts / movements and stored in the "dance_moves" list of lists
# The method should return after a single movement is completed
# Ensure "index_cur_movement" is recorded before returning after every movement
def dance():
    global index_cur_action, index_cur_movement, cur_delay, move_iterations

    # Perform the required movement
    perform_movement(dance_moves[index_cur_action][index_cur_movement])

    # If the index at the current move is less than the length, change to the next movement
    if index_cur_movement + 1 < len(dance_moves[index_cur_action]):
        index_cur_movement += 1
    else:
        # Check to see if the next move is valid. Otherwise, reset to the move at index 0
        if not maintain_move or (move_iterations == 1 and cur_random):
            if index_cur_action + 1 < len(dance_moves):
                index_cur_action += 1
            else:
                index_cur_action = 0

            if cur_random:
                move_iterations = 0
                index_cur_action = random.randrange(0,6,1)

        index_cur_movement = 0

    cur_delay = 0


# Checks for interrupts (such as buttons and other sensors)
#
# Sets "current_mode" when an interrupt occurs and/or "index_cur_action"
def check_interrupt():
    global current_mode, maintain_move, index_cur_action, use_sound_sensors, play_audio, index_cur_movement
    global note_dur, song_index, sound_index, cur_delay, lcdIndex, last_update, lcdLastMove, sound_trig_delay
    global sound_sleep, move_iterations, cur_random

    # Check for input on the keypad
    input_str = scan_keypad()
    if input_str != "False":
        index_cur_action = int(input_str)  # This will work only for numbers 0 - 9 (not *, #)

        # Resetting LCD variables
        last_update = 0
        lcdLastMove = 0
        lcdIndex = 0

        # Handle the input action
        if 1 <= index_cur_action <= 6:
            current_mode = "dance"
            maintain_move = True
            index_cur_action = index_cur_action - 1
            index_cur_movement = 0
            cur_delay = 0
        elif index_cur_action == 7:  # Dance with Random moves
            current_mode = "dance"
            maintain_move = False
            index_cur_action = random.randrange(0,6,1)
            index_cur_movement = 0
            cur_delay = 0
            move_iterations = 0
            cur_random = True
        elif index_cur_action == 8:  # Toggle between sound sensors, play sound, none
            if not use_sound_sensors and not play_audio:
                use_sound_sensors = True
                sound_sleep = 0.10
                sound_trig_delay = -3
                print("Sound Sensors: Enable")
            elif use_sound_sensors and not play_audio:
                use_sound_sensors = False
                play_audio = True
                note_dur, song_index, sound_index = 0, random.randrange(0,3,1), 0
                print("Play Audio: Enabled")
                print("Sound Sensors: Disabled")
            elif not use_sound_sensors and play_audio:
                play_silence()
                use_sound_sensors = False
                play_audio = False
                print("Play Audio and Sound Sensors: Disabled")
            index_cur_action = 0
            sleep(0.15)
        elif index_cur_action == 9:  # Stop any move
            index_cur_action = 0

            # If 9 is pressed twice, reset to initial angle
            if current_mode == "none":
                lfoot.angle = lfoot_initial_angle
                rfoot.angle = rfoot_initial_angle
                lhole.angle = lhole_initial_angle
                rhole.angle = rhole_initial_angle
            else:
                current_mode = "none"
                play_silence()
                sleep(0.20)

        # To prevent excessive continuous inputs
        sleep(0.10)


# Stores the last time the display updated (in seconds)
last_update = 0
lcdLastMove = 0
lcdIndex = 0


# Method for updating the TFT display
def update_display():
    global pics, index_cur_action, current_mode, display, last_update, lcdIndex, lcdLastMove

    # Counter to update picture every 0.8 seconds
    if last_update >= 1.5 or index_cur_action is not lcdLastMove:
        # Reset last_update
        last_update = 0

        # Check if the desired image is within the bounds of the image list
        if lcdIndex > 4 or index_cur_action is not lcdLastMove:
            lcdIndex = 0

        # Control the display according to the current state of the program (namely according to the sound sensors)
        if not current_mode == "dance":
            drawEmoji("/gifs/angel.bmp")
        elif two_active:
            drawEmoji("/gifs/index.bmp")
        elif one_active:
            drawEmoji("/gifs/scream.bmp")
        else:
            drawEmoji(pics[index_cur_action][lcdIndex])

        display.show(group)

        lcdIndex += 1
        lcdLastMove = index_cur_action

    else:
        # Increment last_update with the amount of time slept between interrupt checks
        last_update += real_sleep_time


# sound contains a list of the individual tones in a song. This list will be iterated through
sound_index = 0
song_index = 0
note_dur = 0


# Method for playing the sound on the buzzer based upon sound_index and song_index
# Should start sounds to be played and not stop them on method return
def play_sound():
    note = scores[song_index][sound_index][0]
    if note == "r":  # tests to see if the note is a rest, as there is no frequency associated with rest.
        play_silence()  # in case of a rest, there should not be a note played.
    else:
        piezo.frequency = int(freq[note])
        piezo.duty_cycle = 65536 // 2


# Method for silencing the buzzer. Very simple. I dont even know why i did it.
def play_silence():
    piezo.duty_cycle = 0


# Method for checking if a new sound needs to be played based upon the current note duration versus the score
# sound_index and song_index are controlled from this method
# returns True if a new sound should be played
def check_sound():
    global sound_index, song_index, note_dur
    target_beats = noteLen[scores[song_index][sound_index][1]]
    beats_elap = (note_dur / 60) * score_BPM[song_index]

    # Check if at the first note of a song
    if sound_index == 0 and note_dur == 0:
        return True
    # Check if a new sound needs to be played based upon current duration
    elif beats_elap >= target_beats:
        if sound_index == (len(scores[song_index]) - 1):
            sound_index = 0

            if song_index == 2:
                song_index = 0
            else:
                song_index += 1
        else:
            sound_index += 1

        note_dur = 0
        return True
    elif beats_elap >= 0.8 * target_beats:  # if 80% of the note has elapsed, play silence for note separation
        play_silence()

    return False


# Booleans to record if the sensors are active or not
one_active, two_active = False, False
# The delay since the sensors have been recorded as high and the program is currently in buffer period
sound_trig_delay = -3
prev_level_one = [False, False, False]
prev_level_two = [False, False, False]
sound_sleep = 0.10


# Method for updating sound level depending on the number of sound sensors active ("high")
def update_sound_trigger():
    global sound_trig_delay, one_active, two_active, prev_level_one, prev_level_two, sound_sleep
    print(str(sound_sleep))

    if sound_trig_delay < 0:
        one_active = not mic1.value
        two_active = not mic2.value

        if sound_trig_delay == -3:
            prev_level_one[0] = one_active
            prev_level_two[0] = two_active
            sound_trig_delay = -2
            return
        elif sound_trig_delay == -2:
            prev_level_one[1] = one_active
            prev_level_two[1] = two_active
            sound_trig_delay = -1
            return
        else:
            prev_level_one[2] = one_active
            prev_level_two[2] = two_active

            # Determine if the readings are active or not
            one_num_true = 0
            two_num_true = 0
            for i in range(len(prev_level_one)):
                if prev_level_one[i]:
                    one_num_true += 1
                if prev_level_two[i]:
                    two_num_true += 1

            print(str(one_num_true) + " " + str(two_num_true))
            one_active, two_active = False, False

            if one_num_true >= 2:
                one_active = True
            if two_num_true >= 2:
                two_active = True

            print("Sound Sensors Active: " + str(one_active) + " " + str(two_active))

    # Return if the system is not active and no audio is detected
    if not two_active and not one_active and sound_trig_delay == -1:
        sound_trig_delay = -3
        return

    # Check the sensors if they are not currently activated within the buffer period
    if sound_trig_delay == -1:
        sound_trig_delay = 0

        # If one of them is active, set the sleep time
        if two_active:
            sound_sleep = 0.04
        elif one_active:
            sound_sleep = 0.06

    # Turn off the sound activation after the buffer period
    if (sound_trig_delay >= 2 and sound_sleep == 0.04) or (sound_trig_delay >= 2 and sound_sleep == 0.06):
        sound_trig_delay = -3
        sound_sleep = 0.10
        one_active, two_active = False, False
        return

    # Increment the trig_delay depending on the amount of time between method calls (ie real_sleep_time)
    sound_trig_delay += sound_sleep


# Sleep time (in seconds) between movements in an action
real_sleep_time = 0.04

# Main control loop for the program
while True:
    # Sleep between movements in an action
    if use_sound_sensors:
        update_sound_trigger()
        sleep(sound_sleep)
    else:
        sleep(real_sleep_time)

    # Check for interrupts
    check_interrupt()

    # Perform operation depending on the current mode
    if current_mode == "none":
        pass
    elif current_mode == "dance":
        if play_audio:
            if check_sound():
                play_sound()
                dance()
            note_dur += real_sleep_time
        else:
            if cur_delay == move_delay[index_cur_action]:
                dance()
            else:
                cur_delay += 1

    # Update the other components of the system
    update_display()