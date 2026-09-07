"""Keyboard input provider. Key tokens come from the host adapter, never bpy."""

from .controller import NormalizedCommand, SIDES

# token: (instrument identity, normalized rate channel, direction)
KEY_BINDINGS = {
    "W": ("LEFT", "pitch", 1), "S": ("LEFT", "pitch", -1),
    "A": ("LEFT", "yaw", -1), "D": ("LEFT", "yaw", 1),
    "Q": ("LEFT", "insertion", 1), "E": ("LEFT", "insertion", -1),
    "Z": ("LEFT", "rotation", -1), "X": ("LEFT", "rotation", 1),
    "F": ("LEFT", "jaw", 1), "G": ("LEFT", "jaw", -1),
    "UP_ARROW": ("RIGHT", "pitch", 1), "DOWN_ARROW": ("RIGHT", "pitch", -1),
    "LEFT_ARROW": ("RIGHT", "yaw", -1), "RIGHT_ARROW": ("RIGHT", "yaw", 1),
    "PAGE_UP": ("RIGHT", "insertion", 1), "PAGE_DOWN": ("RIGHT", "insertion", -1),
    "N": ("RIGHT", "rotation", -1), "M": ("RIGHT", "rotation", 1),
    "J": ("RIGHT", "jaw", 1), "K": ("RIGHT", "jaw", -1),
}


class KeyboardInput:
    def __init__(self):
        self.held = set()

    def key(self, token, pressed):
        if token not in KEY_BINDINGS:
            return False
        if pressed:
            self.held.add(token)
        else:
            self.held.discard(token)
        return True

    def clear(self):
        self.held.clear()

    def commands(self):
        values = {side: {} for side in SIDES}
        for key in sorted(self.held):
            side, channel, sign = KEY_BINDINGS[key]
            values[side][channel] = values[side].get(channel, 0) + sign
        return [NormalizedCommand(side, **values[side]) for side in SIDES]
