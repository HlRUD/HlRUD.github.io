import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import json
import os
import webbrowser
import html
import base64


class WebsiteBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("WebCraft Website Builder v2")
        self.root.geometry("1250x750")
        self.root.minsize(850, 550)

        self.project_file = None
        self.elements = []
        self.selected_id = None
        self.drag_data = None
        self.zoom = 1.0
        self.element_counter = 0

        self.page_settings = {
            "title": "My Website",
            "background": "#ffffff",
            "width": 900,
            "height": 600
        }

        self.setup_style()
        self.build_ui()
        self.bind_shortcuts()
        self.draw_canvas()

    # =========================================================
    # STYLE
    # =========================================================

    def setup_style(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except:
            pass

        style.configure(
            "Toolbar.TButton",
            padding=(10, 6),
            font=("Segoe UI", 9)
        )

        style.configure(
            "Panel.TLabel",
            font=("Segoe UI", 9)
        )

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 11, "bold")
        )

        style.configure(
            "Small.TLabel",
            font=("Segoe UI", 8)
        )

    # =========================================================
    # MAIN UI
    # =========================================================

    def build_ui(self):

        # ---------------- TOOLBAR ----------------

        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill="x", padx=6, pady=6)

        ttk.Button(
            toolbar,
            text="New",
            style="Toolbar.TButton",
            command=self.new_project
        ).pack(side="left", padx=2)

        ttk.Button(
            toolbar,
            text="Open",
            style="Toolbar.TButton",
            command=self.open_project
        ).pack(side="left", padx=2)

        ttk.Button(
            toolbar,
            text="Save",
            style="Toolbar.TButton",
            command=self.save_project
        ).pack(side="left", padx=2)

        ttk.Button(
            toolbar,
            text="Preview",
            style="Toolbar.TButton",
            command=self.preview
        ).pack(side="left", padx=2)

        ttk.Button(
            toolbar,
            text="Export HTML",
            style="Toolbar.TButton",
            command=self.export_html
        ).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(
            side="left",
            fill="y",
            padx=8
        )

        ttk.Label(
            toolbar,
            text="Zoom:"
        ).pack(side="left")

        self.zoom_var = tk.StringVar(value="100%")

        zoom_combo = ttk.Combobox(
            toolbar,
            textvariable=self.zoom_var,
            values=["50%", "75%", "100%", "125%", "150%"],
            width=7,
            state="readonly"
        )
        zoom_combo.pack(side="left", padx=4)
        zoom_combo.bind("<<ComboboxSelected>>", self.change_zoom)

        self.status_var = tk.StringVar(value="Ready")

        ttk.Label(
            toolbar,
            textvariable=self.status_var
        ).pack(side="right", padx=8)

        # ---------------- MAIN AREA ----------------

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=0)
        main.rowconfigure(0, weight=1)

        # LEFT
        self.build_left_panel(main)

        # CENTER
        self.build_center_panel(main)

        # RIGHT
        self.build_right_panel(main)

        # ---------------- STATUS BAR ----------------

        status = ttk.Frame(self.root)
        status.pack(fill="x", padx=6, pady=(0, 4))

        ttk.Label(
            status,
            text="WebCraft v2"
        ).pack(side="left")

        ttk.Label(
            status,
            text="Ctrl+S Save  |  Ctrl+O Open  |  Ctrl+N New  |  Delete Remove"
        ).pack(side="right")

    # =========================================================
    # LEFT PANEL
    # =========================================================

    def build_left_panel(self, parent):

        frame = ttk.LabelFrame(
            parent,
            text=" Components "
        )
        frame.grid(
            row=0,
            column=0,
            sticky="ns",
            padx=(0, 6)
        )

        frame.configure(width=190)
        frame.grid_propagate(False)

        canvas = tk.Canvas(
            frame,
            width=170,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=canvas.yview
        )

        inner = ttk.Frame(canvas)

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window(
            (0, 0),
            window=inner,
            anchor="nw",
            width=170
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        components = [
            ("Text", "text"),
            ("Heading", "heading"),
            ("Link", "link"),
            ("Button", "button"),
            ("Input", "input"),
            ("Image", "image"),
            ("Divider", "divider"),
            ("Container", "container")
        ]

        for name, kind in components:

            btn = ttk.Button(
                inner,
                text=name,
                command=lambda k=kind: self.add_element(k)
            )

            btn.pack(
                fill="x",
                padx=10,
                pady=5
            )

        ttk.Separator(inner).pack(
            fill="x",
            padx=10,
            pady=12
        )

        ttk.Label(
            inner,
            text="Add an element\nthen drag it on canvas.",
            justify="center",
            style="Small.TLabel"
        ).pack(
            pady=10
        )

    # =========================================================
    # CENTER PANEL
    # =========================================================

    def build_center_panel(self, parent):

        frame = ttk.LabelFrame(
            parent,
            text=" Canvas "
        )

        frame.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            frame,
            background="#dcdcdc",
            highlightthickness=0
        )

        vbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.canvas.yview
        )

        hbar = ttk.Scrollbar(
            frame,
            orient="horizontal",
            command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=vbar.set,
            xscrollcommand=hbar.set
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        vbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        hbar.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        self.canvas.bind(
            "<Button-1>",
            self.canvas_click
        )

        self.canvas.bind(
            "<B1-Motion>",
            self.canvas_drag
        )

        self.canvas.bind(
            "<ButtonRelease-1>",
            self.canvas_release
        )

    # =========================================================
    # RIGHT PANEL
    # =========================================================

    def build_right_panel(self, parent):

        frame = ttk.LabelFrame(
            parent,
            text=" Settings "
        )

        frame.grid(
            row=0,
            column=2,
            sticky="ns",
            padx=(6, 0)
        )

        frame.configure(width=270)
        frame.grid_propagate(False)

        # Outer scroll area

        canvas = tk.Canvas(
            frame,
            width=250,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=canvas.yview
        )

        inner = ttk.Frame(canvas)

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window(
            (0, 0),
            window=inner,
            anchor="nw",
            width=250
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.settings_inner = inner

        # =====================================================
        # WEBSITE SETTINGS - TOP
        # =====================================================

        website_box = ttk.LabelFrame(
            inner,
            text=" Website Settings "
        )

        website_box.pack(
            fill="x",
            padx=8,
            pady=8
        )

        ttk.Label(
            website_box,
            text="Website title:"
        ).pack(
            anchor="w",
            padx=8,
            pady=(8, 2)
        )

        self.title_entry = ttk.Entry(
            website_box
        )

        self.title_entry.pack(
            fill="x",
            padx=8
        )

        self.title_entry.insert(
            0,
            self.page_settings["title"]
        )

        self.title_entry.bind(
            "<KeyRelease>",
            lambda e: self.update_page_setting()
        )

        ttk.Label(
            website_box,
            text="Background:"
        ).pack(
            anchor="w",
            padx=8,
            pady=(10, 2)
        )

        bg_frame = ttk.Frame(website_box)
        bg_frame.pack(
            fill="x",
            padx=8
        )

        self.bg_entry = ttk.Entry(
            bg_frame
        )

        self.bg_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        self.bg_entry.insert(
            0,
            self.page_settings["background"]
        )

        ttk.Button(
            bg_frame,
            text="Choose",
            command=self.choose_background
        ).pack(
            side="right",
            padx=(5, 0)
        )

        ttk.Label(
            website_box,
            text="Page width:"
        ).pack(
            anchor="w",
            padx=8,
            pady=(10, 2)
        )

        self.width_entry = ttk.Entry(
            website_box
        )

        self.width_entry.pack(
            fill="x",
            padx=8
        )

        self.width_entry.insert(
            0,
            str(self.page_settings["width"])
        )

        self.width_entry.bind(
            "<KeyRelease>",
            lambda e: self.update_page_setting()
        )

        ttk.Label(
            website_box,
            text="Page height:"
        ).pack(
            anchor="w",
            padx=8,
            pady=(10, 2)
        )

        self.height_entry = ttk.Entry(
            website_box
        )

        self.height_entry.pack(
            fill="x",
            padx=8
        )

        self.height_entry.insert(
            0,
            str(self.page_settings["height"])
        )

        self.height_entry.bind(
            "<KeyRelease>",
            lambda e: self.update_page_setting()
        )

        ttk.Button(
            website_box,
            text="Apply Website Settings",
            command=self.update_page_setting
        ).pack(
            fill="x",
            padx=8,
            pady=10
        )

        # =====================================================
        # SELECTED ELEMENT
        # =====================================================

        self.property_box = ttk.LabelFrame(
            inner,
            text=" Selected Element "
        )

        self.property_box.pack(
            fill="x",
            padx=8,
            pady=8
        )

        self.build_empty_properties()

    # =========================================================
    # EMPTY PROPERTIES
    # =========================================================

    def build_empty_properties(self):

        for widget in self.property_box.winfo_children():
            widget.destroy()

        ttk.Label(
            self.property_box,
            text="Select an element\nfrom the canvas.",
            justify="center"
        ).pack(
            padx=10,
            pady=25
        )

    # =========================================================
    # PROPERTIES
    # =========================================================

    def show_properties(self):

        for widget in self.property_box.winfo_children():
            widget.destroy()

        element = self.get_selected()

        if not element:
            self.build_empty_properties()
            return

        ttk.Label(
            self.property_box,
            text=f"Type: {element['type']}"
        ).pack(
            anchor="w",
            padx=8,
            pady=6
        )

        if element["type"] in (
            "text",
            "heading",
            "link",
            "button",
            "input"
        ):

            ttk.Label(
                self.property_box,
                text="Text:"
            ).pack(
                anchor="w",
                padx=8
            )

            self.text_entry = ttk.Entry(
                self.property_box
            )

            self.text_entry.pack(
                fill="x",
                padx=8,
                pady=4
            )

            self.text_entry.insert(
                0,
                element.get("text", "")
            )

            self.text_entry.bind(
                "<KeyRelease>",
                lambda e: self.update_element_property()
            )

        if element["type"] == "link":

            ttk.Label(
                self.property_box,
                text="URL:"
            ).pack(
                anchor="w",
                padx=8,
                pady=(8, 0)
            )

            self.url_entry = ttk.Entry(
                self.property_box
            )

            self.url_entry.pack(
                fill="x",
                padx=8,
                pady=4
            )

            self.url_entry.insert(
                0,
                element.get("url", "https://example.com")
            )

            self.url_entry.bind(
                "<KeyRelease>",
                lambda e: self.update_element_property()
            )

        ttk.Label(
            self.property_box,
            text="Font size:"
        ).pack(
            anchor="w",
            padx=8,
            pady=(8, 0)
        )

        self.font_entry = ttk.Entry(
            self.property_box
        )

        self.font_entry.pack(
            fill="x",
            padx=8
        )

        self.font_entry.insert(
            0,
            str(element.get("font_size", 16))
        )

        self.font_entry.bind(
            "<KeyRelease>",
            lambda e: self.update_element_property()
        )

        ttk.Label(
            self.property_box,
            text="Text color:"
        ).pack(
            anchor="w",
            padx=8,
            pady=(8, 0)
        )

        color_frame = ttk.Frame(
            self.property_box
        )

        color_frame.pack(
            fill="x",
            padx=8,
            pady=4
        )

        self.color_entry = ttk.Entry(
            color_frame
        )

        self.color_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        self.color_entry.insert(
            0,
            element.get("color", "#000000")
        )

        ttk.Button(
            color_frame,
            text="Choose",
            command=self.choose_text_color
        ).pack(
            side="right",
            padx=(5, 0)
        )

        ttk.Label(
            self.property_box,
            text="X:"
        ).pack(
            anchor="w",
            padx=8,
            pady=(8, 0)
        )

        self.x_entry = ttk.Entry(
            self.property_box
        )

        self.x_entry.pack(
            fill="x",
            padx=8
        )

        self.x_entry.insert(
            0,
            str(element["x"])
        )

        ttk.Label(
            self.property_box,
            text="Y:"
        ).pack(
            anchor="w",
            padx=8,
            pady=(8, 0)
        )

        self.y_entry = ttk.Entry(
            self.property_box
        )

        self.y_entry.pack(
            fill="x",
            padx=8
        )

        self.y_entry.insert(
            0,
            str(element["y"])
        )

        ttk.Button(
            self.property_box,
            text="Apply",
            command=self.update_element_property
        ).pack(
            fill="x",
            padx=8,
            pady=10
        )

        ttk.Button(
            self.property_box,
            text="Delete Element",
            command=self.delete_selected
        ).pack(
            fill="x",
            padx=8,
            pady=(0, 10)
        )

    # =========================================================
    # ADD ELEMENT
    # =========================================================

    def add_element(self, kind):

        self.element_counter += 1

        default_text = {
            "text": "Text",
            "heading": "Heading",
            "link": "Click here",
            "button": "Button",
            "input": "Enter text",
            "image": "Image",
            "divider": "",
            "container": "Container"
        }

        element = {
            "id": self.element_counter,
            "type": kind,
            "x": 80,
            "y": 80 + (len(self.elements) * 45),
            "width": 180,
            "height": 45,
            "text": default_text[kind],
            "font_size": 16,
            "color": "#000000"
        }

        if kind == "heading":
            element["font_size"] = 28
            element["height"] = 60

        elif kind == "button":
            element["width"] = 140
            element["height"] = 45

        elif kind == "input":
            element["width"] = 220
            element["height"] = 38

        elif kind == "image":
            element["width"] = 200
            element["height"] = 130
            element["path"] = ""

        elif kind == "divider":
            element["width"] = 400
            element["height"] = 5

        elif kind == "container":
            element["width"] = 400
            element["height"] = 200

        elif kind == "link":
            element["url"] = "https://example.com"

        self.elements.append(element)

        self.selected_id = element["id"]

        self.show_properties()
        self.draw_canvas()

        self.status_var.set(
            f"Added {kind}"
        )

    # =========================================================
    # CANVAS DRAW
    # =========================================================

    def draw_canvas(self):

        self.canvas.delete("all")

        width = int(
            self.page_settings["width"] * self.zoom
        )

        height = int(
            self.page_settings["height"] * self.zoom
        )

        # Page shadow
        self.canvas.create_rectangle(
            25,
            25,
            25 + width + 8,
            25 + height + 8,
            fill="#aaaaaa",
            outline=""
        )

        # Page
        self.canvas.create_rectangle(
            25,
            25,
            25 + width,
            25 + height,
            fill=self.page_settings["background"],
            outline="#888888"
        )

        for element in self.elements:
            self.draw_element(element)

        self.canvas.configure(
            scrollregion=(
                0,
                0,
                width + 80,
                height + 80
            )
        )

    # =========================================================
    # DRAW ELEMENT
    # =========================================================

    def draw_element(self, element):

        scale = self.zoom

        x = 25 + element["x"] * scale
        y = 25 + element["y"] * scale

        w = element["width"] * scale
        h = element["height"] * scale

        selected = (
            element["id"] == self.selected_id
        )

        outline = "#0078d7" if selected else "#888888"

        kind = element["type"]

        if kind == "text":

            self.canvas.create_text(
                x,
                y,
                anchor="nw",
                text=element["text"],
                fill=element["color"],
                font=("Arial", int(element["font_size"] * scale)),
                tags=("element", str(element["id"]))
            )

        elif kind == "heading":

            self.canvas.create_text(
                x,
                y,
                anchor="nw",
                text=element["text"],
                fill=element["color"],
                font=(
                    "Arial",
                    int(element["font_size"] * scale),
                    "bold"
                ),
                tags=("element", str(element["id"]))
            )

        elif kind == "link":

            self.canvas.create_text(
                x,
                y,
                anchor="nw",
                text=element["text"],
                fill="#0066cc",
                font=(
                    "Arial",
                    int(element["font_size"] * scale),
                    "underline"
                ),
                tags=("element", str(element["id"]))
            )

        elif kind == "button":

            self.canvas.create_rectangle(
                x,
                y,
                x + w,
                y + h,
                fill="#0078d7",
                outline=outline,
                width=2,
                tags=("element", str(element["id"]))
            )

            self.canvas.create_text(
                x + w / 2,
                y + h / 2,
                text=element["text"],
                fill="white",
                font=(
                    "Arial",
                    int(element["font_size"] * scale)
                ),
                tags=("element", str(element["id"]))
            )

        elif kind == "input":

            self.canvas.create_rectangle(
                x,
                y,
                x + w,
                y + h,
                fill="white",
                outline=outline,
                width=2,
                tags=("element", str(element["id"]))
            )

            self.canvas.create_text(
                x + 8,
                y + h / 2,
                anchor="w",
                text=element["text"],
                fill="#777777",
                font=(
                    "Arial",
                    int(element["font_size"] * scale)
                ),
                tags=("element", str(element["id"]))
            )

        elif kind == "image":

            path = element.get("path", "")

            if path and os.path.exists(path):

                try:
                    img = tk.PhotoImage(file=path)

                    element["_photo"] = img

                    self.canvas.create_image(
                        x,
                        y,
                        anchor="nw",
                        image=img,
                        tags=("element", str(element["id"]))
                    )

                except:
                    self.draw_image_placeholder(
                        element,
                        x,
                        y,
                        w,
                        h,
                        outline
                    )

            else:

                self.draw_image_placeholder(
                    element,
                    x,
                    y,
                    w,
                    h,
                    outline
                )

        elif kind == "divider":

            self.canvas.create_line(
                x,
                y + h / 2,
                x + w,
                y + h / 2,
                fill="#555555",
                width=2,
                tags=("element", str(element["id"]))
            )

        elif kind == "container":

            self.canvas.create_rectangle(
                x,
                y,
                x + w,
                y + h,
                outline=outline,
                dash=(5, 3),
                width=2,
                tags=("element", str(element["id"]))
            )

            self.canvas.create_text(
                x + 8,
                y + 8,
                anchor="nw",
                text="Container",
                fill="#888888",
                font=("Arial", 10),
                tags=("element", str(element["id"]))
            )

    # =========================================================
    # IMAGE PLACEHOLDER
    # =========================================================

    def draw_image_placeholder(
        self,
        element,
        x,
        y,
        w,
        h,
        outline
    ):

        self.canvas.create_rectangle(
            x,
            y,
            x + w,
            y + h,
            fill="#eeeeee",
            outline=outline,
            width=2,
            tags=("element", str(element["id"]))
        )

        self.canvas.create_text(
            x + w / 2,
            y + h / 2,
            text="IMAGE\nDouble-click",
            justify="center",
            fill="#777777",
            font=("Arial", 12),
            tags=("element", str(element["id"]))
        )

    # =========================================================
    # CANVAS CLICK
    # =========================================================

    def canvas_click(self, event):

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        page_x = 25
        page_y = 25

        real_x = (x - page_x) / self.zoom
        real_y = (y - page_y) / self.zoom

        selected = None

        for element in reversed(self.elements):

            ex = element["x"]
            ey = element["y"]
            ew = element["width"]
            eh = element["height"]

            if (
                ex <= real_x <= ex + ew
                and
                ey <= real_y <= ey + eh
            ):
                selected = element
                break

        if selected:

            self.selected_id = selected["id"]

            self.drag_data = {
                "id": selected["id"],
                "start_x": real_x,
                "start_y": real_y,
                "orig_x": selected["x"],
                "orig_y": selected["y"]
            }

            self.show_properties()
            self.draw_canvas()

        else:

            self.selected_id = None
            self.drag_data = None

            self.build_empty_properties()
            self.draw_canvas()

    # =========================================================
    # DRAG
    # =========================================================

    def canvas_drag(self, event):

        if not self.drag_data:
            return

        element = self.get_selected()

        if not element:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        real_x = (x - 25) / self.zoom
        real_y = (y - 25) / self.zoom

        dx = real_x - self.drag_data["start_x"]
        dy = real_y - self.drag_data["start_y"]

        element["x"] = max(
            0,
            int(self.drag_data["orig_x"] + dx)
        )

        element["y"] = max(
            0,
            int(self.drag_data["orig_y"] + dy)
        )

        self.draw_canvas()

    def canvas_release(self, event):

        self.drag_data = None

        element = self.get_selected()

        if element:
            self.update_property_entries()

    # =========================================================
    # PROPERTY UPDATE
    # =========================================================

    def update_element_property(self):

        element = self.get_selected()

        if not element:
            return

        if hasattr(self, "text_entry"):
            element["text"] = self.text_entry.get()

        if hasattr(self, "url_entry"):
            element["url"] = self.url_entry.get()

        if hasattr(self, "font_entry"):
            try:
                element["font_size"] = max(
                    6,
                    int(self.font_entry.get())
                )
            except:
                pass

        if hasattr(self, "color_entry"):
            element["color"] = self.color_entry.get()

        if hasattr(self, "x_entry"):
            try:
                element["x"] = max(
                    0,
                    int(self.x_entry.get())
                )
            except:
                pass

        if hasattr(self, "y_entry"):
            try:
                element["y"] = max(
                    0,
                    int(self.y_entry.get())
                )
            except:
                pass

        self.draw_canvas()

    def update_property_entries(self):

        element = self.get_selected()

        if not element:
            return

        if hasattr(self, "x_entry"):
            self.x_entry.delete(0, "end")
            self.x_entry.insert(0, str(element["x"]))

        if hasattr(self, "y_entry"):
            self.y_entry.delete(0, "end")
            self.y_entry.insert(0, str(element["y"]))

    # =========================================================
    # PAGE SETTINGS
    # =========================================================

    def update_page_setting(self):

        self.page_settings["title"] = (
            self.title_entry.get()
        )

        self.page_settings["background"] = (
            self.bg_entry.get()
        )

        try:
            self.page_settings["width"] = max(
                300,
                int(self.width_entry.get())
            )
        except:
            pass

        try:
            self.page_settings["height"] = max(
                300,
                int(self.height_entry.get())
            )
        except:
            pass

        self.draw_canvas()

        self.status_var.set(
            "Website settings updated"
        )

    # =========================================================
    # COLOR
    # =========================================================

    def choose_background(self):

        color = colorchooser.askcolor(
            title="Choose background"
        )

        if color[1]:

            self.bg_entry.delete(0, "end")
            self.bg_entry.insert(0, color[1])

            self.update_page_setting()

    def choose_text_color(self):

        color = colorchooser.askcolor(
            title="Choose text color"
        )

        if color[1]:

            self.color_entry.delete(0, "end")
            self.color_entry.insert(0, color[1])

            self.update_element_property()

    # =========================================================
    # IMAGE
    # =========================================================

    def choose_image(self, element):

        path = filedialog.askopenfilename(
            title="Choose image",
            filetypes=[
                (
                    "Images",
                    "*.png *.gif *.ppm *.pgm"
                )
            ]
        )

        if path:

            element["path"] = path
            self.draw_canvas()

    # =========================================================
    # SELECTED ELEMENT
    # =========================================================

    def get_selected(self):

        for element in self.elements:

            if element["id"] == self.selected_id:
                return element

        return None

    # =========================================================
    # DELETE
    # =========================================================

    def delete_selected(self):

        element = self.get_selected()

        if not element:
            return

        self.elements = [
            e for e in self.elements
            if e["id"] != self.selected_id
        ]

        self.selected_id = None

        self.build_empty_properties()
        self.draw_canvas()

        self.status_var.set(
            "Element deleted"
        )

    # =========================================================
    # NEW PROJECT
    # =========================================================

    def new_project(self):

        answer = messagebox.askyesno(
            "New Project",
            "Create a new project?"
        )

        if not answer:
            return

        self.elements = []
        self.selected_id = None
        self.project_file = None
        self.element_counter = 0

        self.page_settings = {
            "title": "My Website",
            "background": "#ffffff",
            "width": 900,
            "height": 600
        }

        self.title_entry.delete(0, "end")
        self.title_entry.insert(
            0,
            "My Website"
        )

        self.bg_entry.delete(0, "end")
        self.bg_entry.insert(
            0,
            "#ffffff"
        )

        self.width_entry.delete(0, "end")
        self.width_entry.insert(
            0,
            "900"
        )

        self.height_entry.delete(0, "end")
        self.height_entry.insert(
            0,
            "600"
        )

        self.build_empty_properties()
        self.draw_canvas()

        self.status_var.set(
            "New project"
        )

    # =========================================================
    # SAVE
    # =========================================================

    def save_project(self):

        if not self.project_file:

            self.project_file = filedialog.asksaveasfilename(
                defaultextension=".webcraft",
                filetypes=[
                    (
                        "WebCraft Project",
                        "*.webcraft"
                    ),
                    (
                        "JSON",
                        "*.json"
                    )
                ]
            )

        if not self.project_file:
            return

        data = {
            "version": 2,
            "settings": self.page_settings,
            "elements": self.clean_elements()
        }

        try:

            with open(
                self.project_file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            self.status_var.set(
                "Project saved"
            )

        except Exception as e:

            messagebox.showerror(
                "Save Error",
                str(e)
            )

    # =========================================================
    # CLEAN ELEMENTS
    # =========================================================

    def clean_elements(self):

        result = []

        for element in self.elements:

            item = {}

            for key, value in element.items():

                if key != "_photo":
                    item[key] = value

            result.append(item)

        return result

    # =========================================================
    # OPEN
    # =========================================================

    def open_project(self):

        path = filedialog.askopenfilename(
            filetypes=[
                (
                    "WebCraft Project",
                    "*.webcraft"
                ),
                (
                    "JSON",
                    "*.json"
                )
            ]
        )

        if not path:
            return

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            self.project_file = path

            self.page_settings = data.get(
                "settings",
                self.page_settings
            )

            self.elements = data.get(
                "elements",
                []
            )

            self.element_counter = 0

            for element in self.elements:

                self.element_counter = max(
                    self.element_counter,
                    int(element.get("id", 0))
                )

            self.selected_id = None

            self.title_entry.delete(0, "end")
            self.title_entry.insert(
                0,
                self.page_settings["title"]
            )

            self.bg_entry.delete(0, "end")
            self.bg_entry.insert(
                0,
                self.page_settings["background"]
            )

            self.width_entry.delete(0, "end")
            self.width_entry.insert(
                0,
                str(self.page_settings["width"])
            )

            self.height_entry.delete(0, "end")
            self.height_entry.insert(
                0,
                str(self.page_settings["height"])
            )

            self.build_empty_properties()
            self.draw_canvas()

            self.status_var.set(
                "Project opened"
            )

        except Exception as e:

            messagebox.showerror(
                "Open Error",
                str(e)
            )

    # =========================================================
    # HTML GENERATOR
    # =========================================================

    def generate_html(self):

        title = html.escape(
            self.page_settings["title"]
        )

        background = html.escape(
            self.page_settings["background"]
        )

        body = []

        for element in self.elements:

            kind = element["type"]

            x = element["x"]
            y = element["y"]

            width = element["width"]
            height = element["height"]

            font_size = element.get(
                "font_size",
                16
            )

            color = element.get(
                "color",
                "#000000"
            )

            text = html.escape(
                element.get("text", "")
            )

            style = (
                f"position:absolute;"
                f"left:{x}px;"
                f"top:{y}px;"
                f"width:{width}px;"
                f"height:{height}px;"
                f"font-size:{font_size}px;"
                f"color:{color};"
            )

            if kind == "text":

                body.append(
                    f'<div style="{style}">{text}</div>'
                )

            elif kind == "heading":

                body.append(
                    f'<h1 style="{style}">{text}</h1>'
                )

            elif kind == "link":

                url = html.escape(
                    element.get(
                        "url",
                        "#"
                    )
                )

                body.append(
                    f'<a href="{url}" '
                    f'style="{style}">'
                    f'{text}</a>'
                )

            elif kind == "button":

                body.append(
                    f'<button style="{style}">'
                    f'{text}'
                    f'</button>'
                )

            elif kind == "input":

                body.append(
                    f'<input '
                    f'placeholder="{text}" '
                    f'style="{style}">'
                )

            elif kind == "divider":

                body.append(
                    f'<hr style="'
                    f'position:absolute;'
                    f'left:{x}px;'
                    f'top:{y}px;'
                    f'width:{width}px;'
                    f'">'
                )

            elif kind == "container":

                body.append(
                    f'<div style="'
                    f'{style}'
                    f'border:1px dashed #888;'
                    f'box-sizing:border-box;'
                    f'">'
                    f'</div>'
                )

            elif kind == "image":

                path = element.get(
                    "path",
                    ""
                )

                if path and os.path.exists(path):

                    try:

                        with open(
                            path,
                            "rb"
                        ) as image_file:

                            encoded = base64.b64encode(
                                image_file.read()
                            ).decode("utf-8")

                        ext = os.path.splitext(
                            path
                        )[1].lower()

                        mime = {
                            ".png": "image/png",
                            ".jpg": "image/jpeg",
                            ".jpeg": "image/jpeg",
                            ".gif": "image/gif"
                        }.get(
                            ext,
                            "image/png"
                        )

                        src = (
                            f"data:{mime};base64,"
                            f"{encoded}"
                        )

                        body.append(
                            f'<img src="{src}" '
                            f'style="{style};'
                            f'object-fit:contain;">'
                        )

                    except:
                        pass

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">
<title>{title}</title>

<style>

* {{
    box-sizing: border-box;
}}

html, body {{
    margin: 0;
    padding: 0;
    background: #eeeeee;
}}

.website {{
    position: relative;
    width: {self.page_settings["width"]}px;
    height: {self.page_settings["height"]}px;
    margin: 30px auto;
    background: {background};
    overflow: hidden;
}}

button {{
    cursor: pointer;
}}

</style>

</head>

<body>

<div class="website">

{''.join(body)}

</div>

</body>
</html>
"""

    # =========================================================
    # EXPORT
    # =========================================================

    def export_html(self):

        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[
                (
                    "HTML",
                    "*.html"
                )
            ]
        )

        if not path:
            return

        try:

            content = self.generate_html()

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(content)

            messagebox.showinfo(
                "Export Complete",
                f"HTML exported successfully.\n\n{path}"
            )

            self.status_var.set(
                "HTML exported"
            )

        except Exception as e:

            messagebox.showerror(
                "Export Error",
                str(e)
            )

    # =========================================================
    # PREVIEW
    # =========================================================

    def preview(self):

        temp_file = os.path.join(
            os.path.abspath("."),
            "_webcraft_preview.html"
        )

        try:

            with open(
                temp_file,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    self.generate_html()
                )

            webbrowser.open(
                "file://" + temp_file
            )

            self.status_var.set(
                "Preview opened"
            )

        except Exception as e:

            messagebox.showerror(
                "Preview Error",
                str(e)
            )

    # =========================================================
    # ZOOM
    # =========================================================

    def change_zoom(self, event=None):

        value = self.zoom_var.get()

        try:

            self.zoom = int(
                value.replace("%", "")
            ) / 100

        except:
            self.zoom = 1.0

        self.draw_canvas()

    # =========================================================
    # SHORTCUTS
    # =========================================================

    def bind_shortcuts(self):

        self.root.bind(
            "<Control-s>",
            lambda e: self.save_project()
        )

        self.root.bind(
            "<Control-o>",
            lambda e: self.open_project()
        )

        self.root.bind(
            "<Control-n>",
            lambda e: self.new_project()
        )

        self.root.bind(
            "<Delete>",
            lambda e: self.delete_selected()
        )

        self.canvas.bind(
            "<Double-Button-1>",
            self.double_click_canvas
        )

    # =========================================================
    # DOUBLE CLICK
    # =========================================================

    def double_click_canvas(self, event):

        element = self.get_selected()

        if not element:
            return

        if element["type"] == "image":

            self.choose_image(element)
            return

        if element["type"] == "link":

            webbrowser.open(
                element.get(
                    "url",
                    "https://example.com"
                )
            )


# =============================================================
# START
# =============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = WebsiteBuilder(root)

    root.mainloop()