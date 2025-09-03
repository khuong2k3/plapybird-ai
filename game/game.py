from collections.abc import Iterator
import math
import tkinter as tk
import torch as tch
import numpy as np
import random
from PIL import Image, ImageTk

from game.ai import AIBase, AIFactory

PIPE_IMG_BOTTOM = Image.open("./assets/Mario_pipe_long.png")
PIPE_IMG_TOP = Image.open("./assets/Mario_pipe_long_top.png")
BIRD_IMG = Image.open("./assets/bird.png")


def pipe_image_top(width: int, height: int):
    resize_height = int(PIPE_IMG_TOP.height * (width / PIPE_IMG_TOP.width))
    image: Image.Image = PIPE_IMG_TOP.resize((width, resize_height))
    image_array = tch.tensor(np.array(image), dtype=tch.uint8)
    # print(image_array.dtype)
    if height <= image_array.shape[0]:
        diff = image_array.shape[0] - height
        image_array = image_array[diff:]
    else:
        diff = height - image_array.shape[0]
        lines = [image_array[10].unsqueeze(0) for _ in range(diff)] + [image_array]
        image_array = tch.cat(lines, dim=0)

    image = Image.fromarray(np.array(image_array))
    return ImageTk.PhotoImage(image=image)


def pipe_image_bottom(width: int, height: int):
    resize_height = int(PIPE_IMG_BOTTOM.height * (width / PIPE_IMG_BOTTOM.width))
    image: Image.Image = PIPE_IMG_BOTTOM.resize((width, resize_height))
    image_array = tch.tensor(np.array(image), dtype=tch.uint8)
    if height <= image_array.shape[0]:
        image_array = image_array[:height]
    else:
        diff = height - image_array.shape[0]
        lines = [image_array] + [image_array[-10].unsqueeze(0) for _ in range(diff)]
        image_array = tch.cat(lines, dim=0)

    image = Image.fromarray(np.array(image_array))
    return ImageTk.PhotoImage(image=image)


# pipe_image_top(40, 20)
# (147, 40, 4)


class Obstacle:
    def __init__(
        self,
        x: float,
        y: float,
        height: float,
        canvas: tk.Canvas,
        speed: float = 1,
        bottom: bool = True,
    ) -> None:
        self.width: float = 40
        self.height: float = height
        self.x: float = x
        self.y: float = y
        self.speed: float = speed
        self.canvas: tk.Canvas = canvas
        self.removed: bool = False
        # self.id = self.canvas.create_rectangle(
        #     self.x, self.y, self.x + self.width, self.y + self.height, fill="green"
        # )

        if bottom:
            self.photo: ImageTk.PhotoImage = pipe_image_bottom(
                int(self.width), int(self.height)
            )
        else:
            self.photo: ImageTk.PhotoImage = pipe_image_top(
                int(self.width), int(self.height)
            )
        self.bottom: bool = bottom

        self.id: int = self.canvas.create_image(self.x, self.y, image=self.photo)

        # resize_height = int(PIPE_IMG_BOTTOM.height * (self.width / PIPE_IMG_BOTTOM.width))
        # if bottom:
        #     self.image: Image.Image = PIPE_IMG_BOTTOM.resize((self.width, resize_height))
        #     self.photo: ImageTk.PhotoImage = ImageTk.PhotoImage(self.image)
        #
        #     self.y: float = y
        #     self.id: int = self.canvas.create_image(self.x, self.y, image=self.photo)
        # else:
        #     self.image: Image.Image = PIPE_IMG_TOP.resize((self.width, resize_height))
        #     self.photo: ImageTk.PhotoImage = ImageTk.PhotoImage(self.image)
        #     self.y: float = y - resize_height + self.height
        #     self.id: int = self.canvas.create_image(self.x, self.y, image=self.photo)

    def in_view(self):
        return self.x + self.width > 0

    def update(self):
        self.x -= 10

    def draw(self):
        self.canvas.moveto(self.id, self.x, self.y)

    def destroy(self):
        self.removed = True
        self.canvas.delete(self.id)


class ObstacleFactory:
    def __init__(
        self,
        canvas: tk.Canvas,
        screen_w: float,
        screen_h: float,
        gap_height: float,
        game_speed: float = 1,
    ) -> None:
        self.canvas: tk.Canvas = canvas
        self.screen_h: float = screen_h
        self.screen_w: float = screen_w
        self.gap_height: float = gap_height
        self.game_speed: float = game_speed

    def top(self, x: float, height: float):
        return Obstacle(x, 0, height, self.canvas, self.game_speed, False)

    def bottom(self, x: float, height: float):
        return Obstacle(x, self.screen_h - height, height, self.canvas, self.game_speed)

    def top_bottom(self, x: float, gap_y: float) -> Iterator[Obstacle]:
        yield self.top(x, gap_y)
        yield self.bottom(x, self.screen_h - gap_y - self.gap_height)


class Player:
    def __init__(
        self, canvas: tk.Canvas, screen_w: float, screen_h: float, speed: float = 1
    ) -> None:
        self.x: float = screen_w / 10.0
        self.y: float = screen_h / 2.0
        self.angle: float = 0.0
        self.screen_h: float = screen_h
        self.screen_w: float = screen_w
        self.canvas: tk.Canvas = canvas
        self.width: float = 40
        self.height: float = 40
        self.speed: float = speed
        self.image: Image.Image = BIRD_IMG.resize((self.width, self.height))
        self.photo: ImageTk.PhotoImage = ImageTk.PhotoImage(self.image)
        self.id: int = self.canvas.create_image(
            self.x, self.y, image=self.photo, anchor=tk.CENTER
        )

    def rotate(self):
        self.canvas.delete(self.id)
        self.photo = ImageTk.PhotoImage(self.image.rotate(self.angle))
        self.id = self.canvas.create_image(
            self.x, self.y, image=self.photo, anchor=tk.CENTER
        )

    def update(self):
        self.y += 8.0 * self.speed
        self.angle -= 5.0 * self.speed
        self.angle = max(self.angle, -90.0)
        # self.y = min(self.y, self.screen_h)

    def go_up(self) -> None:
        self.y -= 40 * self.speed
        self.angle = 0.0
        # self.y = max(self.y, 0)

    def draw(self):
        self.rotate()
        self.canvas.moveto(self.id, self.x, self.y)

    def gap(self, obstacle: Obstacle):
        # print(obstacle.x)
        gap_x = (self.x - obstacle.x) / self.screen_w
        gap_y = (self.y - obstacle.y) / self.screen_h
        gap_ground = (self.screen_h - self.y) / self.screen_h
        return tch.tensor([gap_x, gap_y, gap_ground], dtype=tch.float32)

    def collise(self, obstacle: Obstacle):
        return not (
            self.x + self.width < obstacle.x
            or self.x > obstacle.x + obstacle.width
            or self.y + self.height < obstacle.y
            or self.y > obstacle.y + obstacle.height
        )

    def collises(self, obstacles: list[Obstacle]):
        for obstacle in obstacles:
            if self.collise(obstacle):
                return True
        return False

    def destroy(self):
        self.canvas.delete(self.id)


class AIPlayer:
    def __init__(
        self,
        canvas: tk.Canvas,
        ai: AIBase,
        screen_w: float,
        screen_h: float,
        speed: float = 1,
    ) -> None:
        self.player: Player = Player(canvas, screen_w, screen_h, speed)
        self.ai: AIBase = ai
        self.lasted: int = 0
        self.death: bool = False
        self.gap_tensor: tch.Tensor | None = None

    def update(self):
        self.player.update()
        if not self.death:
            self.lasted += 1

    def draw(self):
        self.player.draw()

    def moving(self, gaps: tch.Tensor):
        check_move = self.ai.forward(gaps).argmax()
        if check_move == 1:
            self.player.go_up()

    def collise(self, obstacle: Obstacle):
        return self.player.collise(obstacle) or (
            self.player.y < 0 or self.player.y > self.player.screen_h
        )

    def collises(self, obstacles: list[Obstacle]):
        return self.player.collises(obstacles) or (
            self.player.y - 5 < 0 or self.player.y + 5 > self.player.screen_h
        )

    def destroy(self):
        self.death = True
        self.player.destroy()


class AIPlayerFactory:
    def __init__(
        self, canvas: tk.Canvas, screen_w: float, screen_h: float, speed: float = 1
    ) -> None:
        self.ai_factory: AIFactory = AIFactory()
        self.canvas: tk.Canvas = canvas
        self.screen_h: float = screen_h
        self.screen_w: float = screen_w
        self.speed: float = speed
        self.iteration: int = 0

    def generate(self, num: int) -> Iterator[AIPlayer]:
        for ai in self.ai_factory.generate(
            num, [0.1, 0.05, 0.01][round(random.random() * 2)]
        ):
            yield AIPlayer(self.canvas, ai, self.screen_w, self.screen_h, self.speed)


class Flappybird:
    def __init__(self, root: tk.Tk):
        self.screen_w: float = 1000
        self.screen_h: float = 500
        self.game_speed: float = 1
        self.root: tk.Tk = root
        self.canvas: tk.Canvas = tk.Canvas(
            self.root, width=self.screen_w, height=self.screen_h
        )
        self._quit: bool = False
        self.canvas.pack()
        # self.player: Player = Player(self.canvas, self.screen_w, self.screen_h)
        self.obstacles_factory: ObstacleFactory = ObstacleFactory(
            self.canvas, self.screen_w, self.screen_h, 100
        )
        self.ai_players: list[AIPlayer] = []
        self.death_ai_player: list[AIPlayer] = []
        self.ai_factory: AIPlayerFactory = AIPlayerFactory(
            self.canvas, self.screen_w, self.screen_h, self.game_speed
        )
        self.ai_players.extend(self.ai_factory.generate(20))
        self.obstacles: list[Obstacle] = []
        self.obstacles.extend(
            self.obstacles_factory.top_bottom(self.screen_w, self.screen_h / 2.0)
        )
        self.obstacles.extend(
            self.obstacles_factory.top_bottom(
                self.screen_w * (1.5), self.screen_h / 2.0
            )
        )
        self.root.bind("<space>", self.go_up)
        self.root.bind("q", self.quit)

    def set_game_speed(self, speed: float):
        # self.player.speed = speed
        self.obstacles_factory.game_speed = speed
        for obstacle in self.obstacles:
            obstacle.speed = speed

    def quit(self, _):
        self._quit = True

    def go_up(self, _):
        return None
        # self.player.go_up()

    def best_ai(self):
        if len(self.death_ai_player) == 0:
            self.ai_factory.ai_factory.best_ai.save()
            return None

        current_best = self.death_ai_player[0]

        for player in self.death_ai_player[1:]:
            if player.lasted > current_best.lasted:
                current_best = player
            elif (
                player.lasted == current_best.lasted
                and current_best.gap_tensor is not None
                and player.gap_tensor is not None
            ):
                if player.gap_tensor[1] < current_best.gap_tensor[1]:
                    current_best = player

        current_best.ai.save()
        return current_best

    def reset_game(self):
        for obstacle in self.obstacles:
            obstacle.destroy()

        self.obstacles: list[Obstacle] = []
        self.obstacles.extend(
            self.obstacles_factory.top_bottom(self.screen_w, self.screen_h / 2.0)
        )
        self.obstacles.extend(
            self.obstacles_factory.top_bottom(
                self.screen_w * (1.5), self.screen_h / 2.0
            )
        )

    def random_obstacles(self):
        for obstacle in self.obstacles:
            if not obstacle.in_view():
                obstacle.destroy()

        self.obstacles = list(filter(lambda x: not x.removed, self.obstacles))
        if len(self.obstacles) < 3:
            min_h = int(self.screen_h / 3.0)
            self.obstacles.extend(
                self.obstacles_factory.top_bottom(
                    self.screen_w,
                    float(random.randint(min_h, int(self.screen_h) - min_h)),
                )
            )

    def neasest_obstacle(self, player: Player):
        current_obstacle = self.obstacles[0]
        for i in range(2, len(self.obstacles), 2):
            obstacle = self.obstacles[i]
            if obstacle.x > player.x:
                if (
                    abs(obstacle.x - player.x) < abs(player.x - current_obstacle.x)
                    and obstacle.bottom
                ):
                    current_obstacle = obstacle
        return current_obstacle

    def update(self):
        self.random_obstacles()

        for obstacle in self.obstacles:
            obstacle.update()
            obstacle.draw()

        check_obstacle = self.neasest_obstacle(self.ai_players[0].player)
        for ai in self.ai_players:
            gap_tensor = ai.player.gap(check_obstacle)
            ai.moving(gap_tensor)
            ai.gap_tensor = gap_tensor
            ai.update()
            ai.draw()
            if ai.collises(self.obstacles):
                self.death_ai_player.append(ai)

        for ai in self.death_ai_player:
            if not ai.death:
                ai.destroy()
                self.ai_players.remove(ai)

        # if self.player.collises(self.obstacles):
        #     self.player.y = 0
        # self.player.update()
        # self.player.draw()

        if len(self.ai_players) == 0:
            self.ai_factory.ai_factory.best_ai = self.best_ai().ai
            self.death_ai_player = []
            self.ai_players.extend(self.ai_factory.generate(20))
            self.reset_game()

    def game_loop(self):
        if not self._quit:
            self.update()
            self.root.after(50, self.game_loop)
        else:
            _ = self.best_ai()
            self.root.quit()

    def start(self):
        self.game_loop()
