import os
import sys
import time
import pygame

# Configuration
POSTER_PATH = "poster_final.jpg"         # Path to the downloaded poster
POLL_INTERVAL = 15                  # Seconds between file checks
FADE_DURATION = 1.0                # Transition duration in seconds
FPS = 30                          # Frames per second for animation

# Initialize Pygame and screen
pygame.init()
pygame.mixer.quit()
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

def load_and_prepare(path):
    """
    Load the image, scale it to fit the screen preserving aspect ratio,
    and return the scaled surface.
    """
    img = pygame.image.load(path).convert_alpha()
    iw, ih = img.get_size()

    # Scale preserving aspect ratio to fit inside the screen
    scale = min(SCREEN_WIDTH / iw, SCREEN_HEIGHT / ih)
    new_w, new_h = int(iw * scale), int(ih * scale)
    img = pygame.transform.smoothscale(img, (new_w, new_h))

    # Create surface same size as screen, fill black, and center image
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surface.fill((0, 0, 0))  # black background

    x = (SCREEN_WIDTH - new_w) // 2
    y = (SCREEN_HEIGHT - new_h) // 2
    surface.blit(img, (x, y))
    return surface

def crossfade(old_surf, new_surf, duration):
    """
    Crossfade transition between two surfaces over `duration` seconds.
    """
    frames = int(duration * FPS)
    for i in range(frames + 1):
        t = i / frames  # 0.0 -> 1.0
        old_alpha = int(255 * (1 - t))
        new_alpha = int(255 * t)

        temp_old = old_surf.copy()
        temp_new = new_surf.copy()
        temp_old.set_alpha(old_alpha)
        temp_new.set_alpha(new_alpha)

        screen.blit(temp_old, (0, 0))
        screen.blit(temp_new, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

def main():
    last_mtime = None
    current_surf = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

        if os.path.exists(POSTER_PATH):
            mtime = os.path.getmtime(POSTER_PATH)
            if last_mtime is None or mtime != last_mtime:
                new_surf = load_and_prepare(POSTER_PATH)
                if current_surf:
                    crossfade(current_surf, new_surf, FADE_DURATION)
                else:
                    screen.blit(new_surf, (0, 0))
                    pygame.display.flip()
                current_surf = new_surf
                last_mtime = mtime

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
