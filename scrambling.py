import random

horizontal = "horizontal"
vertical = "vertical"

class Scrambling:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def apply(self, board):
        raise NotImplementedError

    def undo(self, board):
        raise NotImplementedError

    def describe(self):
        raise NotImplementedError

    def __str__(self):
        return self.describe()

    def __repr__(self):
        pass

class Swap(Scrambling):
    "Exchanging two tiles's position"

    def __init__(self, position_a: int, position_b: int):
        super().__init__("Swap")
        self.__position_a = position_a
        self.__position_b = position_b

    @property
    def position(self) -> tuple:
        return (self.__position_a, self.__position_b)

    def apply(self, board):
        board.swap_positions(self.__position_a, self.__position_b)

    def undo(self, board):
        board.swap_positions(self.__position_a, self.__position_b)

    def describe(self) -> str:
        return f"Swap tile {self.__position_a} with tile {self.__position_b}"

class Rotate(Scrambling):
    "Rotating a tile clockwise by 90, 180 or 270 degrees"

    def __init__(self, position: int, degrees: int):
        super().__init__("Rotate")
        self.__position = position
        self.__degrees = degrees % 360

    @property
    def position(self) -> int:
        return self.__position

    @property
    def degrees(self) -> int:
        return self.__position

    def apply(self, board):
        board.rotate(self.__position, self.__degrees)

    def undo(self, board):
        board.rotate(self.__position, (360 - self.__degrees) % 360)

    def describe(self, board):
        return f"Rotate tile {self.__position} by {self.__degrees} degrees"

class Flip(Scrambling):
    "Flip a tile horizontally or vertically"

    def __init__(self, position: int, axis: str):
        super().__init__("Flip")
        self.__position = position
        self.__axis = axis

    @property
    def position(self) -> int:
        return self.__position
    
    @property
    def axis(self) -> str:
        return self.__axis

    def apply(self, board):
        board.flip(self.__position, self.axis)

    def undo(self, board):
        board.flip(self.__position, self.axis)

    def describe(self):
        return f"Flip tile {self.__position} {self.__axis}ly"

class Randomizer:

    def __init__(self, grid_size: int, rng: random.Random):
        self.__grid_size = grid_size
        self.__rng = rng

    @property
    def grid_size(self) -> int:
        return self.__grid_size

    @staticmethod
    def randomizing_count(grid_size: int):
        return grid_size * (grid_size - 1)

    def generate(self) -> list:
        n = self.__grid_size
        tile_count = n * n
        total = self.randomizing_count(n)

        max_swaps = min(n, total - 2)
        swap_count = self.__rng.randint(1, max_swaps)

        remaining = total - swap_count
        rotate_count = self.__rng.randint(1, remaining - 1)
        flip_count = remaining - rotate_count

        positions = self.__rng.sample(range(tile_count), total + swap_count)
        cursor = 0

        transformations = []

        for _ in range(swap_count):
            transformations.append(
                Swap(positions[cursor], positions[cursor + 1])
            )
            cursor += 2

        for _ in range(rotate_count):
            transformations.append(
                Rotate(
                    positions[cursor], self.__rng.choice((90, 180, 270))
                )
            )
            cursor += 1

        for _ in range(flip_count):
            transformations.append(
                Flip(
                    positions[cursor], self.__rng.choice((horizontal, vertical))
                )
            )
            cursor += 1

        self.__rng.shuffle(transformations)
        return transformations