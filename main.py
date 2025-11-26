import pygame
from sys import exit
import random
from particles import Particle
pygame.mixer.init()

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
FLOORDARK = (26,106,169)
FLOORLIGHT = (100,197,229)
FLOORWHITE = (174,224,240)

screen = pygame.display.set_mode((WIDTH,HEIGHT))
clock = pygame.time.Clock()

# Sprite groups
ballGroup = pygame.sprite.GroupSingle()
lineGroup = pygame.sprite.Group()
gemGroup = pygame.sprite.Group()
skullGroup = pygame.sprite.GroupSingle()
particleGroup = pygame.sprite.Group()
beaconGroup = pygame.sprite.Group()
floorGroup = pygame.sprite.Group()

# Window setup
iconImage = pygame.image.load("img/favicon.png")
pygame.display.set_icon(iconImage)
pygame.mouse.set_visible(False)

# Buttons
playAgainButton = pygame.image.load("img/pa.png").convert_alpha()
quitButton = pygame.image.load("img/q.png").convert_alpha()
startButton = pygame.image.load("img/splash1.png").convert_alpha()

# Game variables
font = pygame.font.SysFont('Arial', 28)
cursor = pygame.image.load("img/cursor.png").convert_alpha()
gemTallyImage = pygame.image.load("img/gem.png").convert_alpha()
skullTallyImage = pygame.image.load("img/skull.png").convert_alpha()
floorTallyImage = pygame.image.load("img/floor_small.png").convert_alpha()
bonkTallyImage = pygame.image.load("img/bonk.png").convert_alpha()
winImage = pygame.image.load("img/w.png").convert_alpha()
soundOnImage = pygame.image.load("img/s.png").convert_alpha()
soundOffImage = pygame.image.load("img/so.png").convert_alpha()
bonk1Sound = pygame.mixer.Sound("audio/bonk1.mp3")
bonk2Sound = pygame.mixer.Sound("audio/bonk2.mp3")
floorSound = pygame.mixer.Sound("audio/floor.mp3")
gem1Sound = pygame.mixer.Sound("audio/gem1.mp3")
gem2Sound = pygame.mixer.Sound("audio/gem2.mp3")
skullSound = pygame.mixer.Sound("audio/skull.mp3")
victorySound = pygame.mixer.Sound("audio/victory.mp3")
soundRect = soundOnImage.get_rect(topleft=(658,758))
currentSound = soundOnImage
score = 0
drawing = False
drawingAllowed = True
maxLength = 200
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
floorGrid = [0,0,0,0,0,0,0,0,0,0]
floorProgress = 0
gemTally = 0
skullTally = 0
floorTally = 0
bonkTally = 0
screenShake = 0
victory = False
victoryTimer = 0
victoryInterval = 1000
playedVictory = False
sound = True

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
        global xVelocity, yVelocity, gravity, gameOver, cameraOffsetY, score, floorProgress, gemTally, skullTally, floorTally, bonkTally, screenShake, victory, victoryTimer
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
        global floorGrid

        # Gem collision
        gemsHit = pygame.sprite.spritecollide(ball, gemGroup, True, pygame.sprite.collide_mask)
        for gem in gemsHit:
            if sound:
                g = random.choice((gem1Sound, gem2Sound))
                g.play()
            gemTally += 1
            score+=5
            type = "gem"
            spawnParticles(gem, type)
            floorProgress += 1
            if floorProgress >= 5:
                floorProgress = 0
                floorTally += 1
                spawnFloor()
                if screenShake:
                    screenShake = 0
                    victory = True
                    victoryTimer = pygame.time.get_ticks()
                    gameOver = True
                    spawnParticles("victory","victory")

        # Skull collision
        skullsHit = pygame.sprite.spritecollide(ball, skullGroup, True, pygame.sprite.collide_mask)
        for skull in skullsHit:
            if sound:
                skullSound.play()
                floorSound.play()
            skullTally += 1
            score-=10
            type = "skull"
            spawnParticles(skull, type)
            if len(floorGroup) > 0:
                floorList = floorGroup.sprites()
                randomFloor = random.choice(floorList)
                floorGrid[int((randomFloor.rect.x/50)-1)] = 0
                spawnParticles(randomFloor, type)
                randomFloor.kill()

        # Line Collision
        linesHit = pygame.sprite.spritecollide(ball, lineGroup, True, pygame.sprite.collide_mask)
        for line in linesHit:
            if sound:
                f = random.choice((bonk1Sound, bonk2Sound))
                f.play()
            bonkTally += 1
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

        # Floor Collision
        floorsHit = pygame.sprite.spritecollide(ball, floorGroup, True, pygame.sprite.collide_mask)
        for floor in floorsHit:
            if sound:
                floorSound.play()
            yVelocity = abs(yVelocity) * bounceBoost
            xVelocity = 0
            self.rect.y -= 4
            type = "floor"
            spawnParticles(floor, type)
            floorGrid[floor.fSlot] = 0
            lineGroup.empty()
            
        # Camera
        screenY = self.rect.y - cameraOffsetY
        if screenY < 50:
            cameraOffsetY -= (50 - screenY)

        # Game over
        if screenY >= HEIGHT:
            if sound:
                skullSound.play()
            gameOver = True

ball = Ball(((WIDTH // 2)-64), (HEIGHT // 2)-120)
ballGroup.add(ball)

class Gem(pygame.sprite.Sprite):
    def __init__(self, xGem, yGem):
        super().__init__()
        self.image = pygame.image.load('img/gem.png').convert_alpha()
        self.rect = self.image.get_rect(topleft=(xGem,yGem))
        self.mask = pygame.mask.from_surface(self.image)

class Floor(pygame.sprite.Sprite):
    def __init__(self, fSlot, cameraOffsetY):
        super().__init__()
        self.fSlot = fSlot
        self.image = pygame.image.load('img/floor.png').convert_alpha()
        worldY = cameraOffsetY + (HEIGHT - 50)
        self.rect = self.image.get_rect(topleft=(50 + (fSlot * 50), worldY))
        # self.rect = self.image.get_rect(topleft=(50+(fSlot*50),750))
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

class Beacon(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pos
        self.rad = 20
        self.border = 2
        self.outline = PURPLE
        self.fill = PINK
        self.image = pygame.Surface((40,40), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.outline, (20,20), self.rad, self.border)
        pygame.draw.circle(self.image, self.fill, (20,20), self.rad-2, 0)
        self.rect = self.image.get_rect()

    def update(self):
        self.rad -= 1
        self.image.fill((0,0,0,0))
        pygame.draw.circle(self.image, self.outline, (20,20), self.rad, self.border)
        pygame.draw.circle(self.image, self.fill, (20,20), self.rad-2, 0)
        if self.rad < 1:
            self.kill()

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

def spawnParticles(item, type):
    for _ in range(50):
        if item == "victory":
            worldPos = pygame.math.Vector2(300, cameraOffsetY + 210)
        else:
            worldPos = pygame.math.Vector2(item.rect.center)
        if type == "gem":
            color = random.choice((GEMDARK, GEMLIGHT, GEMWHITE))
        elif type == "skull":
            color = random.choice((SKULLDARK, SKULLLIGHT, SKULLWHITE))
        elif type == "victory":
            color = random.choice((PINK, PURPLE, PINK))
        else:
            color = random.choice((FLOORDARK, FLOORLIGHT, FLOORWHITE))
        direction = pygame.math.Vector2(random.uniform(-1,1), random.uniform(-1,1))
        if direction.length() == 0:
            direction = pygame.math.Vector2(0,-1)
        else:
            direction = direction.normalize()
        speed = random.uniform(3, 6)
        Particle(particleGroup, (worldPos.x, worldPos.y), color, direction, speed)

def spawnGems():
    while len(gemGroup) < 10:
        x = random.randint(50,518)
        y = random.randint(cameraOffsetY - 1200, cameraOffsetY - 200)
        gem = Gem(x,y)
        gemGroup.add(gem)

def spawnSkulls():
    while len(skullGroup) < 1:
        x = random.randint(50,518)
        y = random.randint(cameraOffsetY - 1200, cameraOffsetY - 200)
        skull = Skull(x,y)
        skullGroup.add(skull)

def spawnFloor():
    emptyFloors = [i for i, x in enumerate(floorGrid) if x == 0]
    if emptyFloors:
        random.shuffle(emptyFloors)
        fslot = emptyFloors[0]
        floorGrid[fslot] = 1
        floor = Floor(fslot, previousCameraOffsetY)
        floorGroup.add(floor)

def startGame():
    global gameOver, xVelocity, yVelocity, cameraOffsetY, drawing, startPosition, endPosition, score, floorProgress, floorGrid, gemTally, skullTally, floorTally, bonkTally, screenShake, victory, playedVictory
    score = 0
    gameOver = False
    drawing = False
    cameraOffsetY = 0
    xVelocity = 0
    yVelocity = jumpHeight
    floorProgress = 0
    lineGroup.empty()
    gemGroup.empty()
    skullGroup.empty()
    particleGroup.empty()
    beaconGroup.empty()
    floorGroup.empty()
    gemTally = 0
    skullTally = 0
    floorTally = 0
    bonkTally = 0
    screenShake = 0
    victory = False
    playedVictory = False
    floorGrid = [0,0,0,0,0,0,0,0,0,0]
    ball.rect.x = ((WIDTH // 2)-48) - (ball.rect.width // 2)
    ball.rect.y = ((HEIGHT // 2)-120) - (ball.rect.height // 2)
    startPosition = pygame.mouse.get_pos()
    endPosition = startPosition

btnPlayAgain = Button(60, 10, playAgainButton)
btnQuit = Button(348, 10, quitButton)
btnStart = Button(50, 0, startButton)

# Start game
startGame()

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if soundRect.collidepoint(pygame.mouse.get_pos()):
                drawingAllowed = False
                if sound:
                    sound = False
                    currentSound = soundOffImage
                    print("Sound off")
                else:
                    sound = True
                    currentSound = soundOnImage
                    print("Sound on")
            if drawingAllowed:
                drawing = True
                mx, my = pygame.mouse.get_pos()
                startPosition = (mx, my + cameraOffsetY)
                endPosition = startPosition
                if gameStarted:
                    beacon = Beacon((mx,my))
                    beaconGroup.add(beacon)
        if event.type == pygame.MOUSEMOTION and drawing:
            mx, my = pygame.mouse.get_pos()
            endPosition = (mx, my + cameraOffsetY)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            drawingAllowed = True
            if drawing:
                drawing = False
                mx, my = pygame.mouse.get_pos()
                endPosition = (mx, my + cameraOffsetY)
                if gameStarted:
                    beacon = Beacon((mx,my))
                    beaconGroup.add(beacon)
                lineGroup.add(Line(startPosition, endPosition, fillColor=PINK, width=4, outlineColor=PURPLE, outlineThickness=2))
    if not gameStarted:
        for layer in parallaxLayers:
            layer.draw(screen)
        if btnStart.draw():
            drawingAllowed = False
            gameStarted = True
            startGame()
    elif not gameOver:
        ballGroup.update(lineGroup)
        previousCameraOffsetY = cameraOffsetY
        particleGroup.update(cameraOffsetY)
        beaconGroup.update()
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
        for floor in floorGroup:
            floor.rect.y = cameraOffsetY + (HEIGHT - 50)
            screen.blit(floor.image, (floor.rect.x, HEIGHT - 50))
        for line in lineGroup:
            screen.blit(line.image, (line.rect.x, line.rect.y - cameraOffsetY))
        for beacon in beaconGroup:
            screen.blit(beacon.image, (beacon.pos[0]-20, beacon.pos[1]-20))
        for particle in particleGroup:
            screenX = particle.pos.x
            screenY = particle.pos.y - cameraOffsetY
            if -50 < screenY < HEIGHT + 50:
                screen.blit(particle.image, (screenX - particle.rect.width//2, screenY - particle.rect.height//2))
        for ball in ballGroup:
            screen.blit(ball.image, (ball.rect.x, ball.rect.y - cameraOffsetY))
        # if drawing:
        #     outlineThickness = 2
        #     lineWidth = 4
        #     pygame.draw.line(
        #         screen,
        #         PURPLE,
        #         (startPosition[0], startPosition[1] - cameraOffsetY),
        #         (endPosition[0],   endPosition[1]   - cameraOffsetY),
        #         lineWidth + outlineThickness*2
        #     )
        #     pygame.draw.line(
        #         screen,
        #         PINK,
        #         (startPosition[0], startPosition[1] - cameraOffsetY),
        #         (endPosition[0],   endPosition[1]   - cameraOffsetY),
        #         lineWidth
        #     )
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
        if victory:
            if not playedVictory:
                if sound:
                    victorySound.play()
                playedVictory = True
            now = pygame.time.get_ticks()
            if now - victoryTimer >= victoryInterval:
                victoryTimer = now
                spawnParticles("victory", "victory")
            screen.blit(winImage, (204,172))
            particleGroup.update(cameraOffsetY)
            for particle in particleGroup:
                screenX = particle.pos.x
                screenY = particle.pos.y - cameraOffsetY
                if -50 < screenY < HEIGHT + 50:
                    screen.blit(particle.image, (screenX - particle.rect.width//2, screenY - particle.rect.height//2))
        pass

    # UI
    if len(floorGroup) > 9 and not victory:
        screenShake = 1
    else:
        screenShake = 0
    # scoreText = font.render(f"Score: {score}",True,GEMWHITE)
    renderOffset = [0,0]
    if not screenShake:
        # screen.blit(scoreText, (560,200))
        barPos = (560,210)
        barSize = (130,32)
        barProgress = floorProgress/5
        if barProgress == 0:
            innerWidth = 0
        else:
            innerWidth = int(barSize[0]*barProgress)
        innerBarSize = (innerWidth-4,barSize[1]-4)
        pygame.draw.rect(screen, GEMWHITE, (barPos,barSize), 2)
        innerPos = (barPos[0]+2, barPos[1]+2)
        pygame.draw.rect(screen, MID, (innerPos,innerBarSize), 0)
    else:
        renderOffset[0] = random.randint(0,4) - 2
        renderOffset[1] = random.randint(0,4) - 2
        # screen.blit(scoreText, (560,10))
        barPos = (560+renderOffset[0],210+renderOffset[1])
        barSize = (130,32)
        barProgress = floorProgress/5
        if barProgress == 0:
            innerWidth = 0
        else:
            innerWidth = int(barSize[0]*barProgress)
        innerBarSize = (innerWidth-4,barSize[1]-4)
        pygame.draw.rect(screen, PURPLE, (barPos,barSize), 2)
        innerPos = (barPos[0]+2, barPos[1]+2)
        pygame.draw.rect(screen, PINK, (innerPos,innerBarSize), 0)
    screen.blit(bonkTallyImage, (560,10))
    screen.blit(font.render(str(bonkTally),True,GEMWHITE), (602,10))
    screen.blit(gemTallyImage, (560,60))
    screen.blit(font.render(str(gemTally),True,GEMWHITE), (602,60))
    screen.blit(skullTallyImage, (560,110))
    screen.blit(font.render(str(skullTally),True,GEMWHITE), (602,110))
    screen.blit(floorTallyImage, (560,160))
    screen.blit(font.render(str(floorTally),True,GEMWHITE), (602,160))
    screen.blit(currentSound, soundRect)
    # Frame cleanup
    mx, my = pygame.mouse.get_pos()
    screen.blit(cursor, (mx,my))
    pygame.display.update()
    clock.tick(FPS)

# desired additions:
# better win screen
# better ice blocks
# sound effects

# did
# added beacons
# added cursor
# added bottom blocks
# changed skull behavior, clearing 1 random floor
# changed # and spawn height of gems
# changed spawn height of skulls