from tkinter import Tk, Canvas, Label, Button, Frame, StringVar, OptionMenu, messagebox
from Board import spaceState
from Player import Player
from AI import AI


class GameUI:
    def __init__(self, game, cell_size=60):
        self.original_game = game
        self.game = game
        self.cell_size = cell_size
        self.size = game.board.size

        self.root = Tk()
        self.root.title("Othello")

        self.main_menu_frame = Frame(self.root)
        self.game_frame = Frame(self.root)

        self.show_main_menu()

    # -------------------------
    # MAIN MENU
    # -------------------------
    def show_main_menu(self):
        self.game_frame.pack_forget()
        self.main_menu_frame.pack()

        Label(self.main_menu_frame, text="Othello", font=("Arial", 24)).pack(pady=20)

        self.white_mode = StringVar(value="Human")
        Label(self.main_menu_frame, text="White Player Mode:").pack()
        OptionMenu(self.main_menu_frame, self.white_mode, "Human", "AI").pack()

        Button(self.main_menu_frame, text="Start Game", command=self.start_game).pack(pady=20)

    # -------------------------
    # START GAME
    # -------------------------
    def start_game(self):
        self.main_menu_frame.pack_forget()
        self.setup_game()
        self.game_frame.pack()

    # -------------------------
    # SETUP GAME SCREEN
    # -------------------------
    def setup_game(self):
        for widget in self.game_frame.winfo_children():
            widget.destroy()

        # Header
        header = Frame(self.game_frame)
        header.pack()

        Button(header, text="Reset", command=self.reset_game).pack(side="left", padx=10)
        Button(header, text="Main Menu", command=self.back_to_menu).pack(side="left")

        self.score_label = Label(header, text="")
        self.score_label.pack(side="right", padx=10)

        # Canvas
        canvas_size = self.size * self.cell_size
        self.canvas = Canvas(self.game_frame, width=canvas_size, height=canvas_size, bg="#006400")
        self.canvas.pack()

        self.status = Label(self.game_frame, text="", font=("Arial", 12))
        self.status.pack()

        self.canvas.bind("<Button-1>", self.on_click)

        # Configure players based on selection
        if self.white_mode.get() == "AI":
            white_player = AI(Player(spaceState.WHITE, mode="AI"))
        else:
            white_player = Player(spaceState.WHITE, mode="human")

        black_player = AI(Player(spaceState.BLACK, mode="AI"))

        self.game.reset(player1=black_player, player2=white_player)

        self.draw_board()
        self.update_status()

    # -------------------------
    # RESET GAME
    # -------------------------
    def reset_game(self):
        self.setup_game()

    # -------------------------
    # BACK TO MENU
    # -------------------------
    def back_to_menu(self):
        self.game_frame.pack_forget()
        self.show_main_menu()

    # -------------------------
    # DRAW BOARD
    # -------------------------
    def draw_board(self):
        self.canvas.delete("all")

        for i in range(self.size + 1):
            x = i * self.cell_size
            self.canvas.create_line(x, 0, x, self.size * self.cell_size)
            y = i * self.cell_size
            self.canvas.create_line(0, y, self.size * self.cell_size, y)

        for y in range(self.size):
            for x in range(self.size):
                cell = self.game.board.board[y][x]
                if cell == spaceState.EMPTY:
                    continue

                cx = x * self.cell_size + self.cell_size // 2
                cy = y * self.cell_size + self.cell_size // 2
                r = int(self.cell_size * 0.4)
                color = "black" if cell == spaceState.BLACK else "white"
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color)

        self.update_scores()

    # -------------------------
    # CLICK HANDLER
    # -------------------------
    def on_click(self, event):
        x = event.x // self.cell_size
        y = event.y // self.cell_size

        if getattr(self.game.current_player, "mode", "human") != "human":
            return

        self.game.play_turn(x, y)
        self.after_move()

    def after_move(self):
        self.draw_board()
        self.update_status()

        # AI turn
        if getattr(self.game.current_player, "mode", "human") == "AI" and not self.game.check_game_over():
            ai_move = self.game.current_player.choose_move(self.game.board)
            if ai_move:
                self.game.play_turn(ai_move[0], ai_move[1])
                self.after_move()
                return

        if self.game.check_game_over():
            winner = self.game.get_winner()
            if winner is None:
                messagebox.showinfo("Game Over", "Tie")
            else:
                color = "Black" if winner.color == spaceState.BLACK else "White"
                messagebox.showinfo("Game Over", f"{color} wins")

    # -------------------------
    # STATUS + SCORES
    # -------------------------
    def update_status(self):
        cp = self.game.current_player
        color = "Black" if cp.color == spaceState.BLACK else "White"
        self.status.config(text=f"Current player: {color}")
        self.update_scores()

    def update_scores(self):
        black_score = self.game.player1.calculateScore(self.game.board)
        white_score = self.game.player2.calculateScore(self.game.board)
        self.score_label.config(text=f"Black: {black_score}   White: {white_score}")

    # -------------------------
    def run(self):
        self.root.mainloop()
