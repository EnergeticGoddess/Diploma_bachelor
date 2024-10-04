import pygame
import random
import pygame_widgets
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame_widgets.button import Button

# Константы
WIDTH, HEIGHT = 640 * 2, 480 * 2
CELL_SIZE = 5
TOTAL_CELLS = WIDTH * HEIGHT // CELL_SIZE ** 2
NUM_RUNS = 1

# Цвета
BLACK = pygame.Color(0, 0, 0)
WHITE = pygame.Color(255, 255, 255)
RED = pygame.Color(255, 0, 0)
BLUE = pygame.Color(0, 0, 255)
GREEN = pygame.Color(0, 255, 0)
ANT_COLORS = [pygame.Color(255, 0, 0), pygame.Color(0, 255, 255), pygame.Color(0, 0, 255), pygame.Color(255, 255, 0), pygame.Color(255, 0, 255), pygame.Color(0, 255, 255)]

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ant Searching for Food")
clock = pygame.time.Clock()

def get_feromone_color(feromone_level):
    # Define a gradient of colors from white to yellow
    colors = [
        (255, 255, 255),  # white
        (255, 255, 0),   # yellow
    ]

    # Interpolate between the colors based on the feromone level
    color = tuple(int(c1 + (c2 - c1) * feromone_level) for c1, c2 in zip(colors[0], colors[1]))

    return color

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.has_food = False
        self.feromone_level = 0

    def draw(self):
        if self.has_food:
            pygame.draw.rect(screen, GREEN, (self.x * CELL_SIZE, self.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        elif self.feromone_level > 0:
            feromone_color = get_feromone_color(self.feromone_level)
            pygame.draw.rect(screen, feromone_color, (self.x * CELL_SIZE, self.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

class AntHill:
    def __init__(self, x, y, reproduction_threshold, starvation_limit, color):
        self.x = x
        self.y = y
        self.reproduction_threshold = reproduction_threshold
        self.starvation_limit = starvation_limit
        self.color = color
        self.ants = [self.Ant(x, y, self)]

    def add_ant(self, ant):
        self.ants.append(ant)

    def draw(self):
        pygame.draw.rect(screen, self.color.lerp(BLACK, 0.2), (self.x * CELL_SIZE, self.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    class Ant:
        def __init__(self, x, y, anthill):
            self.x = x
            self.y = y
            self.starvation_counter = 0
            self.anthill = anthill
            self.carrying_food = False
            self.returning_to_anthill = False

        def draw(self):
            color = self.anthill.color if self.starvation_counter < self.anthill.reproduction_threshold else self.anthill.color.lerp(BLACK, 0.5)
            pygame.draw.rect(screen, color, (self.x * CELL_SIZE, self.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

        def move(self, cells):
            directions = [(dx, dy) for dx in range(-1, 2) for dy in range(-1, 2) if dx != 0 or dy != 0]
            random.shuffle(directions)

            found_food = False
            for dx, dy in directions:
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < WIDTH // CELL_SIZE and 0 <= ny < HEIGHT // CELL_SIZE:
                    cell = cells[nx * (HEIGHT // CELL_SIZE) + ny]
                    if cell.has_food:
                        cell.has_food = False
                        found_food = True
                        break

            if not found_food:
                if self.returning_to_anthill:
                    # Если мы возвращаемся в муравейник, движемся к нему
                    dx = self.anthill.x - self.x
                    dy = self.anthill.y - self.y
                    if dx != 0:
                        self.x += 1 if dx > 0 else -1
                    if dy != 0:
                        self.y += 1 if dy > 0 else -1
                    if self.x == self.anthill.x and self.y == self.anthill.y:
                        self.returning_to_anthill = False
                        self.carrying_food = False
                        if self.starvation_counter < self.anthill.reproduction_threshold:
                            new_ant = self.anthill.Ant(self.x, self.y, self.anthill)
                            return new_ant
                        self.starvation_counter = 0  # Сбрасываем счетчик голода
                else:
                    # Если мы не несем еду, ищем еду и увеличиваем счетчик голода
                    self.starvation_counter += 1

                    # Leave feromones behind
                    cell = cells[self.x * (HEIGHT // CELL_SIZE) + self.y]
                    cell.feromone_level = min(cell.feromone_level + 0.1, 1)

                    # Avoid high feromone levels
                    min_feromone_level = float('inf')
                    best_direction = None
                    for dx, dy in directions:
                        nx, ny = self.x + dx, self.y + dy
                        if 0 <= nx < WIDTH // CELL_SIZE and 0 <= ny < HEIGHT // CELL_SIZE:
                            cell = cells[nx * (HEIGHT // CELL_SIZE) + ny]
                            if cell.feromone_level < min_feromone_level:
                                min_feromone_level = cell.feromone_level
                                best_direction = (dx, dy)

                    dx, dy = best_direction
                    self.x, self.y = self.x + dx, self.y + dy

            else:
                # Если мы нашли еду, берем ее в руки и возвращаемся в муравейник
                self.carrying_food = True
                self.returning_to_anthill = True

            return None

def run_simulation(anthills):
    cells = [Cell(x, y) for x in range(WIDTH // CELL_SIZE) for y in range(HEIGHT // CELL_SIZE)]
    for cell in cells:
        if random.random() < 0.1:
            cell.has_food = True

    # Create a surface for the plot
    plot_width = WIDTH // 4
    plot_height = HEIGHT // 2
    plot_surface = pygame.Surface((plot_width, plot_height))
    plot_rect = plot_surface.get_rect()
    plot_rect.left = WIDTH - plot_width
    plot_rect.top = HEIGHT // 2

    # Create lists to store the data for each type of ant
    ant_data = [[] for _ in anthills]

    running = True
    steps = 0
    total_ants = sum(len(anthill.ants) for anthill in anthills)

    while running:
        screen.fill(WHITE)
        plot_surface.fill(WHITE)

        for cell in cells:
            cell.draw()

        for i, anthill in enumerate(anthills):
            anthill.draw()
            new_ants = []
            for ant in anthill.ants:
                ant.draw()
                new_ant = ant.move(cells)
                if new_ant is not None:
                    new_ants.append(new_ant)
            anthill.ants += new_ants
            anthill.ants = [ant for ant in anthill.ants if ant.starvation_counter < anthill.starvation_limit]

            ant_data[i].append(len(anthill.ants))

        total_ants = sum(len(anthill.ants) for anthill in anthills)
        if total_ants == 0:
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Decay feromones
        for cell in cells:
            cell.feromone_level = max(cell.feromone_level - 0.01, 0)

        if main.show_graph:
            # Draw the plot
            max_ants = max(max(data) for data in ant_data)
            for i, data in enumerate(ant_data):
                for j in range(1, len(data)):
                    pygame.draw.line(plot_surface, ANT_COLORS[i],
                                     ((j - 1) / len(data) * plot_width, plot_height - data[j - 1] / max_ants * plot_height),
                                     (j / len(data) * plot_width, plot_height - data[j] / max_ants * plot_height), 2)

            # Draw axes and labels
            pygame.draw.line(plot_surface, BLACK, (0, plot_height), (plot_width, plot_height), 2)
            pygame.draw.line(plot_surface, BLACK, (0, 0), (0, plot_height), 2)
            font = pygame.font.SysFont(None, 24)
            text = font.render("Time", True, BLACK)
            plot_surface.blit(text, (plot_width - text.get_width(), plot_height - text.get_height()))
            text = font.render("Number of Ants", True, BLACK)
            plot_surface.blit(text, (0, 0))

            # Draw axis ticks and labels
            num_ticks = 5
            for i in range(num_ticks + 1):
                x = i * plot_width / num_ticks
                pygame.draw.line(plot_surface, BLACK, (x, plot_height), (x, plot_height - 5))
                text = font.render(str(int(steps * i / num_ticks)), True, BLACK)
                plot_surface.blit(text, (x - text.get_width() / 2, plot_height - text.get_height() - 5))

                y = plot_height - i * plot_height / num_ticks
                pygame.draw.line(plot_surface, BLACK, (0, y), (5, y))
                text = font.render(str(int(max_ants * i / num_ticks)), True, BLACK)
                plot_surface.blit(text, (10, y - text.get_height() / 2))

            screen.blit(plot_surface, plot_rect)

        # Update the button
        pygame_widgets.update(pygame.event.get())

        pygame.display.flip()
        clock.tick(1000)
        steps += 1

    return total_ants, steps

def main():
    anthills = [
        AntHill(WIDTH // (CELL_SIZE * 4), HEIGHT // (CELL_SIZE * 4), 30, 100, ANT_COLORS[0]),
        AntHill(WIDTH // (CELL_SIZE * 4) * 3, HEIGHT // (CELL_SIZE * 4), 60, 100, ANT_COLORS[1]),
        AntHill(WIDTH // (CELL_SIZE * 2), HEIGHT // (CELL_SIZE + 1), 90, 100, ANT_COLORS[2])
    ]

    # Create a button to toggle the display of the graph
    main.show_graph = True
    toggle_button = Button(
        screen, 10, 10, 100, 30, text='Toggle Graph',
        fontSize=20, margin=20,
        inactiveColour=(200, 200, 200),
        hoverColour=(150, 150, 150),
        pressedColour=(100, 100, 100),
        onClick=lambda: setattr(main, 'show_graph', not main.show_graph)
    )

    total_ants = 0
    total_steps = 0
    for i in range(NUM_RUNS):
        ants, steps = run_simulation(anthills)
        total_ants += ants
        total_steps += steps

    avg_ants = total_ants / NUM_RUNS
    avg_steps = total_steps / NUM_RUNS
    print(f"Среднее количество муравьев: {avg_ants:.2f}")
    print(f"Среднее время жизни экосистемы: {avg_steps} шагов")

if __name__ == "__main__":
    main()
