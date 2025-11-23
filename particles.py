import pygame

class Particle(pygame.sprite.Sprite):
    def __init__(self, groups, pos, color, direction, speed):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.color = color
        self.direction = (
            direction.normalize() 
            if direction.length() != 0 
            else pygame.math.Vector2(0, -1)
        )
        self.speed = speed
        self.image = pygame.Surface((8,8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (4,4), 4)
        self.rect = self.image.get_rect(center=(0,0))

    def update(self):
        self.pos += self.direction * self.speed
        if (
            self.pos.x < -200 or
            self.pos.x > 1200 or
            self.pos.y < -5000 or
            self.pos.y > 5000
        ):
            self.kill()
