from app.palette import GARTIC_PALETTE


class Color:
    def __init__(self, name: str, r: int, g: int, b: int) -> None:
        self.name = name
        self.R = r
        self.G = g
        self.B = b
        self.RGB = (r, g, b)
        self.x = 0
        self.y = 0

    def printData(self) -> None:
        print(f"{self.name}: X: {self.x} Y: {self.y}")


allColors = [Color(color.name, *color.rgb) for color in GARTIC_PALETTE]

black = allColors[0]
gray = allColors[1]
blue = allColors[2]
white = allColors[3]
lightGray = allColors[4]
lightBlue = allColors[5]
green = allColors[6]
brown = allColors[7]
lightBrown = allColors[8]
lightGreen = allColors[9]
red = allColors[10]
orange = allColors[11]
uglyBrown = allColors[12]
purple = allColors[13]
skin = allColors[14]
yellow = allColors[15]
pink = allColors[16]
lightPink = allColors[17]
