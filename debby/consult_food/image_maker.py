import os
from enum import Enum, auto
from typing import NamedTuple, List, NewType, Tuple, Union

from PIL import Image, ImageFont, ImageDraw


class Point(NamedTuple):
    x: int
    y: int


class TextSize(NamedTuple):
    w: int
    h: int


class PositionInfo(NamedTuple):
    portion: Point
    circle: Point


class ColorImg(NamedTuple):
    circle: Image.Image
    half_circle: Image.Image


HasHalfCircle = NewType('HasHalfCircle', bool)
CircleMatrix = NewType('CircleMatrix', List[List[int]])
Amount = NewType('Amount', Union[int, float])


class AlignRule(Enum):
    center = auto()
    left = auto()
    right = auto()
    bottom = auto()
    top = auto()


class Alignment:
    def __init__(self, position: Point, text_size: TextSize):
        self.position = position
        self.text_size = text_size
        self.rules = {
            AlignRule.center: self.calc_center,
            AlignRule.left: self.calc_left_or_top,
            AlignRule.top: self.calc_left_or_top,
            AlignRule.right: self.calc_right_or_bottom,
            AlignRule.bottom: self.calc_right_or_bottom
        }

    @staticmethod
    def calc_center(position: float, font_size: float):
        return position - font_size / 2

    @staticmethod
    def calc_left_or_top(position: float, font_size: float):
        return position

    @staticmethod
    def calc_right_or_bottom(position: float, font_size: float):
        return position - font_size

    def get_aligned_position(self, rule: Tuple[AlignRule, AlignRule]) -> Tuple[float, float]:
        x = self.rules[rule[0]](self.position.x, self.text_size.w)
        y = self.rules[rule[1]](self.position.y, self.text_size.h)
        return x, y


class SixGroupParameters(NamedTuple):
    grains: Amount
    fruits: Amount
    vegetables: Amount
    protein_foods: Amount
    diaries: Amount
    oil: Amount


class SixGroupPortionMaker:
    portion_rows = [260, 670]
    circle_rows = [380, 790]
    portion_columns = [245, 570, 905]
    circle_columns = [40, 373, 707]

    diameter = 35
    x_gap = 5
    y_gap = 15

    x_range = 7
    y_range = 3

    default_daily_portion = [2.5, 2, 3, 4, 1.5, 4]
    default_each_meal_portion = list(map(lambda i: i / 3, default_daily_portion))

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
            text = "{:.1f}".format(num)
        else:
            text = str(int(num))

        w, h = self.draw.textsize(text, font=self.fnt)
        a = Alignment(position=position, text_size=TextSize(w, h))
        final_position = a.get_aligned_position(rule=(AlignRule.center, AlignRule.center))

        self.draw.text(final_position, text, font=self.fnt, fill=(255, 255, 0))

    def draw_background(self, array):
        for y in range(self.y_range):
            for x in range(self.x_range):
                self.img.paste(self.empty, array[x][y], self.empty)

    @staticmethod
    def calc_how_many_circles(num: Union[int, float]) -> Tuple[int, HasHalfCircle]:
        if num > 7:
            num = 7
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

    def make_img(self, portions: SixGroupParameters):
        portion_list = list(portions)
        for index, portion in enumerate(portion_list):
            self.draw_single_group(index, portion)

    def save(self, file_name: str):
        self.img.convert('RGB')
        self.img.save(file_name)


class CaloriesParameters(NamedTuple):
    sample_name: str
    calories: float
    carbohydrates_grams: float
    carbohydrates_percentages: float
    fat_grams: float
    fat_percentages: float
    protein_grams: float
    protein_percentages: float


class CaloriesMaker:
    class WordProperties(Enum):
        carbohydrates_gram = auto()
        carbohydrates_percentages = auto()
        carbohydrates_bar = auto()
        fat_gram = auto()
        fat_percentages = auto()
        fat_bar = auto()
        protein_gram = auto()
        protein_percentages = auto()
        protein_bar = auto()

    class FontProperties(NamedTuple):
        position: Point
        font_size: int
        rule: Tuple[AlignRule, AlignRule]
        color: Tuple[int, int, int]

    class RectangleProperties(NamedTuple):
        one_hundred_percentage_positions: List[Point]
        color: Tuple[int, int, int]

    nutrition_path = '../nutrition'
    fnt_path = os.path.join(nutrition_path, 'msjhbd.ttc')
    word_properties = {
        WordProperties.carbohydrates_gram: FontProperties(
            position=Point(590, 400),
            font_size=55,
            rule=(AlignRule.right, AlignRule.bottom),
            color=(33, 23, 17)
        ),
        WordProperties.fat_gram: FontProperties(
            position=Point(590, 660),
            font_size=55,
            rule=(AlignRule.right, AlignRule.bottom),
            color=(33, 23, 17)
        ),
        WordProperties.protein_gram: FontProperties(
            position=Point(590, 915),
            font_size=55,
            rule=(AlignRule.right, AlignRule.bottom),
            color=(33, 23, 17)
        ),
        WordProperties.carbohydrates_percentages: FontProperties(
            position=Point(640, 310),
            font_size=50,
            rule=(AlignRule.left, AlignRule.top),
            color=(33, 23, 17)
        ),
        WordProperties.fat_percentages: FontProperties(
            position=Point(640, 570),
            font_size=50,
            rule=(AlignRule.left, AlignRule.top),
            color=(33, 23, 17)
        ),
        WordProperties.protein_percentages: FontProperties(
            position=Point(640, 830),
            font_size=50,
            rule=(AlignRule.left, AlignRule.top),
            color=(33, 23, 17)
        ),
        WordProperties.carbohydrates_bar: RectangleProperties(
            one_hundred_percentage_positions=[Point(640, 390), Point(940, 440)],
            color=(241, 137, 0)
        ),
        WordProperties.fat_bar: RectangleProperties(
            one_hundred_percentage_positions=[Point(640, 650), Point(940, 700)],
            color=(129, 172, 153)
        ),
        WordProperties.protein_bar: RectangleProperties(
            one_hundred_percentage_positions=[Point(640, 910), Point(940, 960)],
            color=(129, 172, 153)
        )
    }

    def __init__(self):
        self.img = Image.open(os.path.join(self.nutrition_path, 'calories.png'))
        self.img = self.img.convert('RGBA')
        self.draw = ImageDraw.Draw(self.img)

    def _draw_text(self, text: str, properties: FontProperties):
        fnt = ImageFont.truetype(self.fnt_path, properties.font_size)
        w, h = self.draw.textsize(text, font=fnt)
        a = Alignment(position=properties.position, text_size=TextSize(w, h))
        position = a.get_aligned_position(rule=properties.rule)
        self.draw.text(position, text, font=fnt, fill=properties.color)

    def draw_sample_name(self, text: str):
        properties = self.FontProperties(
            position=Point(290, 140),
            font_size=45,
            rule=(AlignRule.center, AlignRule.center),
            color=(255, 255, 255)
        )
        self._draw_text(text, properties)

    def draw_calories(self, num: float):
        properties = self.FontProperties(
            position=Point(800, 175),
            font_size=80,
            rule=(AlignRule.right, AlignRule.bottom),
            color=(255, 252, 0)
        )
        self._draw_text("{:.1f}".format(num), properties)

        properties = self.FontProperties(
            position=Point(940, 175),
            font_size=65,
            rule=(AlignRule.right, AlignRule.bottom),
            color=(255, 252, 0)
        )
        self._draw_text("大卡", properties)

    def draw_gram(self, num: float, properties: FontProperties):
        self._draw_text("{:.1f} 克".format(num), properties)

    def draw_percentage(self, percentage: float, properties: FontProperties):
        self._draw_text("{:.1f} %".format(percentage), properties)

    def draw_percentage_bar(self, percentage: float, properties: RectangleProperties):
        p100p = properties.one_hundred_percentage_positions
        p100_width = p100p[1].x - p100p[0].x
        p_width = percentage / 100 * p100_width
        positions = [(p100p[0].x, p100p[0].y), (p100p[0].x + p_width, p100p[1].y)]
        self.draw.rectangle(positions, fill=properties.color)

    def draw_carbohydrates(self, gram: float, percentage: float):
        self.draw_gram(gram, self.word_properties[self.WordProperties.carbohydrates_gram])
        self.draw_percentage(percentage, self.word_properties[self.WordProperties.carbohydrates_percentages])
        self.draw_percentage_bar(percentage, self.word_properties[self.WordProperties.carbohydrates_bar])

    def draw_fat(self, gram: float, percentage: float):
        self.draw_gram(gram, self.word_properties[self.WordProperties.fat_gram])
        self.draw_percentage(percentage, self.word_properties[self.WordProperties.fat_percentages])
        self.draw_percentage_bar(percentage, self.word_properties[self.WordProperties.fat_bar])

    def draw_protein(self, gram: float, percentage: float):
        self.draw_gram(gram, self.word_properties[self.WordProperties.protein_gram])
        self.draw_percentage(percentage, self.word_properties[self.WordProperties.protein_percentages])
        self.draw_percentage_bar(percentage, self.word_properties[self.WordProperties.protein_bar])

    def make_img(self, properties: CaloriesParameters):
        self.draw_sample_name(properties.sample_name)
        self.draw_calories(properties.calories)
        self.draw_carbohydrates(properties.carbohydrates_grams, properties.carbohydrates_percentages)
        self.draw_fat(properties.fat_grams, properties.fat_percentages)
        self.draw_protein(properties.protein_grams, properties.protein_percentages)

    def save(self, file_name: str):
        self.img.convert('RGB')
        self.img.save(file_name)


def run():
    processor = SixGroupPortionMaker()
    processor.make_img(SixGroupParameters(1, 0, 0, 0, 0, 1))

    properties = CaloriesParameters(
        sample_name="珍珠奶茶珍珠奶茶",
        calories=1289.5,
        carbohydrates_grams=129,
        carbohydrates_percentages=86,
        fat_grams=20,
        fat_percentages=10,
        protein_grams=4,
        protein_percentages=4
    )
    cm = CaloriesMaker()
    cm.make_img(properties)


if __name__ == '__main__':
    run()
