from typing import NamedTuple, List, NewType, Tuple, Union

from PIL import Image, ImageFont, ImageDraw


class Point(NamedTuple):
    x: int
    y: int


class PositionInfo(NamedTuple):
    portion: Point
    circle: Point


class ColorImg(NamedTuple):
    circle: Image.Image
    half_circle: Image.Image


HasHalfCircle = NewType('HasHalfCircle', bool)
CircleMatrix = NewType('CircleMatrix', List[List[int]])


class SixGroupPortionMaker:
    portion_rows = [230, 640]
    circle_rows = [380, 790]
    portion_columns = [220, 545, 880]
    circle_columns = [40, 373, 707]

    diameter = 35
    x_gap = 5
    y_gap = 15

    x_range = 7
    y_range = 3

    default_daily_portion = [2.5, 2, 3, 4, 1.5, 4]
    default_each_meal_portion = list(map(lambda i: i/3, default_daily_portion))

    def __init__(self):
        self.img = self.open_element('../nutrition/bg_six_group.png', (1024, 1024))
        oc = self.open_element('../nutrition/orange.png', (self.diameter, self.diameter))
        o_half = self.open_element('../nutrition/o_half.png', (self.diameter, self.diameter))
        self.orange = ColorImg(circle=oc, half_circle=o_half)
        lc = self.open_element('../nutrition/light_blue.png', (self.diameter, self.diameter))
        l_half = self.open_element('../nutrition/l_half.png', (self.diameter, self.diameter))
        self.light_blue = ColorImg(circle=lc, half_circle=l_half)
        bc = self.open_element('../nutrition/blue.png', (self.diameter, self.diameter))
        b_half = self.open_element('../nutrition/b_half.png', (self.diameter, self.diameter))
        self.blue = ColorImg(circle=bc, half_circle=b_half)
        self.empty = self.open_element('../nutrition/empty.png', (self.diameter, self.diameter))
        self.fnt = ImageFont.truetype('../nutrition/ARCENA.ttf', 65)
        self.draw = ImageDraw.Draw(self.img)
        self.positions_info = self.make_positions_info()
        self.position_arrays = self.make_position_arrays(self.positions_info)

    @staticmethod
    def open_element(path: str, size: Tuple[int, int]):
        img = Image.open(path)  # type: Image.Image
        img = img.convert('RGBA')
        img = img.resize(size, Image.BICUBIC)
        return img

    def make_positions_info(self) -> List[PositionInfo]:
        positions_info = []
        for row in range(2):
            for col in range(3):
                p_portion = Point(self.portion_columns[col], self.portion_rows[row])
                p_circle = Point(self.circle_columns[col], self.circle_rows[row])
                group = PositionInfo(p_portion, p_circle)
                positions_info.append(group)
        return positions_info

    def make_position_arrays(self, positions_info: List[PositionInfo]) -> List[CircleMatrix]:
        position_arrays = []
        for pi in positions_info:
            position = pi.circle
            array = [[0] * self.y_range for _ in range(self.x_range)]
            for i in range(self.x_range):
                for j in range(self.y_range):
                    x = position.x + (self.diameter + self.x_gap) * i
                    y = position.y + (self.diameter + self.y_gap) * j
                    array[i][j] = (x, y)
            position_arrays.append(array)
        return position_arrays

    def draw_portion_num(self, position: Point, num: int):
        if num - int(num) != 0:  # if num have decimal part like 4.2
            position = (position.x - 30, position.y)  # shift 30 pixels
            text = "{:.1f}".format(num)
        else:
            position = (position.x, position.y)
            text = str(num)

        self.draw.text(position, text, font=self.fnt, fill=(255, 255, 0))

    def draw_background(self, array):
        for y in range(self.y_range):
            for x in range(self.x_range):
                self.img.paste(self.empty, array[x][y], self.empty)

    @staticmethod
    def calc_how_many_circles(num: Union[int, float]) -> Tuple[int, HasHalfCircle]:
        decimal = num - int(num)
        if decimal < 0.25:
            return int(num), False  # circle numbers, should draw circle
        elif decimal > 0.75:
            return int(num) + 1, False
        else:
            return int(num), True

    def draw_line(self, color_img: ColorImg, array: CircleMatrix, row: int, num: Union[int, float]):
        circle_num, has_half_circle = self.calc_how_many_circles(num)
        for x in range(circle_num):
            self.img.paste(color_img.circle, array[x][row], color_img.circle)
        if has_half_circle:
            self.img.paste(color_img.half_circle, array[circle_num][row], color_img.half_circle)

    def draw_single_group(self, group_index: int, portion: Union[int, float]):
        position_info = self.positions_info[group_index]
        array = self.position_arrays[group_index]

        self.draw_portion_num(position_info.portion, portion)
        self.draw_background(array)
        self.draw_line(self.orange, array, 0, portion)
        self.draw_line(self.light_blue, array, 1, self.default_each_meal_portion[group_index])
        self.draw_line(self.blue, array, 2, self.default_daily_portion[group_index])

    def draw_groups(self, portions: List[Union[int, float]]):
        for index, portion in enumerate(portions):
            self.draw_single_group(index, portion)
