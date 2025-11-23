import pygame
from sys import exit
import random
from particles import Particle

pygame.init()
pygame.display.set_caption("bounce!")
FPS = 60
WIDTH = 700
HEIGHT = 800
TILESIZE = 100
DARK = (49,101,95)
MID = (101,173,160)
LIGHT = (174,222,203)
PINK = (195,136,144)
PURPLE = (67,52,85)
GEMDARK = (154,79,80)
GEMLIGHT = (194,141,117)
GEMWHITE = (231,213,179)
SKULLDARK = (0,0,0)
SKULLLIGHT = (59,34,81)
SKULLWHITE = (216,204,228)

screen = pygame.display.set_mode((WIDTH,HEIGHT))
clock = pygame.time.Clock()

# Sprite groups
ballGroup = pygame.sprite.GroupSingle()
lineGroup = pygame.sprite.Group()
gemGroup = pygame.sprite.Group()
skullGroup = pygame.sprite.GroupSingle()
particleGroup = pygame.sprite.Group()

# Window icon
iconImage = pygame.image.load("img/favicon.png")
pygame.display.set_icon(iconImage)

# Buttons
playAgainButton = pygame.image.load("img/pa.png").convert_alpha()
quitButton = pygame.image.load("img/q.png").convert_alpha()
startButton = pygame.image.load("img/splash.png").convert_alpha()

# Game variables
font = pygame.font.SysFont('Arial', 28)
score = 0
drawing = False
drawingAllowed = True
jumpHeight = 16
gravity = 0.45
yVelocity = jumpHeight
xVelocity = 0
bounceBoost = 1.05
gameOver = False
startPosition = (0,0)
endPosition = (0,0)
cameraOffsetY = 0
gameStarted = False

# Background layers
bgImages = []
for i in range(1,4):
    bgImage = pygame.image.load(f'img/bg{i}.png').convert_alpha()
    bgImages.append(bgImage)

class parallaxLayer:
    def __init__(self, imagePath, speedFactor):
        self.img = pygame.image.load(imagePath).convert_alpha()
        self.speed = speedFactor
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        self.offsetY = 0
    def update(self,cameraOffsetY):
        self.offsetY = -(cameraOffsetY * self.speed)
        self.offsetY %= self.height
    def draw(self,screen):
        y1 = self.offsetY
        y2 = self.offsetY - self.height
        screen.blit(self.img,(0,y1))
        screen.blit(self.img,(0,y2))

parallaxLayers = [
    parallaxLayer('img/bg1.png',0.2),
    parallaxLayer('img/bg2.png',0.5),
    parallaxLayer('img/bg3.png',0.8)
]

class Ball(pygame.sprite.Sprite):
    def __init__(self, xBall, yBall):
        super().__init__()
        self.image = pygame.image.load('img/ball.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = xBall
        self.rect.y = yBall
    def update(self, lineGroup):
        global xVelocity, yVelocity, gravity, gameOver, cameraOffsetY, score
        self.rect.x += xVelocity
        self.rect.y -= yVelocity

        # Bounce against walls
        if self.rect.left <= 50:
            self.rect.left = 50
            xVelocity = -xVelocity
        if self.rect.right >= WIDTH-150:
            self.rect.right = WIDTH-150
            xVelocity = -xVelocity

        yVelocity -= gravity

        # Gem collision
        gemsHit = pygame.sprite.spritecollide(ball, gemGroup, True, pygame.sprite.collide_mask)
        for gem in gemsHit:
            score+=5
            type = "gem"
            spawnParticles(gem, type)

        # Skull collision
        skullsHit = pygame.sprite.spritecollide(ball, skullGroup, True, pygame.sprite.collide_mask)
        for skull in skullsHit:
            score-=10
            type = "skull"
            spawnParticles(skull, type)

        # Line Collision
        linesHit = pygame.sprite.spritecollide(ball, lineGroup, True, pygame.sprite.collide_mask)
        for line in linesHit:
            x1 = line.startPosition[0]
            y1 = line.startPosition[1]
            x2 = line.endPosition[0]
            y2 = line.endPosition[1]
            v = pygame.math.Vector2(xVelocity, -yVelocity)
            lineDirection = pygame.math.Vector2(x2 - x1, y2 - y1).normalize()
            normal = pygame.math.Vector2(-lineDirection.y, lineDirection.x)
            v = v.reflect(normal) * bounceBoost
            xVelocity, yVelocity = v.x, abs(v.y)
            self.rect.x += normal.x * 3
            self.rect.y += normal.y * 3
            score += 1

        # Camera
        screenY = self.rect.y - cameraOffsetY
        if screenY < 50:
            cameraOffsetY -= (50 - screenY)

        # Game over
        if self.rect.y >= HEIGHT:
            gameOver = True

ball = Ball(((WIDTH // 2)-64), (HEIGHT // 2)-120)
ballGroup.add(ball)

class Gem(pygame.sprite.Sprite):
    def __init__(self, xGem, yGem):
        super().__init__()
        self.image = pygame.image.load('img/gem.png').convert_alpha()
        self.rect = self.image.get_rect(topleft=(xGem,yGem))
        self.mask = pygame.mask.from_surface(self.image)

class Skull(pygame.sprite.Sprite):
    def __init__(self, xSkull, ySkull):
        super().__init__()
        self.image = pygame.image.load('img/skull.png').convert_alpha()
        self.rect = self.image.get_rect(topleft=(xSkull,ySkull))
        self.mask = pygame.mask.from_surface(self.image)

class Line(pygame.sprite.Sprite):
    def __init__(self, startPosition, endPosition, fillColor, width, outlineColor=PURPLE, outlineThickness=2):
        super().__init__()
        self.startPosition = startPosition
        self.endPosition = endPosition
        totalWidth = width+outlineThickness * 2
        min_x, max_x = min(startPosition[0], endPosition[0]), max(startPosition[0], endPosition[0])
        min_y, max_y = min(startPosition[1], endPosition[1]), max(startPosition[1], endPosition[1])
        surface_width = max(1, max_x - min_x + width * 2)
        surface_height = max(1, max_y - min_y + width * 2)
        self.image = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        relativeStartPosition = (startPosition[0] - min_x + width, startPosition[1] - min_y + width)
        relativeEndPosition = (endPosition[0] - min_x + width, endPosition[1] - min_y + width)
        pygame.draw.line(
            self.image,
            outlineColor,
            relativeStartPosition,
            relativeEndPosition,
            width + outlineThickness*2
        )
        pygame.draw.line(
            self.image,
            fillColor,
            relativeStartPosition,
            relativeEndPosition,
            width
        )
        self.rect = self.image.get_rect(topleft=(min_x - totalWidth, min_y - totalWidth))
        self.mask = pygame.mask.from_surface(self.image)

class Button():
    def __init__(self, xButton, yButton, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = xButton
        self.rect.y = yButton
    def draw(self):
        screen.blit(self.image, (self.rect.x, self.rect.y))
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1:
                return True

def spawnParticles(gem, type):
    for _ in range(50):
        worldPos = pygame.math.Vector2(gem.rect.center)
        if type == "gem":
            color = random.choice((GEMDARK, GEMLIGHT, GEMWHITE))
        else:
            color = random.choice((SKULLDARK, SKULLLIGHT, SKULLWHITE))
        direction = pygame.math.Vector2(random.uniform(-1,1), random.uniform(-1,1))
        if direction.length() == 0:
            direction = pygame.math.Vector2(0,-1)
        else:
            direction = direction.normalize()
        speed = random.uniform(2, 4)
        Particle(particleGroup, (worldPos.x, worldPos.y), color, direction, speed)

def spawnGems():
    while len(gemGroup) < 5:
        x = random.randint(50,518)
        y = random.randint(cameraOffsetY - 1600, cameraOffsetY - 200)
        gem = Gem(x,y)
        gemGroup.add(gem)

def spawnSkulls():
    while len(skullGroup) < 1:
        x = random.randint(50,518)
        y = random.randint(cameraOffsetY - 1600, cameraOffsetY - 200)
        skull = Skull(x,y)
        skullGroup.add(skull)

def startGame():
    global gameOver, xVelocity, yVelocity, cameraOffsetY, drawing, startPosition, endPosition, score
    score = 0
    gameOver = False
    drawing = False
    cameraOffsetY = 0
    xVelocity = 0
    yVelocity = jumpHeight
    lineGroup.empty()
    gemGroup.empty()
    skullGroup.empty()
    ball.rect.x = ((WIDTH // 2)-48) - (ball.rect.width // 2)
    ball.rect.y = ((HEIGHT // 2)-120) - (ball.rect.height // 2)
    startPosition = pygame.mouse.get_pos()
    endPosition = startPosition

btnPlayAgain = Button(204, 300, playAgainButton)
btnQuit = Button(204, 428, quitButton)
btnStart = Button(0, 0, startButton)

# Start game
startGame()

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if drawingAllowed:
                drawing = True
                mx, my = pygame.mouse.get_pos()
                startPosition = (mx, my + cameraOffsetY)
                endPosition = startPosition
        if event.type == pygame.MOUSEMOTION and drawing:
            mx, my = pygame.mouse.get_pos()
            endPosition = (mx, my + cameraOffsetY)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            drawingAllowed = True
            if drawing:
                drawing = False
                mx, my = pygame.mouse.get_pos()
                endPosition = (mx, my + cameraOffsetY)
                lineGroup.add(Line(startPosition, endPosition, fillColor=PINK, width=4, outlineColor=PURPLE, outlineThickness=2))
    if not gameStarted:
        if btnStart.draw():
            drawingAllowed = False
            gameStarted = True
            startGame()
    elif not gameOver:
        ballGroup.update(lineGroup)
        particleGroup.update()
        spawnGems()
        spawnSkulls()
        for layer in parallaxLayers:
            layer.update(cameraOffsetY)

        # Draw the screen
        for layer in parallaxLayers:
            layer.draw(screen)
        for gem in gemGroup:
            screenY = gem.rect.y - cameraOffsetY
            if screenY > HEIGHT:
                gem.kill()
            else:
                screen.blit(gem.image, (gem.rect.x, screenY))
        for skull in skullGroup:
            screenY = skull.rect.y - cameraOffsetY
            if screenY > HEIGHT:
                skull.kill()
            else:
                screen.blit(skull.image, (skull.rect.x, screenY))
        for line in lineGroup:
            screen.blit(line.image, (line.rect.x, line.rect.y - cameraOffsetY))
        for particle in particleGroup:
            screenX = particle.pos.x
            screenY = particle.pos.y - cameraOffsetY
            if -50 < screenY < HEIGHT + 50:
                screen.blit(particle.image, (screenX - particle.rect.width//2, screenY - particle.rect.height//2))
        for ball in ballGroup:
            screen.blit(ball.image, (ball.rect.x, ball.rect.y - cameraOffsetY))
        if drawing:
            outlineThickness = 2
            lineWidth = 4
            pygame.draw.line(
                screen,
                PURPLE,
                (startPosition[0], startPosition[1] - cameraOffsetY),
                (endPosition[0],   endPosition[1]   - cameraOffsetY),
                lineWidth + outlineThickness*2
            )
            pygame.draw.line(
                screen,
                PINK,
                (startPosition[0], startPosition[1] - cameraOffsetY),
                (endPosition[0],   endPosition[1]   - cameraOffsetY),
                lineWidth
            )
    else:
        for layer in parallaxLayers:
            layer.update(cameraOffsetY)
            layer.draw(screen)
        if btnPlayAgain.draw():
            drawingAllowed = False
            startGame()
        if btnQuit.draw():
            pygame.quit()
            exit()
        pass

    # UI
    scoreText = font.render(f"Score: {score}",True,GEMWHITE)
    screen.blit(scoreText, (560,10))

    # Frame cleanup
    pygame.display.update()
    clock.tick(FPS)
