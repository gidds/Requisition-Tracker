import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

class Card:
    def __init__(self, title, description, due_date=None):
        self.title = title
        self.description = description
        self.due_date = due_date
        self.comments = []

class List:
    def __init__(self, name):
        self.name = name
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

class Board:
    def __init__(self, name):
        self.name = name
        self.lists = []

    def add_list(self, list):
        self.lists.append(list)

class TrelloApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline Trello")
        self.board = Board("My Board")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, expand=True)

        self.lists_frame = tk.Frame(self.root)
        self.lists_frame.pack(pady=10)

        self.add_list_button = tk.Button(self.lists_frame, text="Add List", command=self.add_list)
        self.add_list_button.pack(side=tk.LEFT)

        self.add_card_button = tk.Button(self.lists_frame, text="Add Card", command=self.add_card)
        self.add_card_button.pack(side=tk.LEFT)

    def add_list(self):
        list_name = simpledialog.askstring("Add List", "Enter list name")
        if list_name:
            new_list = List(list_name)
            self.board.add_list(new_list)
            self.notebook.add(tk.Frame(self.notebook), text=list_name)

    def add_card(self):
        list_index = self.notebook.index(self.notebook.select())
        list_name = self.notebook.tab(list_index, "text")
        for list in self.board.lists:
            if list.name == list_name:
                card_title = simpledialog.askstring("Add Card", "Enter card title")
                card_description = simpledialog.askstring("Add Card", "Enter card description")
                due_date = simpledialog.askstring("Add Card", "Enter due date (optional)")
                if card_title and card_description:
                    new_card = Card(card_title, card_description, due_date)
                    list.add_card(new_card)
                    card_frame = tk.Frame(self.notebook.select())
                    card_frame.pack(fill=tk.BOTH, expand=True)
                    tk.Label(card_frame, text=card_title).pack()
                    tk.Label(card_frame, text=card_description).pack()
                    if due_date:
                        tk.Label(card_frame, text=f"Due: {due_date}").pack()
                    comment_button = tk.Button(card_frame, text="Comment", command=lambda: self.comment_card(new_card))
                    comment_button.pack()
                    edit_button = tk.Button(card_frame, text="Edit", command=lambda: self.edit_card(new_card))
                    edit_button.pack()
                    delete_button = tk.Button(card_frame, text="Delete", command=lambda: self.delete_card(new_card))
                    delete_button.pack()

    def comment_card(self, card):
        comment = simpledialog.askstring("Comment", "Enter comment")
        if comment:
            card.comments.append(comment)
            messagebox.showinfo("Comment Added", "Comment added successfully")

    def edit_card(self, card):
        new_title = simpledialog.askstring("Edit Card", "Enter new title")
        new_description = simpledialog.askstring("Edit Card", "Enter new description")
        if new_title and new_description:
            card.title = new_title
            card.description = new_description
            messagebox.showinfo("Card Edited", "Card edited successfully")

    def delete_card(self, card):
        confirm = messagebox.askyesno("Delete Card", "Are you sure you want to delete this card?")
        if confirm:
            for list in self.board.lists:
                if card in list.cards:
                    list.cards.remove(card)
                    messagebox.showinfo("Card Deleted", "Card deleted successfully")

if __name__ == "__main__":
    root = tk.Tk()
    app = TrelloApp(root)
    root.mainloop()