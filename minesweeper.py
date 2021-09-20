import collections.abc
from random import sample
import pygame
import sys
from string import digits

BOMB = pygame.image.load('bomb.gif')
FLAG = pygame.image.load('flag.gif')
BACKGROUND_COLOR = (255, 255, 255)
NUMBERS_COLOR = OUTLINE_COLOR = (0, 0, 0)
UNREVEALED_CELL_COLOR = (255, 143, 38)
REVEALED_CELL_COLOR = (7, 89, 0)
RECTANGLE_COLOR = (191, 191, 191)
FOCUSED_RECTANGLE_COLOR = (255, 0, 0)


def near_row(lst, row: int):
    if row == 0:
        return lst[1]
    if row == len(lst) - 1:
        return lst[-2]
    return [lst[row - 1], lst[row + 1]]


def near_col(lst, row: int, column: int):
    if row == 0:
        return lst[1][column]
    elif row == len(lst) - 1:
        return lst[-2][column]
    return [lst[row - 1][column], lst[row + 1][column]]


def near(lst, row: int, column: int):
    nearby_buttons = []
    nearby_buttons.extend([near_row(lst[row], column)])
    if row > 0:
        nearby_buttons.extend([near_row(lst[row - 1], column)])
    if row < len(lst) - 1:
        nearby_buttons.extend([near_row(lst[row + 1], column)])
    nearby_buttons.extend([near_col(lst, row, column)])
    flat_results = flatten(nearby_buttons)
    return flat_results


def flatten(lst_2d):
    if isinstance(lst_2d, collections.abc.Iterable):
        return [button for i in lst_2d for button in flatten(i)]
    else:
        return [lst_2d]


class Rec:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.flag = False
        self.num = 0
        self.bomb = False
        self.open = False
        self.color = UNREVEALED_CELL_COLOR
        self.rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1)

    def __str__(self):
        x = self.x
        y = self.y
        bomb = self.bomb
        return f'Rectangle x={x}, y={y}, is bomb = {bomb} num = {self.num}'

    def __repr__(self):
        return self.__str__()

    def left_click(self):
        if self.flag or self.open:
            return
        self.open = True
        self.color = REVEALED_CELL_COLOR
        return self.bomb

    def right_click(self):
        if self.color == REVEALED_CELL_COLOR:
            return
        if self.flag:
            self.flag = False
        else:
            self.flag = True


def find_numbers(lst):
    for index_i, row in enumerate(lst):
        for index_j, cell in enumerate(row):
            neighbours = near(lst, index_i, index_j)
            cell.num = len([1 for c in neighbours if c.bomb])


def init_buttons(width, height, bomb_amount, immunity=None):
    board = []
    for i in range(width):
        row = []
        for j in range(height):
            row.append(Rec(i, j))
        board.append(row)
    flat = flatten(board)
    if immunity is not None:
        x = immunity[0]
        y = immunity[1]
        element = board[x][y]
        neighs = near(board, x, y)
        flat.remove(element)
        for button in neighs:
            flat.remove(button)
    for button in sample(flat, k=bomb_amount):
        button.bomb = True
    find_numbers(board)
    return board


class Application:
    ui_width = 150
    ui_height = 50

    def refresh_settings(self):
        settings = self.ui_settings
        width = int(settings[0][1])
        height = int(settings[1][1])
        number_of_mines = int(settings[2][1])
        self.__init__(width, height, number_of_mines)

    def __init__(self, width, height, number_of_mines, immunity=None):
        self.number_of_mines = number_of_mines
        self.height = height
        self.width = width
        self.remain_open = None
        self.game_active = True
        self.buttons = None
        self.move = None
        self.text = ''
        self.ui_settings = []
        self.labels = []
        self.reset_rect = None
        window_height = BLOCK_SIZE * height
        window_width = BLOCK_SIZE * width
        self.font = pygame.font.SysFont('Ariel', int(BLOCK_SIZE * 3))
        self.small_font = pygame.font.SysFont('Ariel', int(BLOCK_SIZE / 2))
        self.screen = pygame.display.set_mode((window_width + 175, max(window_height, 355)))
        self.start_game(immunity)
        self.generate_ui()

    def generate_ui(self):
        width_rect = pygame.Rect(self.width * (BLOCK_SIZE + 1), 50, self.ui_width, self.ui_height)
        self.ui_settings.append([width_rect, str(self.width), False])
        height_rect = pygame.Rect(self.width * (BLOCK_SIZE + 1), 140, self.ui_width, self.ui_height)
        self.ui_settings.append([height_rect, str(self.height), False])
        mines_rect = pygame.Rect(self.width * (BLOCK_SIZE + 1), 240, self.ui_width, self.ui_height)
        self.ui_settings.append([mines_rect, str(self.number_of_mines), False])
        self.reset_rect = pygame.Rect(self.width * (BLOCK_SIZE + 1), 300, self.ui_width, self.ui_height)
        self.labels.append((pygame.Rect(self.width * (BLOCK_SIZE + 1), 10, self.ui_width, self.ui_height), 'Width'))
        self.labels.append((pygame.Rect(self.width * (BLOCK_SIZE + 1), 100, self.ui_width, self.ui_height), 'Height'))
        self.labels.append((pygame.Rect(self.width * (BLOCK_SIZE + 1), 200, self.ui_width, self.ui_height), 'Num of '
                                                                                                            'mines'))

    def start_game(self, immunity=None):
        self.buttons = init_buttons(self.width, self.height, self.number_of_mines, immunity)
        self.remain_open = self.width * self.height - self.number_of_mines
        self.game_active = True
        self.move = 0

    def end_game(self, victory=True):
        self.game_active = False
        self.reveal_all()
        if victory:
            self.text = 'VICTORY'
        else:
            self.text = 'LOST'

    def reveal_all(self):
        for button in flatten(self.buttons):
            button.open = True
            button.color = REVEALED_CELL_COLOR

    def right_click(self, i, j):
        item = self.buttons[i][j]
        item.right_click()

    def first_move_immunity(self, i, j):
        self.start_game((i, j))
        self.move = 1
        self.left_click(i, j)
        self.move = 1

    def left_click(self, i, j):
        item = self.buttons[i][j]
        if item.open is True:
            return
        res = item.left_click()
        if self.move == 0:
            self.first_move_immunity(i, j)
            return
        if res:
            for button in flatten(self.buttons):
                button.open = True
                button.color = REVEALED_CELL_COLOR
            self.end_game(False)
        if res is False:
            if self.buttons[i][j].num == 0:
                self.middle_click(i, j)
            self.remain_open -= 1
            self.move += 1
        return res

    def middle_click(self, i, j):
        neighs = near(self.buttons, i, j)
        for button in neighs:
            self.left_click(button.x, button.y)


def update_cells(screen, buttons, font):
    for index_row, row in enumerate(buttons):
        for index_col, item in enumerate(row):
            rect, color = item.rect, item.color
            draw_rect(screen, color, rect)
            if item.flag:
                rect = NEW_FLAG.get_rect(topleft=(rect[0], rect[1]))
                screen.blit(NEW_FLAG, rect)
            elif item.open:
                if item.bomb:
                    rect = NEW_BOMB.get_rect(topleft=(rect[0], rect[1]))
                    screen.blit(NEW_BOMB, rect)
                    continue
                num = item.num
                if num == 0:
                    continue
                text_width, text_height = font.size(str(num))
                screen.blit(font.render(str(num), True, NUMBERS_COLOR),
                            (rect[0] + rect[2] // 2 - text_width / 2, rect[1] + rect[3] // 2 - text_height / 2))


def update_ui(screen, ui_settings, labels, reset_rect, font):
    for ui_rect, num, clicked in ui_settings:
        color = RECTANGLE_COLOR
        if clicked:
            color = FOCUSED_RECTANGLE_COLOR
        draw_rect(screen, color, ui_rect)
        text_width, text_height = font.size(str(num))
        screen.blit(font.render(str(num), True, NUMBERS_COLOR),
                    (ui_rect[0] + ui_rect[2] // 2 - text_width / 2, ui_rect[1] + ui_rect[3] // 2 - text_height / 2))

    for rect, label in labels:
        text_width, text_height = font.size(label)
        screen.blit(font.render(label, True, NUMBERS_COLOR),
                    (rect[0] + rect[2] // 2 - text_width / 2, rect[1] + rect[3] // 2 - text_height / 2))

    color = RECTANGLE_COLOR
    text = 'Reset'

    draw_rect(screen, color, reset_rect)
    rect = reset_rect
    text_width, text_height = font.size(str(text))
    screen.blit(font.render(text, True, NUMBERS_COLOR),
                (rect[0] + rect[2] // 2 - text_width // 2,
                 rect[1] + rect[3] // 2 - text_height // 2))


def update_game_over(rectangles):
    if rectangles.game_active is False:
        text = rectangles.text
        font = rectangles.font
        text_width, text_height = font.size(str(text))
        width = BLOCK_SIZE * rectangles.width + 175
        height = max(BLOCK_SIZE * rectangles.height, 400)
        text_x = width // 2 - text_width // 2
        text_y = height // 2 - text_height // 2
        rectangles.screen.blit(font.render(str(text), True, NUMBERS_COLOR), (text_x, text_y))


def update_screen(rectangles):
    number_font = rectangles.small_font
    screen = rectangles.screen
    screen.fill(BACKGROUND_COLOR)
    update_cells(screen, rectangles.buttons, number_font)
    update_ui(screen, rectangles.ui_settings, rectangles.labels, rectangles.reset_rect, rectangles.small_font)
    update_game_over(rectangles)
    pygame.display.flip()


def draw_rect(surface, fill_color, rect, border=1):
    surface.fill(OUTLINE_COLOR, rect)
    surface.fill(fill_color, rect.inflate(-border * 2, -border * 2))


def check_events(buttons):
    for event in pygame.event.get():
        input_active = any([i[-1] for i in buttons.ui_settings])
        if event.type == pygame.MOUSEBUTTONDOWN:
            if buttons.game_active:
                for index_row, row in enumerate(buttons.buttons):
                    for index_col, item in enumerate(row):
                        rect, color = item.rect, item.color
                        if rect.collidepoint(event.pos):
                            if event.button == 3:
                                buttons.right_click(index_row, index_col)
                            if event.button == 2:
                                buttons.middle_click(index_row, index_col)
                            if event.button == 1:
                                buttons.left_click(index_row, index_col)

            for button in buttons.ui_settings:
                rect, num, clicked = button
                val = clicked
                if rect.collidepoint(event.pos):
                    if event.button == 1:
                        for b in buttons.ui_settings:
                            b[-1] = False
                        button[-1] = not val

            rect = buttons.reset_rect
            if rect.collidepoint(event.pos):
                if event.button == 1:
                    buttons.refresh_settings()

        elif event.type == pygame.KEYDOWN and input_active:
            active_button = [i for i in buttons.ui_settings if i[-1] is True][0]
            if event.key == pygame.K_BACKSPACE:
                active_button[1] = active_button[1][:-1]
            elif event.unicode in digits:
                active_button[1] += event.unicode

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                buttons.start_game()

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


if __name__ == '__main__':
    pygame.init()
    WIDTH = 10
    HEIGHT = 10
    BLOCK_SIZE = 45
    AMOUNT_OF_MINES = 15
    pygame.display.set_caption("Minesweeper")
    NEW_BOMB = pygame.transform.scale(BOMB, (BLOCK_SIZE, BLOCK_SIZE))
    NEW_FLAG = pygame.transform.scale(FLAG, (BLOCK_SIZE, BLOCK_SIZE))
    app_buttons = Application(WIDTH, HEIGHT, AMOUNT_OF_MINES)
    while True:
        update_screen(app_buttons)
        if app_buttons.remain_open == 0:
            app_buttons.end_game(True)
        check_events(app_buttons)
