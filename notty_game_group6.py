import sys
import random
import pygame
from pygame.locals import *
from functools import partial

# initializtion
pygame.init()
pygame.font.init()
pygame.mixer.init()

# basic font
font = pygame.font.SysFont("markerfelt", 20)

# full screen and width and height
info = pygame.display.Info()
WINDOW_WIDTH = info.current_w
WINDOW_HEIGHT = info.current_h

# game screen parameters
TOOLBAR_WIDTH = 400
TOOLBAR_COLOR = (100, 100, 100)
PADDING = 8
CARD_SIZE = (70, 100)
PROFILE_IMAGE_RADIUS = 50

background_color = (205,230,255)
white = (255, 254, 235)
grey = (220, 220, 220)
black = (0, 0, 0)
light = (69, 142, 123)
dark = (38, 84, 72)
message_color = (255, 100, 100)
disabled_color = (148, 172, 166)

COLOUR_TO_NUM = {'red': 0, 'yellow': 1, 'green': 2, 'blue': 3}
NUM_TO_COLOUR = {0: 'red', 1: 'yellow', 2: 'green', 3: 'blue'}
MIN_LENGTH = 3 

# music
pygame.mixer.music.load('notty_game_music/entergame.mp3')
pygame.mixer.music.play(-1)
game_bg_sound=pygame.mixer.Sound('notty_game_music/main_bg.mp3')
winner_sound=pygame.mixer.Sound('notty_game_music/clap.mp3')
loser_sound=pygame.mixer.Sound('notty_game_music/lose.wav')
button_sound=pygame.mixer.Sound('notty_game_music/clicking.mp3')

# card images
card_images = {}
for color in range(4):
    for num in range(10):
        card_images[(color, num)] = pygame.image.load(f"notty_game_img/{NUM_TO_COLOUR[color]}_{num + 1}.png")

# base class of deck and collection
class CardGroup():
    def __init__(self, cards):
        self.cards = cards

    def shuffle(self):
        random.shuffle(self.cards)

    def add_a_card(self, card):
        self.cards.append(card)

    def pop_a_card(self):
        self.shuffle()
        return self.cards.pop()
            
    def is_valid_group(self):
        if len(self.cards) < 3 or self.cards is None:
            return False
        colour = [c[0] for c in self.cards]
        number = [n[1] for n in self.cards]
        sorted_number = sorted(number)
        if len(set(colour)) == 1 and len(set(number)) == len(number):
            for i in range(len(number)):
                if i != 0 and sorted_number[i] - sorted_number[i-1] != 1:
                    return False
            return True
        if len(set(number)) == 1 and len(set(colour)) == len(colour):
            return True
        return False
                
    # create a matrix for counting cards (row: colour, column: number)
    # if I have "red 3, red 5, green 1, blue 7, blue 8" in my hand, the counting table will be like:
    # 0 0 1 0 1 0 0 0 0 0
    # 0 0 0 0 0 0 0 0 0 0
    # 1 0 0 0 0 0 0 0 0 0
    # 0 0 0 0 0 0 1 1 0 0 
    
    def get_counting_table(self):
        # create a matrix for counting cards (row: colour, column: number)
        table = [[0 for _ in range(10)] for _ in range(4)]
        for card in self.cards:
            table[card[0]][card[1]] += 1
        return table

    # find all valid groups
    def find_all_valid_groups(self):
        counting_table = self.get_counting_table()

        # list for recording the valid group, which is a list of list of tuples
        valid_list = []

        # check if any number has three colours or more
        for n in range(10):
            color_in_that_num = []
            for c in range(4):
                if counting_table[c][n] > 0:
                    color_in_that_num.append((c, n))
            if len(color_in_that_num) >= 3:
                valid_list.append(color_in_that_num)

        # check if any colour has three consecutive numbers or more
        for c in range(4):
            num_in_that_color = counting_table[c]
            possible_valid_list = []
            start_or_continue = False
            for n in range(10):
                if num_in_that_color[n] > 0:
                    possible_valid_list.append((c, n))
                    if not start_or_continue:
                        start_or_continue = True
                else:
                    if start_or_continue:
                        start_or_continue = False
                if (not start_or_continue or n == 9):
                    # append the list of tuples after the end of the consecutive numbers
                    # consider all combinations when there are more than three consecutive numbers in that colour
                    if len(possible_valid_list) >= MIN_LENGTH:
                        valid_list.append(possible_valid_list)
                    if len(possible_valid_list) > 0:
                        possible_valid_list = []

        if len(valid_list) == 0:
            return None
        else:
            return valid_list

    def find_largest_valid_group(self):
        valid_card_list = self.find_all_valid_groups()
        if valid_card_list == None:
            return None
        else:
            max_len = 0
            max_list = []
            for v in valid_card_list:
                if len(v) > max_len:
                    max_len = len(v)
                    max_list = v
            return max_list
                
    # find all waiting cards
    # Ex. input "red 2, red 3" return "red 1, red 4"
    def waiting_list(self):
        waiting_list = []
        color_groups = dict()
        number_groups = dict()

        for card in self.cards:
            if card[0] in color_groups:
                color_groups[card[0]].append(card[1])
            else:
                color_groups[card[0]] = [card[1]]
            if card[1] in number_groups:
                number_groups[card[1]].append(card[0])
            else:
                number_groups[card[1]] = [card[0]]

        for color, numbers in color_groups.items():
            numbers.sort()
            for i in range(len(numbers) - 1):
                if numbers[i + 1] == numbers[i] + 1:
                    missing_low = numbers[i] - 1
                    missing_high = numbers[i + 1] + 1
                    if missing_low > 0 and missing_low not in numbers:
                        waiting_list.append((color, missing_low))
                    if missing_high <= 10 and missing_high not in numbers:
                        waiting_list.append((color, missing_high))
                if numbers[i + 1] - numbers[i] == 2:
                    waiting_list.append((color, numbers[i] + 1))

        for number, colors in number_groups.items():
            if len(set(colors)) == 2:
                missing_colors = {0, 1, 2, 3} - set(colors)
                for color in missing_colors:
                    waiting_list.append((color, number))
        
        return waiting_list

class Deck(CardGroup):
    def __init__(self, cards):
        super().__init__(cards)
        self.build()

    def build(self):
        for c in range(4):
            for n in range(10):
                for _ in range(2):
                    self.cards.append((c, n))

# player or computer cards
class Collection(CardGroup):
    def __init__(self, deck, cards, player_name, player_img = None):
        self.cards = cards if cards is not None else []
        self.deck = deck
        self.player_name = player_name
        self.player_img = player_img

    def get_a_card_from(self, source):
        if len(self.cards) < 20:
            source.shuffle()
            self.add_a_card(source.pop_a_card())
   
    def display_cards(self, y_start, player_type, cards_to_discard=[]):
        card_rects = []
        x_start = 450 if (player_type == "player") else 560
        card_x_start = x_start + 18 if (player_type == "player") else x_start + 58
        card_y_start = y_start + 15
        img_x_start = 1320 if (player_type == "player") else 440
        text_x_start = 1350 if (player_type == "player") else 445

        bg = pygame.image.load('notty_game_img/bg_box_' + player_type + '.png')
        screen.blit(bg, (x_start, y_start))

        text_surf = font.render(self.player_name, True, white)
        screen.blit(text_surf, (text_x_start, y_start + 110))
        if self.player_img:
            img = pygame.image.load(self.player_img).convert_alpha()
            img = pygame.transform.scale(img, (PROFILE_IMAGE_RADIUS * 2, PROFILE_IMAGE_RADIUS * 2))
            screen.blit(img, (img_x_start, y_start))
        for n in range(len(self.cards)):
            card = card_images[(self.cards[n][0], self.cards[n][1])]
            card = pygame.transform.scale(card, CARD_SIZE)
            if n < 10:
                pos = (card_x_start + (CARD_SIZE[0] + PADDING) * n, card_y_start)
            else:
                pos = (card_x_start + (CARD_SIZE[0] + PADDING) * (n - 10), card_y_start + (CARD_SIZE[1] + PADDING))
            rect = (pygame.Rect(pos, CARD_SIZE), self.cards[n])
            if rect in cards_to_discard:
                # draw selected border
                pygame.draw.rect(screen, dark, pygame.Rect(pos[0] - 5, pos[1] - 5, CARD_SIZE[0] + 10, CARD_SIZE[1] + 10), 3, 20)  
            screen.blit(card, pos)
            card_rects.append(rect)
        return card_rects

    def handle_click_card(self, card_rects):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        
        for rect in card_rects:
            if rect[0].x + rect[0].w > mouse[0] > rect[0].x and rect[0].y + rect[0].h > mouse[1] > rect[0].y:
                if click[0]:
                    return rect
        return None

# class Play contains drawing cards from the deck or others, and discarding valid group
class Play:

    def __init__(self, computer_num, difficulty):
        self.deck = Deck([])
        self.computer_list = []
        self.drawn_from_deck = False
        self.drawn_from_comp = False
        self.game_started = False
        self.winner = None
        self.cards_to_discard = []
        self.play_for_me = False

        if computer_num == 1:
            self.computer_list.append(Collection(self.deck, [], f"computer", f"notty_game_img/{difficulty}_1.png"))
        else:
            for n in range(computer_num):
                self.computer_list.append(Collection(self.deck, [], f"computer {n+1}", f"notty_game_img/{difficulty}_{n+1}.png"))
        self.computer_difficulty = difficulty
        self.player = Collection(self.deck, [], "player", f"notty_game_img/player.png")
        self.current_player = self.player

        self.buttons = [
            Button("DISCARD", 30, 520, 300, 70, light, dark, self.player_put_VG_back_to_deck, "got a valid group finally"),
            Button("PASS", 30, 620, 300, 70, light, dark, self.player_turn_over, "finish all I wanna do"),
            Button("EXIT", 200, 70, 100, 70, (120, 150, 175), (80, 110, 135), self.exit, "I wanna go"),
            Button("PLAY FOR ME", 30, 720, 300, 70, light, dark, self.player_out, "take a rest for a while")
        ]

        if computer_num == 2:
            self.buttons += [Button("comp1", 30, 220, 95, 70, light, dark, partial(self.player_get_from_computer_i, 1), "draw from computer"),
            Button("comp2", 140, 220, 95, 70, light, dark, partial(self.player_get_from_computer_i, 2)),
            Button("+1", 30, 360, 95, 70, light, dark, partial(self.player_get_from_deck, 1), "draw from deck"),
            Button("+2", 140, 360, 95, 70, light, dark, partial(self.player_get_from_deck, 2)),
            Button("+3", 250, 360, 95, 70, light, dark, partial(self.player_get_from_deck, 3))]
        
        elif computer_num == 1:
            self.buttons += [Button("comp", 30, 220, 95, 70, light, dark, partial(self.player_get_from_computer_i, 1), "draw from computer"),
            Button("+1", 30, 360, 95, 70, light, dark, partial(self.player_get_from_deck, 1), "draw from deck"),
            Button("+2", 140, 360, 95, 70, light, dark, partial(self.player_get_from_deck, 2)),
            Button("+3", 250, 360, 95, 70, light, dark, partial(self.player_get_from_deck, 3))]
            
    def update_discard_button_status(self):
        # discard_button = next((btn for btn in self.buttons if btn.text == "DISCARD"), None)
        discard_button = [btn for btn in self.buttons if btn.text == "DISCARD"][0]
        if discard_button:
            valid_group = self.player.find_all_valid_groups()
            if valid_group:
                discard_button.color = light
                discard_button.hover_color = dark
                discard_button.action = self.player_put_VG_back_to_deck
            else:
                discard_button.color = disabled_color
                discard_button.hover_color = disabled_color
                discard_button.action = None

    def start_game(self):
        self.game_started = True
        self.get_initial_cards()
        self.update_discard_button_status()
        pygame.mixer.music.pause()
        game_bg_sound.play()

    def get_initial_cards(self):
        for _ in range(5):
            self.player.get_a_card_from(self.deck)
            for c in self.computer_list:
                c.get_a_card_from(self.deck)

    def a_get_from_b(self, a, b, n):

        if len(a.cards) + n <= 20 and len(b.cards) >= n:
            for _ in range(n):
                a.get_a_card_from(b)
        else:
            n_limit = 20 - len(a.cards)
            for _ in range(n_limit):
                a.get_a_card_from(b)
        self.display_all_cards()
        self.check_game_over()
        self.update_buttons_visibility(len(self.player.cards))
        self.update_discard_button_status()
    
    def player_get_from_deck(self, n):
        if not self.drawn_from_deck:
            self.a_get_from_b(self.player, self.deck, n)
            self.drawn_from_deck = True
            self.update_draw_from_deck_buttons()

    def player_get_from_computer_i(self, i):
        if not self.drawn_from_comp:
            self.a_get_from_b(self.player, self.computer_list[i-1], 1)
            self.drawn_from_comp = True
            self.update_draw_from_comp_buttons()

    def computer_i_get_n_from_deck(self, computer_num, n):
        self.a_get_from_b(self.computer_list[computer_num], self.deck, n)

    def computer_i_get_1_from_player(self, computer_num):
        self.a_get_from_b(self.computer_list[computer_num], self.player, 1)

    def computer_i_get_1_from_computer_j(self, computer_i, computer_j):
        self.a_get_from_b(self.computer_list[computer_i], self.computer_list[computer_j], 1)

    def someone_put_LVG_back_to_deck(self, who):
        remove_cards = who.find_largest_valid_group()
        if remove_cards is not None:
            for card in remove_cards:
                who.cards.remove(card)
                self.deck.add_a_card(card)
        self.display_all_cards()
        self.check_game_over()

    def computer_i_put_LVG_back_to_deck(self, computer_num):
        self.someone_put_LVG_back_to_deck(self.computer_list[computer_num-1])

    def player_put_VG_back_to_deck(self):
        cards_to_discard_collection = Collection(self.deck, [card[1] for card in self.cards_to_discard], "cards to discard")
        if cards_to_discard_collection.is_valid_group():
            for card in cards_to_discard_collection.cards:
                self.player.cards.remove(card)
                self.deck.add_a_card(card)
            self.cards_to_discard.clear()
        else:
            self.display_warning("Invalid Group!", 120, 545)
        self.display_all_cards()
        self.check_game_over()
        self.update_discard_button_status()
        self.update_buttons_visibility(len(self.player.cards))
    
    def display_warning(self, message, x, y):
        warning_text = font.render(message, True, message_color)
        screen.blit(warning_text, (x, y))
        pygame.display.update()
        pygame.time.wait(500)
    
    def display_all_cards(self):
        bg_image = pygame.image.load('notty_game_img/bg_game.png')
        bg_image = pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(bg_image, (0, 0))
        self.display_player_info(self.current_player)
        for i in range(len(self.computer_list)):
            self.computer_list[i].display_cards(60 + 270 * i, "computer")
        self.player.display_cards(610, "player", self.cards_to_discard)
        if self.play_for_me:
            Button("BACK TO GAME", 30, 720, 300, 70, light, dark, current_play.back_to_player, "I'm back!").draw(screen)
        pygame.display.update()

    def display_player_info(self, current_player):
        if current_player.player_img:
            img = pygame.image.load(current_player.player_img).convert_alpha()
            img = pygame.transform.scale(img, (PROFILE_IMAGE_RADIUS * 2, PROFILE_IMAGE_RADIUS * 2))
            img_circle = pygame.Surface((PROFILE_IMAGE_RADIUS * 2, PROFILE_IMAGE_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.circle(img_circle, (255, 255, 255), (PROFILE_IMAGE_RADIUS, PROFILE_IMAGE_RADIUS), PROFILE_IMAGE_RADIUS)
            img_circle.blit(img, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            screen.blit(img_circle, (50, 50))
        name_text = font.render(f"{current_player.player_name}'s turn", True, dark)
        screen.blit(name_text, (40, 20))

    def computer_action(self, i):
        if self.computer_difficulty == 'dumb':
            self.computer_dumb_action(i)
        else:
            self.computer_smart_action(i)

    def computer_dumb_action(self, i):
        self.computer_i_get_n_from_deck(i, random.randint(1, 3))
        pygame.time.wait(100)
        if random.uniform(0, 1) > 0.5:
            self.computer_i_get_1_from_player(i)
            pygame.time.wait(100)
        self.computer_i_put_LVG_back_to_deck(i)
        pygame.time.wait(100)

    def computer_smart_action(self, i):
        if len(self.computer_list[i].cards) < 20:
            self.computer_i_put_LVG_back_to_deck(i)
            pygame.time.wait(100)

            w = len(self.computer_list[i].waiting_list())
            self.computer_i_get_n_from_deck(i, max(min(int(w/2), 3), 1))

            self.computer_i_put_LVG_back_to_deck(i)
            pygame.time.wait(100)

            p = self.probability_of_valid_group_if_i_draw_from_j(self.computer_list[i], self.player)

            if len(self.computer_list) == 2:
                another = 1 if i == 0 else 0
                c = self.probability_of_valid_group_if_i_draw_from_j(self.computer_list[i], self.computer_list[another])
                if p > max(c, 0.5) and len(self.player.cards) > 3:
                    self.computer_i_get_1_from_player(i)
                elif c > max(p, 0.5) and len(self.computer_list[another].cards) > 3:
                    self.computer_i_get_1_from_computer_j(i, another)
            else:
                if p > 0.5 and len(self.player.cards) > 3:
                    self.computer_i_get_1_from_player(i)
            pygame.time.wait(100)
        
        self.computer_i_put_LVG_back_to_deck(i)
        pygame.time.wait(100)

    def player_out(self):
        self.play_for_me = True

    def comp_play_for_player(self):
        if self.drawn_from_deck == False:
            w = len(self.player.waiting_list())
            self.player_get_from_deck(max(min(int(w/2), 3), 1))
            pygame.time.wait(100)
        if self.drawn_from_comp == False:
            if len(self.computer_list) == 2:
                c1 = self.probability_of_valid_group_if_i_draw_from_j(self.player, self.computer_list[0])
                c2 = self.probability_of_valid_group_if_i_draw_from_j(self.player, self.computer_list[1])
                if c1 > max(c2, 0.5) and len(self.computer_list[0].cards) > 3:
                    self.player_get_from_computer_i(1)
                elif c2 > max(c1, 0.5) and len(self.computer_list[1].cards) > 3:
                    self.player_get_from_computer_i(2)
            else:
                c1 = self.probability_of_valid_group_if_i_draw_from_j(self.player, self.computer_list[0]) and len(self.computer_list[0].cards) > 3
                if c1 > 0.5 and len(self.computer_list[0].cards) > 3:
                    self.player_get_from_computer_i(1)
        self.someone_put_LVG_back_to_deck(self.player)

    def back_to_player(self):
        self.play_for_me = False

    def update_draw_from_deck_buttons(self):
        for button in self.buttons:
            if button.text in ["+1", "+2", "+3"]:
                button.color = disabled_color
                button.hover_color = disabled_color
                button.action = None
                
    def update_buttons_visibility(self, card_count):
        if not self.drawn_from_deck:
            for button in self.buttons:
                if card_count == 18 and button.text in ["+3"]:
                    button.color = disabled_color
                    button.hover_color = disabled_color
                    button.action = None
                elif card_count == 19 and button.text in ["+2","+3"]:
                    button.color = disabled_color
                    button.hover_color = disabled_color
                    button.action = None
                elif card_count >= 20 and button.text in ["+1","+2","+3"]:
                    button.color = disabled_color
                    button.hover_color = disabled_color
                    button.action = None
                elif card_count < 18:
                    self.reset_draw_from_deck_buttons()

    def update_draw_from_comp_buttons(self):
        for button in self.buttons:
            if button.text in ["comp", "comp1", "comp2"]:
                button.color = disabled_color
                button.hover_color = disabled_color
                button.action = None

    def reset_draw_from_deck_buttons(self):
        self.drawn_from_deck = False
        action_list = [partial(self.player_get_from_deck, 1), partial(self.player_get_from_deck, 2), partial(self.player_get_from_deck, 3)]
        for button in self.buttons:
            if button.text in ["+1", "+2", "+3"]:
                button.color = light
                button.hover_color = dark
                button.action = action_list[["+1", "+2", "+3"].index(button.text)]

    def reset_draw_from_comp_buttons(self):
        self.drawn_from_comp = False
        action_list = [partial(self.player_get_from_computer_i, 1), partial(self.player_get_from_computer_i, 1), partial(self.player_get_from_computer_i, 2)]
        for button in self.buttons:
            if button.text in ["comp", "comp1", "comp2"]:
                button.color = light
                button.hover_color = dark
                button.action = action_list[["comp", "comp1", "comp2"].index(button.text)]

    def probability_of_valid_group_if_i_draw_from_j(self, i, j):
        wl = i.waiting_list()
        valid_count = 0
        for card in j.cards:
            if card in wl:
                valid_count += 1
        return valid_count / len(j.cards)

    def player_turn_over(self):
        if self.current_player == self.player:
            self.cards_to_discard.clear()
            self.current_player = self.computer_list[0]
        elif self.current_player == self.computer_list[-1]:
            self.current_player = self.player
        else:
            next = self.computer_list.index(self.current_player) + 1
            self.current_player = self.computer_list[next]
            
        self.reset_draw_from_deck_buttons()
        self.reset_draw_from_comp_buttons()
        self.display_all_cards()
        self.update_buttons_visibility(len(self.current_player.cards))
        self.update_discard_button_status() 

    def check_game_over(self):
        global game_over
        max_card_count = 0
        if len(self.player.cards) == 0:
            game_over = True
            self.winner = "player"
        else:
            for i in range(len(self.computer_list)):
                if len(self.computer_list[i].cards) == 0:
                    game_over = True
                    self.winner = f"Computer {i+1}"
                if len(self.computer_list[i].cards) == 20:
                    max_card_count += 1
            if max_card_count == len(self.computer_list) and len(self.player.cards) == 20 and not self.player.find_all_valid_groups():
                game_over = True
                self.winner = "Nobody"

    def exit(self):
        pygame.quit()
        sys.exit()

class Button:
    def __init__(self, text, x, y, w, h, color, hover_color, action=None, description=None):
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.description = description

    def draw(self, screen):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if self.x + self.w > mouse[0] > self.x and self.y + self.h > mouse[1] > self.y:
            pygame.draw.rect(screen, self.hover_color, (self.x, self.y, self.w, self.h), 0, 15)
            if click[0] == 1:
                if self.action:
                    button_sound.play()
                    pygame.time.delay(200)
                    self.action()
        else:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.w, self.h), 0, 15)

        text_surface = font.render(self.text, True, grey)
        text_rect = text_surface.get_rect()
        text_rect.center = (self.x + (self.w / 2), self.y + (self.h / 2))
        screen.blit(text_surface, text_rect)

        discrption_font = pygame.font.SysFont("chalkduster", 14)
        if self.description:
            text_surf = discrption_font.render(self.description, True, dark)
            screen.blit(text_surf, (self.x, self.y + (self.h / 2) - 60))

class StartButton(Button):
    def __init__(self, text, x, y, w, h, color, hover_color, action=None, description=None):
        super().__init__(text, x, y, w, h, color, hover_color, action, description)
        self.selected = False

    def draw(self, screen):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if self.selected:
            button_color = dark
            button_hover_color = light
        else:
            button_color = light
            button_hover_color = dark

        if self.x + self.w > mouse[0] > self.x and self.y + self.h > mouse[1] > self.y:
            pygame.draw.rect(screen, button_hover_color, (self.x, self.y, self.w, self.h), 0, 15)
            if click[0] == 1:
                if self.action:
                    button_sound.play()
                    pygame.time.delay(200)
                    self.action()
                    self.selected = True
        else:
            pygame.draw.rect(screen, button_color, (self.x, self.y, self.w, self.h), 0, 15)

        text_surface = font.render(self.text, True, grey)
        text_rect = text_surface.get_rect()
        text_rect.center = (self.x + (self.w / 2), self.y + (self.h / 2))
        screen.blit(text_surface, text_rect)

        discrption_font = pygame.font.SysFont("chalkduster", 12)
        if self.description:
            text_surf = discrption_font.render(self.description, True, white)
            screen.blit(text_surf, (self.x, self.y + (self.h / 2) - 60))

class BaseScreen:
    def __init__(self):
        pass
    
    def draw(self, screen):
        pass

class StartScreen(BaseScreen):
    def __init__(self):
        super().__init__()
        self.computer_count = 1
        self.computer_difficulty = "dumb"

        self.start_button = StartButton("START", 950, 700, 200, 60, light, dark, self.start_game)
        self.comp_1_button = StartButton("1", 150, 500, 200, 60, light, dark, partial(self.set_computer_count, 1))
        self.comp_2_button = StartButton("2", 400, 500, 200, 60, light, dark, partial(self.set_computer_count, 2))
        self.dumb_button = StartButton("Dumb", 800, 500, 200, 60, light, dark, partial(self.set_computer_difficulty, 'dumb'))
        self.smart_button = StartButton("Smart", 1050, 500, 200, 60, light, dark, partial(self.set_computer_difficulty, 'smart'))
        self.exit_button = Button("EXIT", 1200, 700, 200, 60, light, dark, self.quit_game)
        
        self.buttons = [
            self.start_button,
            self.comp_1_button,
            self.comp_2_button,
            self.dumb_button,
            self.smart_button,
            self.exit_button
        ]

        self.reset_selection()

    def draw(self, screen):
        start_bg = pygame.image.load('notty_game_img/bg_menu.png')
        start_bg = pygame.transform.scale(start_bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(start_bg, (0, 0))

        title_font = pygame.font.SysFont("markerfelt", 60)
        title_text = title_font.render("Notty Game", True, white)
        screen.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, WINDOW_HEIGHT // 10))

        content_font = pygame.font.SysFont("markerfelt", 25)
        choose_number_text = content_font.render("# STEP 1 Choose the opponent number", True, dark)
        screen.blit(choose_number_text, (180, 280))

        comp_1_img = pygame.image.load('notty_game_img/one_player.png')
        screen.blit(comp_1_img, (200, 380))
        comp_2_img = pygame.image.load('notty_game_img/two_player.png')
        screen.blit(comp_2_img, (420, 360))

        choose_difficulty_text = content_font.render("# STEP 2 Choose the opponent type", True, dark)
        screen.blit(choose_difficulty_text, (850, 280))

        dumb_img = pygame.image.load('notty_game_img/dumb_1.png')
        screen.blit(dumb_img, (845, 340))
        smart_img = pygame.image.load('notty_game_img/smart_1.png')
        screen.blit(smart_img, (1090, 340))

        for button in self.buttons:
            button.draw(screen)
        self.start_button.selected = False

    def set_computer_count(self, count):
        self.computer_count = count

        if self.computer_count == 1:
            self.comp_1_button.selected = True
            self.comp_2_button.selected = False
        elif self.computer_count == 2:
            self.comp_1_button.selected = False
            self.comp_2_button.selected = True

    def set_computer_difficulty(self, difficulty):
        self.computer_difficulty = difficulty

        if self.computer_difficulty == "dumb":
            self.dumb_button.selected = True
            self.smart_button.selected = False
        elif self.computer_difficulty == "smart":
            self.dumb_button.selected = False
            self.smart_button.selected = True

    def reset_selection(self):
        self.computer_count = 1
        self.computer_difficulty = "dumb"
        self.comp_1_button.selected = True
        self.comp_2_button.selected = False
        self.dumb_button.selected = True
        self.smart_button.selected = False

    def start_game(self):
        global current_play
        current_play = Play(self.computer_count, self.computer_difficulty)
        current_play.start_game()
        global game_started
        game_started = True
        self.reset_selection()

    def quit_game(self):
        pygame.quit()
        sys.exit()

class PlayScreen(BaseScreen):
    def __init__(self, play):
        super().__init__()
        self.play = play

    def draw(self, screen):
        bg_image = pygame.image.load('notty_game_img/bg_game.png')
        bg_image = pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(bg_image, (0, 0))

        self.play.display_player_info(self.play.current_player)
        for i in range(len(self.play.computer_list)):
            self.play.computer_list[i].display_cards(60 + i * 270, "computer")
        card_rects = self.play.player.display_cards(610, "player", self.play.cards_to_discard)

        clicked_card = self.play.player.handle_click_card(card_rects)
        if clicked_card:
            if clicked_card in self.play.cards_to_discard:
                self.play.cards_to_discard.remove(clicked_card)
            else:
                self.play.cards_to_discard.append(clicked_card)
            pygame.time.delay(200)

        for button in self.play.buttons:
            button.draw(screen)

        pygame.display.update()

class GameOverScreen(BaseScreen):
    def __init__(self, winner):
        super().__init__()
        self.winner = winner

    def draw(self, screen):
        game_over_bg = pygame.image.load('notty_game_img/bg_game_over.png')
        game_over_bg = pygame.transform.scale(game_over_bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(game_over_bg, (0, 0))

        game_over_text = pygame.font.SysFont("markerfelt", 60).render("Game Over", True, (50, 50, 70))
        screen.blit(game_over_text, (WINDOW_WIDTH // 2 - game_over_text.get_width() // 2, WINDOW_HEIGHT // 8))

        winner_text = pygame.font.SysFont("markerfelt", 45).render(f"{self.winner} Wins!", True, (80, 80, 180))
        screen.blit(winner_text, (WINDOW_WIDTH // 2 - winner_text.get_width() // 2, WINDOW_HEIGHT // 8 + 80))

        if self.winner == "player":
            win_image = pygame.image.load('notty_game_img/win.png').convert_alpha()
            screen.blit(win_image, (WINDOW_WIDTH // 2 - win_image.get_width() // 2, WINDOW_HEIGHT // 2 - 200))
            game_bg_sound.stop()
            if not pygame.mixer.get_busy():
                winner_sound.play()
        else:
            lose_image = pygame.image.load('notty_game_img/lose.png').convert_alpha()
            screen.blit(lose_image, (WINDOW_WIDTH // 2 - lose_image.get_width() // 2, WINDOW_HEIGHT // 2 - 200))
            game_bg_sound.stop()
            if not pygame.mixer.get_busy():
                loser_sound.play()

        restart_button = Button("RESTART", WINDOW_WIDTH // 2 - 215, WINDOW_HEIGHT // 2 + 250, 200, 60, light, dark, self.restart_game)
        restart_button.draw(screen)

        exit_button = Button("EXIT", WINDOW_WIDTH // 2 + 15, WINDOW_HEIGHT // 2 + 250, 200, 60, light, dark, self.exit_game)
        exit_button.draw(screen)

        pygame.display.update()

    def restart_game(self):
        global game_over, game_started
        game_over = False
        game_started = False
        pygame.mixer.music.play(-1,1.0)
        winner_sound.stop()
        loser_sound.stop()

    def exit_game(self):
        pygame.quit()
        sys.exit()

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Notty game')

game_started = False
game_over = False
current_play = None
start_screen = StartScreen()

# main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    if not game_started:
        start_screen.draw(screen)
    elif game_over:
        GameOverScreen(current_play.winner).draw(screen)
    else:
        if current_play.current_player in current_play.computer_list:
            computer_index = current_play.computer_list.index(current_play.current_player)
            current_play.computer_action(computer_index)
            current_play.player_turn_over()
        elif current_play.current_player == current_play.player:
            if current_play.play_for_me:
                current_play.comp_play_for_player()
                current_play.player_turn_over()
            elif current_play.current_player == current_play.player:
                PlayScreen(current_play).draw(screen)
    pygame.display.update()

