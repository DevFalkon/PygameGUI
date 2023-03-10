import pygame as pg
import sys
from pygame._sdl2.video import Window
from pygame import gfxdraw
import math
from ctypes import windll, wintypes, byref

# To get the correct dimensions of the screen
user32 = windll.user32
user32.SetProcessDPIAware()


class Circle:
    def __init__(self, screen, centre_x, centre_y, rad, color) -> None:
        self.screen = screen
        # Drawing circle outline with antialiasing
        gfxdraw.aacircle(self.screen, centre_x, centre_y, rad, color)
        # Filling in the circle
        gfxdraw.filled_circle(self.screen, centre_x, centre_y, rad, color)
        self.centre_x = centre_x
        self.centre_y = centre_y
        self.rad = rad

    def circle_dist(self, mouse_pos):  # Returns True is the cursor is inside the circle
        x_pos = mouse_pos[0] - self.centre_x
        y_pos = mouse_pos[1] - self.centre_y
        # Finding the distance of the cursor from the centre off the circle
        dist = math.sqrt(math.pow(x_pos, 2) + math.pow(y_pos, 2))
        if dist <= self.rad:
            return True
        return False


# To get the maximum possible size of a window
# total screen width, height-dock height
# also used to give the coordinates of top left corner of the screen
def get_max_window(max_width=True, origin=False):
    spi_get_work_area = 0x0030
    desktop_working_area = wintypes.RECT()

    _ = windll.user32.SystemParametersInfoW(spi_get_work_area, 0, byref(desktop_working_area), 0)

    left = int(str(desktop_working_area.left))
    right = int(str(desktop_working_area.right))
    top = int(str(desktop_working_area.top))
    bottom = int(str(desktop_working_area.bottom))
    if max_width:
        return right-left, bottom-top
    if origin:
        return left, top  # returns (x,y) position


# Returns the cursor position relative to the entire display
def get_abs_cursor_pos():
    cursor = wintypes.POINT()
    windll.user32.GetCursorPos(byref(cursor))
    return int(str(cursor.x)), int(str(cursor.y))  # Converts c_long to int


class GuiWindow:
    def __init__(self, width=1020, height=720, title="PygameGUI"):
        self.width, self.height = width, height
        self.title = title

        pg.init()
        self.screen = pg.display.set_mode((width, height), pg.NOFRAME)
        pg.display.set_caption(self.title)

        self.window = Window.from_display_module()

        self.top_bar_height = 35  # in px

        self.close_bttn = None
        self.min_bttn = None
        self.max_bttn = None

        self.title_bar()

        # variables for drag functionality
        self.drag_lock = False
        self.initial_window_position = (0, 0)
        self.initial_mouse_position = (0, 0)
        self.relative_mouse_position = pg.mouse.get_pos()
        self.was_maximised = False

        # variables for maximising and minimising the app window
        self.last_position = self.window.position
        self.last_size = self.window.size
        self.is_maximised = False

    # Run this method in every iteration of the main loop
    def win_update(self):
        left_click = pg.mouse.get_pressed()[0]
        mouse_pos = pg.mouse.get_pos()

        if self.close_bttn.circle_dist(mouse_pos) and not self.drag_lock:

            if left_click:
                self.quit_app()

        elif self.min_bttn.circle_dist(mouse_pos) and left_click and not self.drag_lock:
            pg.display.iconify()

        elif self.max_bttn.circle_dist(mouse_pos) and not self.drag_lock:
            self.drag_lock = True
            if left_click:
                if not self.is_maximised:
                    self.maximise()

                else:
                    self.minimise()

        self.drag_window(mouse_pos, left_click)

    def drag_window(self, mouse_pos, click):
        mouse_x, mouse_y = mouse_pos
        if not click or self.was_maximised:

            # Maximise the window if its y position is < -10
            pos_x, pos_y = self.window.position
            if pos_y < -10:
                pos_y = 0
                if pos_x < 0:
                    pos_x = 0
                self.window.position = pos_x, pos_y
                self.maximise()

            self.drag_lock = False
            self.was_maximised = False
            self.initial_mouse_position = get_abs_cursor_pos()
            self.relative_mouse_position = pg.mouse.get_pos()
            self.initial_window_position = self.window.position

        if mouse_y <= self.top_bar_height and mouse_x <= self.width - 90:

            if click and not self.drag_lock:

                if not self.is_maximised:
                    pos_x = self.initial_window_position[0] - \
                        (self.initial_window_position[0] - get_abs_cursor_pos()[0]) - self.relative_mouse_position[0]
                    pos_y = self.initial_window_position[1] - \
                        (self.initial_window_position[1] - get_abs_cursor_pos()[1]) - self.relative_mouse_position[1]

                    if pos_y < -15:
                        pos_y = -15
                    self.window.position = pos_x, pos_y

                elif mouse_x <= self.width - 90:  # Minimising the window if dragged in full screen mode
                    self.minimise()
                    self.window.position = get_abs_cursor_pos()[0] - self.width//2, 0
                    self.initial_window_position = self.window.position
                    self.drag_lock = True
                    self.was_maximised = True

        else:
            if click:
                self.drag_lock = True

    @staticmethod
    def centre_window(self):  # To centre the pygame window
        max_width, max_height = get_max_window()
        pos_x = max_width // 2 - self.width // 2
        pos_y = max_height // 2 - self.height // 2
        self.window.position = (pos_x, pos_y)

    def maximise(self):
        self.last_position = self.window.position
        self.is_maximised = True

        # --------Maximising animation--------
        max_width, max_height = get_max_window()
        speed = 300
        width, height = self.window.size
        x, y = self.window.position

        while self.width < max_width or self.height < max_height:

            if self.width < max_width:
                width += speed
            elif self.width > max_width:
                width = max_width

            if self.height < max_height:
                height += speed
            elif self.height > max_height:
                height = max_height

            self.window.size = width, height
            self.width, self.height = width, height

            if x > 0:
                x -= speed//2
            elif x < 0:
                x = 0

            if y > 0:
                y -= speed//2
            elif y < 0:
                y = 0

            pg.display.flip()
            self.width, self.height = self.window.size
            self.title_bar()
            pg.time.Clock().tick(100)
            self.window.position = (x, y)

        self.width, self.height = get_max_window()
        self.window.size = self.width, self.height
        self.window.position = get_max_window(max_width=False, origin=True)
        pg.display.flip()
        self.title_bar()
        # --------End of animation--------

    def minimise(self):
        self.is_maximised = False

        # --------Minimising animation--------
        min_width, min_height = self.last_size
        speed = 300
        width, height = self.window.size
        x, y = self.window.position

        while width > min_width or height > min_height:
            if width > min_width:
                width -= speed
            elif width < min_width:
                width = min_width

            if self.height > min_height:
                height -= speed
            elif height < min_height:
                height = min_height

            self.window.size = width, height
            self.width, self.height = width, height

            if x < self.last_position[0]:
                x += speed // 2
            elif x > 0:
                x = self.last_position[0]

            if y < self.last_position[1]:
                y += speed // 2
            elif y > 0:
                y = self.last_position[1]

            pg.display.flip()
            self.width, self.height = self.window.size
            self.title_bar()
            pg.time.Clock().tick(100)
            self.window.position = (x, y)

        self.width, self.height = self.last_size
        self.window.size = self.width, self.height
        self.window.position = self.last_position
        pg.display.flip()
        self.title_bar()
        # --------End of animation--------

    def title_bar(self, color='grey'):
        title_bar_color = self.color(color)
        pg.draw.rect(self.screen, title_bar_color, pg.Rect(0, 0, self.width, self.top_bar_height))

        if self.title:
            title_size = self.top_bar_height - 15
            font = pg.font.Font('PygameGUI\\fonts\\Inter-Regular.ttf', title_size)
            text = font.render(self.title, True, self.color('white'))
            self.screen.blit(text, (self.width // 2 - (len(self.title) // 3) * title_size, 5))

        self.close_bttn = Circle(self.screen, self.width - 25,
                                 self.top_bar_height // 2,
                                 self.top_bar_height // 4,
                                 self.color('red'))
        self.max_bttn = Circle(self.screen, self.width - 50,
                               self.top_bar_height // 2,
                               self.top_bar_height // 4,
                               self.color('yellow'))
        self.min_bttn = Circle(self.screen, self.width - 75,
                               self.top_bar_height // 2,
                               self.top_bar_height // 4,
                               self.color('green'))

        pg.display.update(pg.Rect(0, 0, self.width, self.top_bar_height))

    @staticmethod
    def color(color):
        colors = {
            'red': (235, 18, 7),
            'green': (74, 222, 16),
            'yellow': (235, 200, 7),
            'grey': (61, 61, 61),
            'light_grey': (163, 160, 158),
            'white': (255, 255, 255)
        }
        return colors[color]

    def quit_app(self):
        # Closing animation
        opacity = self.window.opacity * 100
        while opacity > 0:
            opacity -= 20
            self.window.opacity = opacity / 100
            pg.time.Clock().tick(100)

        # Closing the app
        pg.quit()
        sys.exit()
