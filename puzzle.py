import cv2 as cv
import numpy as np

from scrambling import (
    horizontal,
    vertical,
    Swap,
    Rotate,
    Flip,
    Randomizer
)

class Tile:
    def __init__(self, tiles: np.ndarray, position: int):
        self.__tiles = tiles
        self.__position = position
        self.__rotation = 0
        self.__flipped = False

    @property
    def position(self) -> int:
        return self.__position

    @property
    def rotation(self) -> int:
        return self.__rotation

    @property
    def flipped(self) -> bool:
        return self.__flipped

    def original_state(self) -> bool:
        "Is True when the tile is not rotated or flipped"
        return self.__rotation == 0 and not self.__flipped

    def rotate(self, degrees: int):
        self.__rotation = (self.__rotation + degrees) % 360

    def flip_horizontal(self):
        self.__rotation = (360 - self.__rotation) % 360
        self.__flipped = not self.__flipped

    def flip_vertical(self):
        self.flip_horizontal()
        self.__rotation = (self.__rotation + 180) % 360

    def reset_orientation(self):
        self.__rotation = 0
        self.__flipped = False

    def render(self) -> np.ndarray:
        tiles = self.__tiles

        if self.__flipped:
            tiles = cv.flip(tiles, 1)

        if self.__rotation == 90:
            tiles = cv.rotate(tiles, cv.ROTATE_90_CLOCKWISE)
        elif self.__rotation == 180:
            tiles = cv.rotate(tiles, cv.ROTATE_180)
        elif self.__rotation == 270:
            tiles = cv.rotate(tiles, cv.ROTATE_90_COUNTERCLOCKWISE)

        return tiles

class ImageProcessor:
    def __init__(self, target_size: int = 400):
        self.__target_size = target_size

    @property
    def target_size(self) -> int:
        return self.__target_size

    def canvas_size(self, grid_size: int) -> int:
        return (self.__target_size // grid_size) * grid_size

    @staticmethod
    def load(path: str) -> np.ndarray:
        try:
            raw_bytes = np.from_file(path, dtype=np.unit8)
        except OSError as error:
            raise ValueError("The file could not be opened")

        if raw_bytes.size == 0:
            raise ValueError("The selected file is empty.")

        image = cv.imdecode(raw_bytes, cv.IMREAD_COLOR)
        if image is None:
            raise ValueError("That file is not a supported image")

        return image
    
    # We crop the center tile and then from that scale out to the full canvas
    def prepare(self, image: np.ndarray, grid_size: int) -> np.ndarray:
        size = self.canvas_size(grid_size)
        height, width = image.shape[:2]

        side = min(height, width)
        top = (height - side) // 2
        left = (width - side) // 2
        center_tile = image[top:top + side, left:left + side]

        interpolation = cv.INTER_AREA if side > size else cv.INTER_CUBIC
        return cv.resize(
            center_tile, (size, size), interpolation=interpolation
        )

    @staticmethod
    def slice_tiles(image: np.ndarray, grid_size: int) -> list:
        tile_size = image.shape[0] // grid_size
        tiles = []
        for row in range(grid_size):
            for column in range(grid_size):
                top = row * tile_size
                left = column * tile_size
                tiles.append(
                    image[top:top + tile_size, left:left + tile_size].copy()
                )
        return tiles

class PuzzleBoard:
    def __init__(self, prepared_image: np.ndarray, grid_size: int):
        self.__grid_size = grid_size
        self.__image_size = prepared_image.shape[0]
        self.__tile_size = self.__image_size // grid_size
        self.__tiles = [
            Tile(tile, position)
            for position, tile in enumerate(
                ImageProcessor.slice_tiles(prepared_image, grid_size)
            )
        ]
        self.__history = []
        self.__moves = 0

    @property
    def grid_size(self) -> int:
        return self.__grid_size

    @property
    def tile_size(self) -> int:
        return self.__tile_size

    @property
    def image_size(self) -> int:
        return self.__image_size

    @property
    def tile_count(self) -> int:
        return self.__grid_size * self.__grid_size

    @property
    def moves(self) -> int:
        return self.__moves

    @property
    def history(self) -> tuple:
        return tuple(self.__history)

    # Functions that are used to scramble the tiles inside canvas

    def swap_positions(self, position_a: int, position_b: int):
        self.__check_position(position_a)
        self.__check_position(position_b)
        self.__tiles[position_a], self.__tiles[position_b] = (
            self.__tiles[position_b],
            self.__tiles[position_a],
        )

    def rotate(self, position: int, degrees: int):
        self.__check_position(position)
        self.__tiles[position].rotate(degrees)

    def flip(self, position: int, axis: str):
        self.__check_position(position)
        if axis == horizontal:
            self.__tiles[position].flip_horizontal()
        elif axis == vertical:
            self.__tiles[position].flip_vertical()
        else:
            raise ValueError(f"Unknown flip axis: {axis!r}")

    def __check_position(self, position: int) -> None:
        if not 0 <= position < self.tile_count:
            raise IndexError(f"Tile position {position} is outside the grid.")

    # Scrambling and solving

    def scramble(self, rng=None) -> tuple:
        scrambling = Randomizer(self.__grid_size, rng).generate()
        for scrambling_step in scrambling:
            scrambling_step.apply(self)
            self.__history.append(scrambling_step)
        self.__moves = 0
        return tuple(scrambling)

    def solve(self):
        while self.__history:
            self.__history.pop().undo(self)
        self.__moves = 0

    # Record player moves

    def player_swap(self, position_a: int, position_b: int):
        self.__record(Swap(position_a, position_b))

    def player_rotate(self, position: int ,degrees: int):
        self.__record(Rotate(position, degrees))

    def player_flip(self, position: int, axis: str = horizontal):
        self.__record(Flip(position, axis))

    def __record(self, player_input):
        player_input.apply(self)
        self.__history.append(player_input)
        self.__moves = self.__moves + 1

    # Checking board state

    def tile_at(self, position: int) -> Tile:
        self.__check_position(position)
        return self.__tiles[position]

    def is_tile_correct(self, position: int) -> bool:
        tile = self.__tiles[position]
        return tile.position == position and tile.original_state()

    def incorrect_positions(self) -> list:
        return [
            position
            for position in range(self.tile_count)
            if not self.is_tile_correct(position)
        ]

    def tiles_remaining(self) -> int:
        return len(self.incorrect_positions())

    def is_solved(self) -> bool:
        return self.tiles_remaining() == 0

    def home_of(self, position: int) -> int: 
        return self.__tiles[position].position

    # Geometry helper

    def cell_of(self, position: int) -> tuple:
        return divmod(position, self.__grid_size)

    def bounds_of(self, position: int) -> tuple:
        row, column = self.cell_of(position)
        left = column * self.__tile_size
        top = row * self.__tile_size
        return (left, top, left + self.__tile_size, top + self.__tile_size)

    def position_at_pixel(self, x: int, y: int):
        if not (0 <= x < self.__image_size and 0 <= y < self.__image_size):
            return None
        column = int(x) // self.__tile_size
        row = int(y) // self.__tile_size
        if not (0 <= row < self.__grid_size and 0 <= column < self.__grid_size):
            return None
        return row * self.__grid_size + column

    # Drawing

    def render(self) -> np.ndarray:
        canvas = np.zeros((self.__image_size, self.__image_size, 3), dtype=np.uint8)
        size = self.__tile_size
        for position, tile in enumerate(self.__tiles):
            row, column = divmod(position, self.__grid_size)
            canvas[row * size:(row + 1) * size, column * size:(column + 1) * size] = (
                tile.render()
            )
        return canvas