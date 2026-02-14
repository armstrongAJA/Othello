import tkinter as tk

root = tk.Tk()
root.title('Tk click test')
c = tk.Canvas(root, width=400, height=300, bg='green')
c.pack(fill='both', expand=True)

def log(e):
    print('PRESS', e.x, e.y, 'widget=', e.widget)
    dot = c.create_oval(e.x-4, e.y-4, e.x+4, e.y+4, fill='red', outline='')
    root.after(200, lambda: c.delete(dot))

root.bind_all('<ButtonPress-1>', log, add='+')
root.mainloop()