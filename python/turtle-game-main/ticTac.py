import turtle

screen = turtle.Screen()
screen.title("SAR's Tic Tac Toe")

current_mode = "light"
font_setup = ("Arial", 32, "bold")

drawer = turtle.Turtle()
drawer.speed(0)
drawer.pensize(3)
drawer.hideturtle()

text_writer = turtle.Turtle()
text_writer.hideturtle()
text_writer.penup()

X_score = 0
O_score = 0

def apply_theme():
    if current_mode == "light":
        screen.bgcolor("white")
        drawer.color("black")
        text_writer.color("black")
    else:
        screen.bgcolor("black")
        drawer.color("white")
        text_writer.color("white")

def toggle_mode():
    global current_mode
    current_mode = "dark" if current_mode == "light" else "light"
    apply_theme()
    redraw_labels()

screen.listen()
screen.onkey(toggle_mode, "t")

def draw_board():
    drawer.clear()
    for x in [-100, 100]:
        drawer.penup()
        drawer.goto(x, 300)
        drawer.pendown()
        drawer.goto(x, -300)
    for y in [-100, 100]:
        drawer.penup()
        drawer.goto(-300, y)
        drawer.pendown()
        drawer.goto(300, y)

def redraw_labels():
    text_writer.clear()
    text_writer.goto(0, 370)
    text_writer.write("Press 'T' to toggle theme", align="center", font=("Arial", 20, "italic"))

grid_positions = {
    (0, 0): (0, 0), (0, 1): (200, 0), (0, 2): (-200, 0),
    (1, 0): (0, -200), (1, 1): (200, -200), (1, 2): (-200, -200),
    (2, 0): (0, 200), (2, 1): (200, 200), (2, 2): (-200, 200)
}

board = [["" for _ in range(3)] for _ in range(3)]
current_player = "X"

def draw_x(x, y):
    drawer.penup()
    drawer.goto(x - 40, y + 40)
    drawer.pendown()
    drawer.goto(x + 40, y - 40)
    drawer.penup()
    drawer.goto(x - 40, y - 40)
    drawer.pendown()
    drawer.goto(x + 40, y + 40)

def draw_o(x, y):
    drawer.penup()
    drawer.goto(x, y - 40)
    drawer.pendown()
    drawer.circle(40)

def check_winner():
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != "":
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] != "":
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] != "":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != "":
        return board[0][2]
    return None

def board_full():
    return all(board[r][c] != "" for r in range(3) for c in range(3))

def click_handler(x, y):
    global current_player, X_score, O_score
    for (row, col), (cx, cy) in grid_positions.items():
        if cx - 100 < x < cx + 100 and cy - 100 < y < cy + 100:
            if board[row][col] == '':
                board[row][col] = current_player
                if current_player == 'X':
                    draw_x(cx, cy)
                    current_player = 'O'
                else:
                    draw_o(cx, cy)
                    current_player = 'X'

                winner = check_winner()
                if winner:
                    announce_result(f"Player {winner} wins!")
                    if winner == "X":
                        X_score += 1
                    else:
                        O_score += 1
                    show_play_again()
                    return
                elif board_full():
                    announce_result("It's a Tie!")
                    show_play_again()
                    return
            break

def announce_result(message):
    text_writer.clear()
    redraw_labels()
    text_writer.goto(0, 330)
    text_writer.write(message, align="center", font=font_setup)

def reset_game():
    global board, current_player
    board = [['' for _ in range(3)] for _ in range(3)]
    current_player = 'X'
    drawer.clear()
    text_writer.clear()
    draw_board()
    redraw_labels()
    screen.onscreenclick(click_handler)
    apply_theme()

def show_play_screen():
    apply_theme()
    text_writer.clear()
    text_writer.goto(0, 0)
    text_writer.write("Play", align="center", font=("Arial", 40, "bold"))

    def start_click(x, y):
        if -80 < x < 80 and -40 < y < 40:
            text_writer.clear()
            draw_board()
            redraw_labels()
            apply_theme()
            screen.onscreenclick(click_handler)

    screen.onscreenclick(start_click)

def show_play_again():
    screen.onscreenclick(None)
    text_writer.goto(0, -400)
    text_writer.write("Click here to Play Again", align="center", font=("Arial", 24, "bold"))

    def play_again_click(x, y):
        if -200 < x < 200 and -430 < y < -370:
            text_writer.clear()
            reset_game()

    screen.onscreenclick(play_again_click)

show_play_screen()
screen.mainloop()
