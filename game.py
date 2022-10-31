import pygame
import random
import pathlib
import time
import json

basement = pathlib.Path(__file__).parent.absolute()
images = basement / "images"
fonts = basement / "fonts"
sounds = basement / "sounds"

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()

jump_sound = pygame.mixer.Sound(str(sounds / "jump.mp3"))
fall_sound = pygame.mixer.Sound(str(sounds / "fall.mp3"))
bumb_sound = pygame.mixer.Sound(str(sounds / "bump.mp3"))


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, _game):
        super().__init__()
        self.run_animation = [pygame.image.load(images / "player" / f"run{i}.png") for i in range(1, 4)]
        self.jump_image = pygame.image.load(images / "player" / "jump.png")
        self.fall_image = pygame.image.load(images / "player" / "fall.png")
        self.fallen_image = pygame.image.load(images / "player" / "fallen.png")
        self.idle_image = pygame.image.load(images / "player" / "idle.png")

        self.image = self.idle_image.copy()
        self.rect = pygame.Rect(x, y, 100, 100)
        self.game = _game

        self.is_jumping = False
        self.direction = 1
        self.gravity_reversed = False
        self.fall_sound_played = False

        self.vec = pygame.math.Vector2(0, 0)

        self.delta_g_pressed = 0
        self.delta_s_pressed = 0

    def reverse_gravity(self):
        self.gravity_reversed = not self.gravity_reversed

    def update(self):
        # get pressed keys
        keys = pygame.key.get_pressed()

        # move left by setting x velocity to -5
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction = -1
            self.vec.x = -5

        # move right by setting x velocity to 5
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction = 1
            self.vec.x = 5

        # jump by setting y velocity to -20
        if keys[pygame.K_SPACE] and not self.is_jumping:
            if not self.gravity_reversed:
                self.vec.y = -20
            else:
                self.vec.y = 15
            
            self.is_jumping = True

            jump_sound.play()

        # if gravity is reversed and pressed K_s, move to 30 down
        if not self.is_jumping and self.gravity_reversed and (keys[pygame.K_s] or keys[pygame.K_DOWN]) and abs(self.delta_s_pressed - time.time()) > 0.25:
            self.rect.move_ip(0, -30)
            self.delta_s_pressed = time.time()
            self.is_jumping = True

            jump_sound.play()

        # reverse gravity by setting y velocity to 20
        if keys[pygame.K_g] and abs(self.delta_g_pressed - time.time()) > 0.5:
            if self.gravity_reversed:
                self.vec.y = -10
            else:
                self.vec.y = 10

            self.delta_g_pressed = time.time()
            self.reverse_gravity()

            bumb_sound.play()

        # apply gravity
        if not self.gravity_reversed:
            self.vec.y += 0.5
            self.vec.y = min(20, self.vec.y)
        else:
            self.vec.y -= 0.5
            self.vec.y = max(-20, self.vec.y)

        self.vec.x *= 0.9

        # move the player
        self.rect.move_ip(self.vec)

        # check if the player is on the ground
        if self.rect.bottom >=  600:
            self.rect.bottom = 600
            self.is_jumping = False

        # check if player touches the platform
        if self.rect.colliderect(self.game.platform.rect):
            self.is_jumping = False
            self.fall_sound_played = False

        # teleport player if on the left side of the screen
        if self.rect.left <= 0:
            self.rect.right = 800

        # teleport player if on the right side of the screen
        elif self.rect.right >= 800:
            self.rect.left = 0

        # if player is falling, play sound
        if self.vec.y > 0 and self.is_jumping and not self.fall_sound_played:
            self.fall_sound_played = True
            fall_sound.play()

        # # check if the player is on the ceiling
        # if self.rect.top <= 0:
        #     self.gravity_reversed = False
        #     self.rect.top = 0

        if not self.gravity_reversed:
            # run animation 12 frames per second
            if abs(self.vec.x) > .9 and not self.is_jumping:
                self.image = self.run_animation[round(time.time() * 12) % 3]
                self.image = pygame.transform.flip(self.image, self.direction == -1, False)

            # idle image
            elif not self.is_jumping:
                self.image = self.idle_image
                self.image = pygame.transform.flip(self.image, self.direction == -1, False)
                
            # jump image
            elif self.vec.y < 0:
                self.image = self.jump_image
                self.image = pygame.transform.flip(self.image, self.direction == -1, False)
            # fall image
            else:
                self.image = self.fall_image
                self.image = pygame.transform.flip(self.image, self.direction == -1, False)

        else:
            # run animation 12 frames per second
            if abs(self.vec.x) > .9 and not self.is_jumping:
                self.image = self.run_animation[round(time.time() * 12) % 3]
                self.image = pygame.transform.flip(self.image, self.direction == -1, True)

            # idle image
            elif not self.is_jumping:
                self.image = self.idle_image
                self.image = pygame.transform.flip(self.image, self.direction == -1, True)
                
            # jump image
            elif self.vec.y > 0:
                self.image = self.jump_image
                self.image = pygame.transform.flip(self.image, self.direction == -1, True)

            # fall image
            else:
                self.image = self.fall_image
                self.image = pygame.transform.flip(self.image, self.direction == -1, True)

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color):
        super().__init__()
        animation_image = pygame.image.load(images / "platform_1.png") # 100 x 186
        
        # chop picture into 6 pieces with size 100, 31
        self.images = [
            animation_image.subsurface(0, 0, 100, 31), 
            animation_image.subsurface(0, 31, 100, 31), 
            animation_image.subsurface(0, 62, 100, 31), 
            animation_image.subsurface(0, 93, 100, 31), 
            animation_image.subsurface(0, 124, 100, 31), 
            animation_image.subsurface(0, 155, 100, 31)
        ]

        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.w = w
        self.h = h

        self.delta_time = 0

    def update(self):
        # animate with 6 images per second
        if abs(self.delta_time - time.time()) >= 1 / 12 + random.randint(1, 3) / 100:
            self.image = self.images[(self.images.index(self.image) + 1) % len(self.images)]
            self.delta_time = time.time()

class MovingPlatform(Platform):
    def __init__(self, x, y, w, h, color):
        super().__init__(x, y, w, h, color)

        animation_image = pygame.image.load(images / "moving_platform_1.png") # 110 x 180

        # chop picture into 6 pieces with size 110, 30
        self.images = [
            animation_image.subsurface(0, 0, 110, 30),
            animation_image.subsurface(0, 30, 110, 30),
            animation_image.subsurface(0, 60, 110, 30),
            animation_image.subsurface(0, 90, 110, 30),
            animation_image.subsurface(0, 120, 110, 30),
            animation_image.subsurface(0, 150, 110, 30)
        ]

        self.image = self.images[0]
        self.original_image = self.image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.w = w
        self.h = h

        self.delta_time = 0

        self.direction = 1
        self.speed = 3

    def update(self):
        self.rect.x += self.direction * self.speed

        if self.rect.x <= 0:
            self.direction = 1
        elif self.rect.x >= 450:
            self.direction = -1

        # animate with 6 images per second
        if abs(self.delta_time - time.time()) >= 1 / 12:

            self.image = self.images[(self.images.index(self.original_image) + 1) % len(self.images)]
            self.original_image = self.image

            if self.direction == -1:
                self.image = pygame.transform.flip(self.image, True, False)
           
            self.delta_time = time.time()


class DeathLaser(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        laser_animation = pygame.image.load(images / "laser.png") # 800 x 1440

        # chop by 800 x 240
        self.images = [
            laser_animation.subsurface(0, 0, 800, 240),
            laser_animation.subsurface(0, 240, 800, 240),
            laser_animation.subsurface(0, 480, 800, 240),
            laser_animation.subsurface(0, 720, 800, 240),
            laser_animation.subsurface(0, 960, 800, 240),
            laser_animation.subsurface(0, 1200, 800, 240)
        ]

        self.image = self.images[0]
        self.rect = pygame.Rect(x, y, w, h)
        self.rect.x = x
        self.rect.y = y + 800 

        self.w = w
        self.h = h

        self.delta_time = 0

    def update(self, score):
        # animate 12 fps
        if abs(self.delta_time - time.time()) >= 1 / 12:
            self.image = self.images[(self.images.index(self.image) + 1) % len(self.images)]
            self.delta_time = time.time()

        # move laser up and speed up it by score
        self.rect.y -= 2 + score / 800

    def check_collision(self, player):
        # check if player.rect + 100 collide with laser.rect
        return player.rect.colliderect(self.rect.x, self.rect.y + 100, self.w, self.h)
    
    def y_distance_to_player(self, player):
        return self.rect.y - player.rect.y


class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

        self.max_camera_y = 0
        self.max_player_y = 0

    def update(self, target):
        # follow player on y axis
        x = -target.rect.x + int(self.width / 2)
        y = -target.rect.y + int(self.height / 2)

        # limit scrolling
        x = min(0, x)  # left
        # y = min(0, y)  # top
        x = max(-(self.camera.width - self.width), x)  # right
        y = max(-(self.camera.height - self.height), y)  # bottom

        self.camera = pygame.Rect(x, y, self.width, self.height)

        self.max_camera_y = max(self.max_camera_y, self.camera.bottomleft[1])
        self.max_player_y = -min(self.max_player_y, target.rect.top)

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)


class InfiniteXImage(pygame.Surface):
    def __init__(self, image, width, height):
        super().__init__((width, height))
        self.image = image
        self.width = width
        self.height = height
        
        self.fill((255, 0, 0))

        # duplicate image to right x axis for fill the screen width
        for i in range(0, width, image.get_width()):
            self.blit(self.image, (i, 0))

        self.set_colorkey((255, 0, 0))


class ParallaxBackground:
    def __init__(self, screen, images, speed, enldess):
        self.screen = screen
        self.images = images
        self.speed = speed
        self.endless = enldess

        self.bottom_y = 0
        self.up_y = 800

        self.image_rects = []
        for image in self.images:
            image_rect = image.get_rect()
            self.image_rects.append(image_rect)

        self.objects = list(zip(self.images, self.image_rects, self.speed, self.endless))

    def draw(self, camera, player_top):
        for i, obj in enumerate(self.objects):
            image, image_rect, speed, endless = obj

            image_rect.y = camera.camera.y * speed

            if endless:
                self.screen.blit(image, (0, 0 + (camera.max_player_y * speed) % image.get_height()))
                self.screen.blit(image, (0, (camera.max_player_y * speed) % image.get_height() - image.get_height()))

            else:
                self.screen.blit(image, image_rect)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.running = True
        self.font_big = pygame.font.Font(str(fonts / "ka1.ttf"), 32)
        self.font_medium = pygame.font.Font(str(fonts / "ka1.ttf"), 24)
        self.font_small = pygame.font.Font(str(fonts / "ka1.ttf"), 16)

        self.stats_path = basement / "stats.json"
        with self.stats_path.open("r") as f:
            self.stats = json.load(f)

        self.images = [pygame.image.load(str(images / x)) for x in ["sCitySky.png", "sMockup.png", "sCityCarsFar.png", "sCityCarsClose.png"]]
        self.images[0] = pygame.transform.scale(self.images[0], (800, 720))
        self.images = [InfiniteXImage(image, 800, 600) for image in self.images]
        self.background = ParallaxBackground(self.screen, self.images, [.1, .1, .2, .4], [True, False, True, True])
        
        self.arrow_images = [pygame.image.load(str(images / x)).convert() for x in ["arrow_normal.jpg", "arrow_reversed.jpg"]]
        self.arrow_images = [pygame.transform.scale(image, (68, 100)) for image in self.arrow_images]
        [x.set_colorkey((255, 255, 255)) for x in self.arrow_images]

        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()

        self.player = Player(50, 50, self)
        self.laser = DeathLaser(0, 0, 800, 240)

        # generate start random platforms with same height and same width and same space between them
        # x of platforms is less than 800
        # platforms generates in up
        for i in range(10):
            x = random.randint(0, 800)
            y = random.randint(0, 10)
            w = 100
            h = 30
            self.platform = Platform(x, y * 100, w, h, (255, 0, 0))
            self.all_sprites.add(self.platform)
            self.platforms.add(self.platform)

        self.all_sprites.add(self.player)

        self.camera = Camera(800, 600)

        self.platforms_ = None
        self.is_colliding = False

        self.new_chunk_y = 0
        self.score = 0

    def run(self):
        while self.running:
            self.clock.tick(60)
            self.events()
            self.update()
            self.draw()

        self.stats["highest_score"] = int(max(self.stats["highest_score"], self.score))

        with self.stats_path.open("w") as f:
            json.dump(self.stats, f, indent=4, ensure_ascii=False)

        pygame.quit()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self):
        self.all_sprites.update()

        # if player collides with platform at the bottom, not detect collision
        # else detect collision
        
        # get platforms that under the player
        if not self.player.gravity_reversed:
            platforms_under_player = [platform for platform in self.platforms if platform.rect.top + 20 >= self.player.rect.bottom]
            self.platforms_ = pygame.sprite.Group(platforms_under_player)

        else:
            platforms_under_player = [platform for platform in self.platforms if platform.rect.bottom - 20 <= self.player.rect.top]
            self.platforms_ = pygame.sprite.Group(platforms_under_player)

        # check if player collides with platforms
        hits = pygame.sprite.spritecollide(self.player, self.platforms_, False)
        
        if hits:
            self.player.vec.y = 0
            if not self.player.gravity_reversed:
                self.player.rect.bottom = hits[0].rect.top
            else:
                self.player.rect.top = hits[0].rect.bottom
            self.player.is_jumping = False
            self.is_colliding = True
        else:
            self.is_colliding = False

        # player is moving with moving platforms
        if self.is_colliding and isinstance(hits[0], MovingPlatform):
            self.player.rect.x += hits[0].direction * hits[0].speed * 2
        
        hits.clear()
        platforms_under_player.clear()
        self.platforms_.empty()

        # update camera
        self.camera.update(self.player)

        # generate new chunk
        if self.player.rect.top <= self.new_chunk_y + 600:
            self.new_chunk_y -= 600
            for i in range(10):
                is_moving = random.randint(0, 10)

                x = random.randint(0, 800)
                y = random.randint(0, 10)
                w = 100
                h = 30

                if is_moving <= 2:
                    self.platform = Platform(x, y * 100 + self.new_chunk_y, w, h, (255, 0, 0))
                
                else:
                    self.platform = MovingPlatform(x, y * 100 + self.new_chunk_y, w, h, (255, 0, 0))

                self.all_sprites.add(self.platform)
                self.platforms.add(self.platform)

        # remove platforms that under the max_camera_y
        for platform in self.platforms:
            if platform.rect.top >= -self.camera.max_camera_y + 1500:
                platform.kill()

        # kill game if player falls
        if self.player.rect.bottom >= -self.camera.max_camera_y + 2000:
            self.running = False

        # update score
        self.score = (self.camera.max_camera_y - 850) / 2.5

        # kill game if player collides with laser
        if self.laser.check_collision(self.player):
            self.running = False

    def draw(self):
        self.screen.fill((0, 0, 0))

        self.background.draw(self.camera, self.player.rect.top)

        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        self.laser.update(self.score)
        self.screen.blit(self.laser.image, self.camera.apply(self.laser))
        
        if self.player.gravity_reversed:            
            self.screen.blit(pygame.transform.flip(self.screen, False, True), (0, 0))

        text = self.font_big.render(str(int(self.score)), 1, (255, 255, 255))
        self.screen.blit(text, (10, 10))

        max_score = max(self.stats["highest_score"], self.score)

        text = self.font_small.render(f"{int(max_score)}", 1, (255, 215, 0))
        self.screen.blit(text, (10, 55))

        laser_distance = self.laser.y_distance_to_player(self.player)

        text = self.font_medium.render("Laser below", 1, (244, 148, 184))
        text_rect = text.get_rect(center=(400, 20))
        self.screen.blit(text, text_rect)

        text = self.font_small.render(f"{int(laser_distance)}", 1, (255, 215, 0))
        # centered text
        text_rect = text.get_rect(center=(400, 55))
        self.screen.blit(text, text_rect)

        # draw arrows
        if self.player.gravity_reversed:
            self.screen.blit(self.arrow_images[1], (700, 30))
        else:
            self.screen.blit(self.arrow_images[0], (700, 30))

        pygame.display.flip()
        pygame.display.update()


if __name__ == "__main__":
    game = Game()
    game.run()
