import turtle

screen = turtle.Screen()
screen.title("Tic Tac Toe")

# Light mode/dark mode toggle setup
current_mode = "light"

def toggle_mode():
    global current_mode
    if current_mode == "light":
        screen.bgcolor("black")
        drawer.color("white")
        turtle.color("white")
        current_mode = "dark"
        font_setup = ("Arial", 32)
    else:
        screen.bgcolor("white")
        drawer.color("black")
        turtle.color("black")
        current_mode = "light"
        
        font_setup = ("Arial", 32,)

# Add a button for toggling modes
screen.listen()
screen.onkey(toggle_mode, "t")

# Initialize drawer
drawer = turtle.Turtle()
drawer.speed(0)
drawer.pensize(3)
drawer.hideturtle()
font_setup = ("Arial", 32)

X_score = 0
O_score = 0

turtle.penup()
turtle.speed(0)
turtle.hideturtle()
turtle.goto(-35, 350)
turtle.write(f"{X_score} - {O_score}", font=font_setup)

# Draw the board
def draw_board():
    drawer.penup()
    drawer.goto(-100, 300)
    drawer.pendown()
    drawer.goto(-100, -300)

    drawer.penup()
    drawer.goto(100, 300)
    drawer.pendown()
    drawer.goto(100, -300)

    drawer.penup()
    drawer.goto(-300, 100)
    drawer.pendown()
    drawer.goto(300, 100)

    drawer.penup()
    drawer.goto(-300, -100)
    drawer.pendown()
    drawer.goto(300, -100)

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

grid_positions = {
    (0, 0): (0, 0), (0, 1): (200, 0), (0, 2): (-200, 0),
    (1, 0): (0, -200), (1, 1): (200, -200), (1, 2): (-200, -200),
    (2, 0): (0, 200), (2, 1): (200, 200), (2, 2): (-200, 200)
}

board = [["" for _ in range(3)] for _ in range(3)]
current_player = "X"

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
                    turtle.goto(200, 300)
                    if winner == "X":
                        X_score += 1
                    elif winner == "O":
                        O_score += 1

                    turtle.clear()
                    turtle.write(f"Player {winner} wins!", font=font_setup)
                    turtle.goto(-35, 350)
                    turtle.write(f"{X_score} - {O_score}", font=font_setup)

                    
                    screen.onscreenclick(None)
                    button = turtle.Turtle()
                    button.penup()
                    button.hideturtle()
                    button.goto(0, -400)
                    button.write("Click here to Restart", align="center", font=("Arial", 24, "bold"))

                    def restart_button_click(x, y):
                        if -150 < x < 150 and -430 < y < -370:
                            button.clear()
                            screen.onscreenclick(click_handler)
                            reset_game()

                    screen.onscreenclick(restart_button_click)
                    return
                break


def reset_game():
    global board, current_player
    board = [['' for _ in range(3)] for _ in range(3)]
    current_player = 'X'
    drawer.clear()
    turtle.clear()
    draw_board()
    turtle.goto(-35, 350)
    turtle.write(f"{X_score} - {O_score}", font=font_setup)

draw_board()
screen.onclick(click_handler)
screen.mainloop()