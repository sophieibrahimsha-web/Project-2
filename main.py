# PLANTIVITY
# Main Dashboard + Task Tracker + CalendarView + ProgressView
# Task model + TaskController (shelve)

import shelve
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry, Calendar
from datetime import datetime
from PIL import Image, ImageTk

# Dropdown Options
category_options = ["School", "Work", "Personal", "Health", "Other"]
priority_options = ["High", "Medium", "Low"]
completion_options = ["Not Started", "In Progress", "Completed"]

# Task Model + Controller
class Task:
    def __init__(self, title, description, category, due_date, priority, completion_status="Not Started"):
        self.title = title
        self.description = description
        self.category = category
        self.due_date = due_date
        self.priority = priority
        self.completion_status = completion_status

# Operations on tasks
class TaskController:
    def __init__(self, filename="plantivity_data"):
        self.filename = filename
        self.tasks = []
        self.load()

    # Load tasks from shelve database
    def load(self):
        try:
            with shelve.open(self.filename) as db:
                self.tasks = db.get("tasks", [])
        except (OSError, TypeError, ValueError) as e:
            print("Error loading tasks:", e)
            self.tasks = []

    # Save tasks to shelve database
    def save(self):
        try:
            with shelve.open(self.filename) as db:
                db["tasks"] = self.tasks
        except (OSError, TypeError, ValueError) as e:
            print("Error saving tasks:", e)

    # Add new task
    def add_task(self, t):
        # If >20 tasks, reset
        if len(self.tasks) >= 20:
            self.tasks = []
        self.tasks.append(t)
        self.save()

    # Replace old task with updated task
    def update_task(self, old_task, new_task):
        for i, t in enumerate(self.tasks):
            if t.title == old_task.title:
                self.tasks[i] = new_task
                self.save()
                return True
        return False

    # Delete a task
    def delete_task(self, title):
        for t in list(self.tasks):
            if t.title == title:
                self.tasks.remove(t)
                self.save()
                return True
        return False

    # Return full task list
    def get_all_tasks(self):
        return self.tasks

    # Return completed tasks
    def get_completed_tasks(self):
        return [t for t in self.tasks if t.completion_status == "Completed"]

    # Return percentage of tasks complete
    def get_completion_percentage(self):
        if len(self.tasks) == 0:
            return 0
        return round((len(self.get_completed_tasks()) / len(self.tasks)) * 100, 2)

    # Return incomplete tasks
    def get_incomplete_tasks(self):
        return [t for t in self.tasks if t.completion_status != "Completed"]

    # Return next upcoming task
    def get_next_task(self):
        tasks = self.get_incomplete_tasks()
        if not tasks:
            return None
        try:
            return sorted(tasks, key=lambda t: t.due_date)[0]
        except Exception:
            return None


# Calendar
class CalendarView(tk.Toplevel):
    def __init__(self, parent, controller: TaskController):
        super().__init__(parent)
        self.title("Plantivity ~ Task Calendar")
        self.geometry("900x500")
        self.controller = controller

        # Home button
        home_frame = tk.Frame(self)
        home_frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Button(home_frame, text="Home", command=self.destroy).pack()

        self.calendar = Calendar(
            self, selectmode="day", date_pattern="yyyy-mm-dd", showweeknumbers=False
        )
        self.calendar.grid(row=1, column=0, padx=20, pady=20)
        self.calendar.bind("<<CalendarSelected>>", self.on_select)  # passes event

        right = tk.Frame(self)
        right.grid(row=1, column=1, padx=20)

        tk.Label(right, text="Tasks on selected date", font=("Arial", 14, "bold")).pack()
        self.listbox = tk.Listbox(right, width=50, height=20)
        self.listbox.pack()

        tk.Button(self, text="Close", command=self.destroy).grid(row=2, column=0, columnspan=2, pady=10)

        self.highlight()

    def highlight(self):
        self.calendar.calevent_remove("all")
        for t in self.controller.get_all_tasks():
            try:
                d = datetime.strptime(t.due_date, "%Y-%m-%d").date()
                tag = "done" if t.completion_status == "Completed" else "task"
                self.calendar.calevent_create(d, t.title, tag)
            except (ValueError, TypeError):
                pass

        try:
            self.calendar.tag_config("task", background="#ffd54f")
            self.calendar.tag_config("done", background="#81c784")
        except tk.TclError:
            pass

    def on_select(self, event=None):   # ← FIXED HERE
        d = self.calendar.get_date()
        self.listbox.delete(0, tk.END)
        found = False
        for t in self.controller.get_all_tasks():
            if t.due_date == d:
                found = True
                self.listbox.insert(
                    tk.END,
                    f"{t.title} — {t.category} — {t.priority} — {t.completion_status}"
                )
        if not found:
            self.listbox.insert(tk.END, "No tasks on this date.")

# Progress View(Plant Growth)
class ProgressView(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
    # Window
        self.title("Plantivity ~ Progress")
        self.geometry("700x400")
        self.controller = controller

        #Stages attributes initialized here
        self.stages = []
        self.bg_img = None

        # Home button
        home_frame = tk.Frame(self)
        home_frame.pack(anchor="w", padx=10, pady=5)
        tk.Button(home_frame, text="Home", command=self.destroy).pack()

        self.canvas = tk.Canvas(self, width=680, height=300, bg="white")
        self.canvas.pack()
        tk.Button(self, text="Refresh", command=self.refresh).pack(pady=10)

        self.load_images()
        self.refresh()

    # Load plant stage images & background
    def load_images(self):
        def load_stage(path):
            try:
                img = Image.open(path).resize((110, 110))
                return ImageTk.PhotoImage(img)
            except (FileNotFoundError, OSError):
                return None

    # Plant growth stages
        self.stages = [
            load_stage("sprout.png"),
            load_stage("seedling.png"),
            load_stage("budding.png"),
            load_stage("flower.png")
        ]
        # Dirt Background image
        try:
            bg = Image.open("dirt.png").resize((680, 300))
            self.bg_img = ImageTk.PhotoImage(bg)
        except (FileNotFoundError, OSError):
            self.bg_img = None

    # Calculate which stage flower is in
    def calculate_stage(self):
        completed = len(self.controller.get_completed_tasks())
        if completed == 0:
            return -1, 0

        # Each 4 completed tasks = 1 flower
        stage_index = (completed - 1) % 4
        full_flowers = (completed - 1) // 4
        return stage_index, full_flowers

    def refresh(self):
        self.canvas.delete("all")
        canvas_height = 300
        canvas_width = 680
        if self.bg_img:
            self.canvas.create_image(0, 0, image=self.bg_img, anchor="nw")
        stage_index, full_flowers = self.calculate_stage()

        # Show message if no tasks are complete
        if stage_index == -1:
            self.canvas.create_text(
                canvas_width // 2, canvas_height // 2,
                text="Complete your first task to grow your plant!",
                font=("Arial", 14),
                fill="white"
            )
            return

        # Plant placement
        x_start = 80
        spacing = 130
        y_pos = canvas_height - 90
        # Draw full flowers
        for i in range(full_flowers):
            if self.stages[-1]:
                self.canvas.create_image(x_start + i * spacing, y_pos, image=self.stages[-1])
        # Draw current stage of plant
        cur_img = self.stages[stage_index]
        if cur_img:
            self.canvas.create_image(x_start + full_flowers * spacing, y_pos, image=cur_img)


# Main Dashboard
class MainDashboard:
    def __init__(self,root):
        self.root = root
        self.root.title("Plantivity")
        self.root.geometry("900x600")
        self.root.configure(bg="white")
        self.controller = TaskController()

        # Background image
        self.bg_canvas = tk.Canvas(self.root, width=900, height=600, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0)
        try:
            self.bg_img_raw = Image.open("bg.png").resize((900, 600))
            self.bg_img = ImageTk.PhotoImage(self.bg_img_raw)
            self.bg_canvas.create_image(0, 0, image=self.bg_img, anchor="nw")
            self.bg_canvas.lower("all")
        except (FileNotFoundError, OSError):
            pass

        self.create_header()
        self.create_cards()

    def create_header(self):
        tk.Label(
            self.root, text="Welcome to Plantivity!",
            font=("Helvetica", 26, "bold"), bg="#F8F8F8"
        ).pack(pady=60)
        tk.Label(
            self.root, text="Your personal productivity assistant",
            font=("Helvetica", 16), bg="#F8F8F8"
        ).pack(pady=5)

    def create_cards(self):
        button_frame = tk.Frame(self.root, bg="#F8F8F8")
        button_frame.pack(pady=20)

        style = ttk.Style()
        style.configure(
            "Rounded.TButton",
            font=("Helvetica", 16, "bold"),
            padding=12
        )

        def on_enter(e):
            e.widget.configure(style="Hover.TButton")
        def on_leave(e):
            e.widget.configure(style="Rounded.TButton")

        style.configure(
            "Hover.TButton",
            font=("Helvetica", 16, "bold"),
            padding=12,
            background="#e8ffe8"
        )

        def make_btn(text, command):
            btn = ttk.Button(
                button_frame,
                text=text,
                command=command,
                style="Rounded.TButton",
                width=16
            )
            btn.pack(pady=8, ipady=5)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            return btn

        make_btn("Task Tracker", self.open_task_dashboard)
        make_btn("Calendar View", self.open_calendar)
        make_btn("Progress Tracker", self.open_progress)

    def open_task_dashboard(self):
        Dashboard(self.root)

    def open_calendar(self):
        CalendarView(self.root, self.controller)

    def open_progress(self):
        ProgressView(self.root, self.controller)


# Task Dashboard + Filtering
class Dashboard:
    def __init__(self, parent):
        self.root = tk.Toplevel(parent)
        self.root.title("Plantivity Dashboard")
        self.root.geometry("1000x650")
        self.controller = TaskController()

        # Stage attributes initialized
        self.next_label = None
        self.progress_label = None
        self.tree = None

        # Filters for category, priority and status
        self.filter_category = tk.StringVar(value="All")
        self.filter_priority = tk.StringVar(value="All")
        self.filter_status = tk.StringVar(value="All")

        self.create_home_button()
        self.create_header()
        self.create_filter()
        self.create_tree()
        self.create_buttons()
        self.refresh()

    def create_home_button(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10, anchor="w", padx=10)
        tk.Button(frame, text="Home", command=self.root.destroy, width=10).pack()

    def create_header(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="x", pady=10)
        self.next_label = tk.Label(frame, text="Next Task: None", font=("Arial", 14, "bold"))
        self.next_label.pack(side="left", padx=20)
        self.progress_label = tk.Label(frame, text="Progress: 0%", font=("Arial", 14))
        self.progress_label.pack(side="right", padx=20)


    # Filter Dropdowns + Clear Button

    def create_filter(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=20, pady=5)

        tk.Label(frame, text="Category:").pack(side="left", padx=(0, 5))
        cat_options = ["All"] + category_options
        cat_menu = ttk.Combobox(frame, values=cat_options, textvariable=self.filter_category, width=15)
        cat_menu.pack(side="left", padx=(0, 15))
        cat_menu.bind("<<ComboboxSelected>>", lambda e=None: self.refresh())

        tk.Label(frame, text="Priority:").pack(side="left", padx=(0, 5))
        pri_options = ["All"] + priority_options
        pri_menu = ttk.Combobox(frame, values=pri_options, textvariable=self.filter_priority, width=15)
        pri_menu.pack(side="left", padx=(0, 15))
        pri_menu.bind("<<ComboboxSelected>>", lambda e=None: self.refresh())

        tk.Label(frame, text="Status:").pack(side="left", padx=(0, 5))
        status_options = ["All"] + completion_options
        status_menu = ttk.Combobox(frame, values=status_options, textvariable=self.filter_status, width=15)
        status_menu.pack(side="left", padx=(0, 15))
        status_menu.bind("<<ComboboxSelected>>", lambda e=None: self.refresh())

        clear_btn = tk.Button(frame, text="Clear Filters", command=self.clear_filters, width=12)
        clear_btn.pack(side="left", padx=(10, 0))

    # Tree and Buttons
    def create_tree(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=20)
        cols = ("Title", "Description", "Category", "Due Date", "Priority", "Status")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150)
        self.tree.pack(fill="both", expand=True)

    def create_buttons(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)
        tk.Button(frame, text="Add Task", width=15, command=self.add).grid(row=0, column=0, padx=10)
        tk.Button(frame, text="Edit Task", width=15, command=self.edit).grid(row=0, column=1, padx=10)
        tk.Button(frame, text="Delete Task", width=15, command=self.delete).grid(row=0, column=2, padx=10)
        tk.Button(frame, text="Calendar", width=15, command=self.open_calendar).grid(row=0, column=3, padx=10)
        tk.Button(frame, text="Progress", width=15, command=self.open_progress).grid(row=0, column=4, padx=10)

    # Refresh Tree with Filters
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for t in self.controller.get_all_tasks():
            # Apply filters
            if self.filter_category.get() != "All" and t.category != self.filter_category.get():
                continue
            if self.filter_priority.get() != "All" and t.priority != self.filter_priority.get():
                continue
            if self.filter_status.get() != "All" and t.completion_status != self.filter_status.get():
                continue
            self.tree.insert("", "end", values=(t.title, t.description, t.category, t.due_date, t.priority, t.completion_status))
        nxt = self.controller.get_next_task()
        self.next_label.config(text=f"Next Task: {nxt.title}" if nxt else "Next Task: None")
        pct = self.controller.get_completion_percentage()
        self.progress_label.config(text=f"Progress: {pct}%")

    def clear_filters(self):
        self.filter_category.set("All")
        self.filter_priority.set("All")
        self.filter_status.set("All")
        self.refresh()

    def get_selected_title(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0])["values"][0]

    def add(self):
        TaskPopup(self, mode="add")

    def edit(self):
        title = self.get_selected_title()
        if not title:
            messagebox.showwarning("Select task", "Please select a task to edit.")
            return
        for t in self.controller.get_all_tasks():
            if t.title == title:
                TaskPopup(self, mode="edit", task_obj=t)
                return

    def delete(self):
        title = self.get_selected_title()
        if not title:
            messagebox.showwarning("Delete Task", "Select a task first.")
            return
        if messagebox.askyesno("Delete", f"Delete '{title}'?"):
            self.controller.delete_task(title)
            self.refresh()

    def open_calendar(self):
        CalendarView(self.root, self.controller)

    def open_progress(self):
        ProgressView(self.root, self.controller)

# Task Popup
class TaskPopup:
    def __init__(self, dashboard, mode, task_obj=None):
        self.dashboard = dashboard
        self.controller = dashboard.controller
        self.mode = mode
        self.task_obj = task_obj
        self.win = tk.Toplevel()
        self.win.title("Add Task" if mode=="add" else "Edit Task")
        self.win.geometry("400x450")

        tk.Label(self.win, text="Title").pack()
        self.title_entry = tk.Entry(self.win, width=40)
        self.title_entry.pack()

        tk.Label(self.win, text="Description").pack()
        self.desc_entry = tk.Entry(self.win, width=40)
        self.desc_entry.pack()

        tk.Label(self.win, text="Category").pack()
        self.cat_box = ttk.Combobox(self.win, values=category_options)
        self.cat_box.pack()

        tk.Label(self.win, text="Due Date").pack()
        self.date_entry = DateEntry(self.win, date_pattern="yyyy-mm-dd")
        self.date_entry.pack()

        tk.Label(self.win, text="Priority").pack()
        self.pri_box = ttk.Combobox(self.win, values=priority_options)
        self.pri_box.pack()

        tk.Label(self.win, text="Status").pack()
        self.status_box = ttk.Combobox(self.win, values=completion_options)
        self.status_box.pack()

        tk.Button(self.win, text="Save", command=self.save).pack(pady=20)

        if mode=="edit":
            self.load()

    def load(self):
        t = self.task_obj
        self.title_entry.insert(0, t.title)
        self.desc_entry.insert(0, t.description)
        self.cat_box.set(t.category)
        self.date_entry.set_date(t.due_date)
        self.pri_box.set(t.priority)
        self.status_box.set(t.completion_status)

    def save(self):
        new = Task(
            title=self.title_entry.get(),
            description=self.desc_entry.get(),
            category=self.cat_box.get(),
            due_date=self.date_entry.get(),
            priority=self.pri_box.get(),
            completion_status=self.status_box.get()
        )
        if self.mode=="add":
            self.controller.add_task(new)
        else:
            self.controller.update_task(self.task_obj, new)
        self.dashboard.refresh()
        self.win.destroy()


# Run Tracker
if __name__ == "__main__":
    root = tk.Tk()
    MainDashboard(root)
    root.mainloop()
