import pygame
import sys

def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Main Menu")

    font = pygame.font.Font(None, 74)
    menu_options = ["Start Game", "Settings", "Exit"]
    selected_option = 0

    clock = pygame.time.Clock()

    while True:
        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    if menu_options[selected_option] == "Start Game":
                        return "start_game"
                    elif menu_options[selected_option] == "Settings":
                        return "settings"
                    elif menu_options[selected_option] == "Exit":
                        pygame.quit()
                        sys.exit()

        for i, option in enumerate(menu_options):
            color = (255, 255, 255) if i == selected_option else (100, 100, 100)
            text = font.render(option, True, color)
            screen.blit(text, (400 - text.get_width() // 2, 200 + i * 100))

        pygame.display.flip()
        clock.tick(30)