import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import json
import os
import webbrowser
import html
import base64
import requests
from urllib.parse import urlparse


class WebsiteBuilder:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "WebCraft Website Builder v2"
        )

        self.root.geometry(
            "1250x750"
        )

        self.root.minsize(
            850,
            550
        )

        self.project_file = None
        self.elements = []
        self.selected_id = None
        self.drag_data = None
        self.zoom = 1.0
        self.element_counter = 0

        self.github_token = ""
        self.github_repo_url = ""
        self.github_file_path = "main/pannel.html"
        self.github_branch = "main"

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

        toolbar = ttk.Frame(
            self.root
        )

        toolbar.pack(
            fill="x",
            padx=6,
            pady=6
        )

        ttk.Button(
            toolbar,
            text="New",
            style="Toolbar.TButton",
            command=self.new_project
        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(
            toolbar,
            text="Open",
            style="Toolbar.TButton",
            command=self.open_project
        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(
            toolbar,
            text="Save",
            style="Toolbar.TButton",
            command=self.save_project
        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(
            toolbar,
            text="Preview",
            style="Toolbar.TButton",
            command=self.preview
        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(
            toolbar,
            text="Export HTML",
            style="Toolbar.TButton",
            command=self.export_html
        ).pack(
            side="left",
            padx=2
        )

        ttk.Separator(
            toolbar,
            orient="vertical"
        ).pack(
            side="left",
            fill="y",
            padx=8
        )

        ttk.Button(
            toolbar,
            text="GitHub",
            style="Toolbar.TButton",
            command=self.github_window
        ).pack(
            side="left",
            padx=2
        )

        ttk.Label(
            toolbar,
            text="Zoom:"
        ).pack(
            side="left",
            padx=(12, 2)
        )

        self.zoom_var = tk.StringVar(
            value="100%"
        )

        zoom_combo = ttk.Combobox(
            toolbar,
            textvariable=self.zoom_var,
            values=[
                "50%",
                "75%",
                "100%",
                "125%",
                "150%"
            ],
            width=7,
            state="readonly"
        )

        zoom_combo.pack(
            side="left",
            padx=4
        )

        zoom_combo.bind(
            "<<ComboboxSelected>>",
            self.change_zoom
        )

        self.status_var = tk.StringVar(
            value="Ready"
        )

        ttk.Label(
            toolbar,
            textvariable=self.status_var
        ).pack(
            side="right",
            padx=8
        )

        main = ttk.Frame(
            self.root
        )

        main.pack(
            fill="both",
            expand=True,
            padx=6,
            pady=(0, 6)
        )

        main.columnconfigure(
            1,
            weight=1
        )

        main.rowconfigure(
            0,
            weight=1
        )

        self.build_left_panel(main)
        self.build_center_panel(main)
        self.build_right_panel(main)

        status = ttk.Frame(
            self.root
        )

        status.pack(
            fill="x",
            padx=6,
            pady=(0, 4)
        )

        ttk.Label(
            status,
            text="WebCraft v2"
        ).pack(
            side="left"
        )

        ttk.Label(
            status,
            text="Ctrl+S Save | Ctrl+O Open | Ctrl+N New | Delete Remove"
        ).pack(
            side="right"
        )

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

        frame.configure(
            width=190
        )

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

        inner = ttk.Frame(
            canvas
        )

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

            ttk.Button(
                inner,
                text=name,
                command=lambda k=kind:
                self.add_element(k)
            ).pack(
                fill="x",
                padx=10,
                pady=5
            )

        ttk.Separator(
            inner
        ).pack(
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

        frame.rowconfigure(
            0,
            weight=1
        )

        frame.columnconfigure(
            0,
            weight=1
        )

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

        frame.configure(
            width=270
        )

        frame.grid_propagate(False)

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

        inner = ttk.Frame(
            canvas
        )

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

        ttk.Label(
            website_box,
            text="Background:"
        ).pack(
            anchor="w",
            padx=8,
            pady=(10, 2)
        )

        bg_frame = ttk.Frame(
            website_box
        )

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

        ttk.Button(
            website_box,
            text="Apply Website Settings",
            command=self.update_page_setting
        ).pack(
            fill="x",
            padx=8,
            pady=10
        )

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
            "input",
            "container"
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
                element.get(
                    "url",
                    "https://example.com"
                )
            )

        if element["type"] == "image":

            ttk.Label(
                self.property_box,
                text="Image path:"
            ).pack(
                anchor="w",
                padx=8
            )

            image_frame = ttk.Frame(
                self.property_box
            )

            image_frame.pack(
                fill="x",
                padx=8,
                pady=4
            )

            self.image_entry = ttk.Entry(
                image_frame
            )

            self.image_entry.pack(
                side="left",
                fill="x",
                expand=True
            )

            self.image_entry.insert(
                0,
                element.get("path", "")
            )

            ttk.Button(
                image_frame,
                text="Browse",
                command=self.choose_image
            ).pack(
                side="right",
                padx=(5, 0)
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
            element.get(
                "color",
                "#000000"
            )
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
            "y": 80 + len(self.elements) * 55,
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
    # SELECTED ELEMENT
    # =========================================================

    def get_selected(self):

        for element in self.elements:
            if element["id"] == self.selected_id:
                return element

        return None

    # =========================================================
    # DRAW CANVAS
    # =========================================================

    def draw_canvas(self):

        self.canvas.delete("all")

        width = int(
            self.page_settings["width"] * self.zoom
        )

        height = int(
            self.page_settings["height"] * self.zoom
        )

        self.canvas.configure(
            scrollregion=(
                20,
                20,
                width + 40,
                height + 40
            )
        )

        # Page background

        self.canvas.create_rectangle(
            20,
            20,
            width + 20,
            height + 20,
            fill=self.page_settings["background"],
            outline="#999999"
        )

        for element in self.elements:

            x = 20 + element["x"] * self.zoom
            y = 20 + element["y"] * self.zoom

            w = element["width"] * self.zoom
            h = element["height"] * self.zoom

            selected = (
                element["id"] == self.selected_id
            )

            outline = (
                "#0078d7"
                if selected
                else "#888888"
            )

            kind = element["type"]

            if kind == "text":

                self.canvas.create_text(
                    x,
                    y,
                    anchor="nw",
                    text=element.get("text", ""),
                    fill=element.get("color", "#000000"),
                    font=(
                        "Segoe UI",
                        max(
                            1,
                            int(
                                element.get(
                                    "font_size",
                                    16
                                ) * self.zoom
                            )
                        )
                    ),
                    tags=("element", element["id"])
                )

            elif kind == "heading":

                self.canvas.create_text(
                    x,
                    y,
                    anchor="nw",
                    text=element.get("text", ""),
                    fill=element.get("color", "#000000"),
                    font=(
                        "Segoe UI",
                        max(
                            1,
                            int(
                                element.get(
                                    "font_size",
                                    28
                                ) * self.zoom
                            )
                        ),
                        "bold"
                    ),
                    tags=("element", element["id"])
                )

            elif kind == "link":

                self.canvas.create_text(
                    x,
                    y,
                    anchor="nw",
                    text=element.get(
                        "text",
                        "Click here"
                    ),
                    fill=element.get(
                        "color",
                        "#0000ee"
                    ),
                    underline=True,
                    font=(
                        "Segoe UI",
                        max(
                            1,
                            int(
                                element.get(
                                    "font_size",
                                    16
                                ) * self.zoom
                            )
                        )
                    ),
                    tags=("element", element["id"])
                )

            elif kind == "button":

                self.canvas.create_rectangle(
                    x,
                    y,
                    x + w,
                    y + h,
                    fill="#eeeeee",
                    outline=outline,
                    width=2,
                    tags=("element", element["id"])
                )

                self.canvas.create_text(
                    x + w / 2,
                    y + h / 2,
                    text=element.get(
                        "text",
                        "Button"
                    ),
                    fill=element.get(
                        "color",
                        "#000000"
                    ),
                    font=(
                        "Segoe UI",
                        max(
                            1,
                            int(
                                element.get(
                                    "font_size",
                                    16
                                ) * self.zoom
                            )
                        )
                    ),
                    tags=("element", element["id"])
                )

            elif kind == "input":

                self.canvas.create_rectangle(
                    x,
                    y,
                    x + w,
                    y + h,
                    fill="#ffffff",
                    outline=outline,
                    width=2,
                    tags=("element", element["id"])
                )

                self.canvas.create_text(
                    x + 8 * self.zoom,
                    y + h / 2,
                    anchor="w",
                    text=element.get(
                        "text",
                        "Enter text"
                    ),
                    fill="#777777",
                    font=(
                        "Segoe UI",
                        max(
                            1,
                            int(
                                element.get(
                                    "font_size",
                                    16
                                ) * self.zoom
                            )
                        )
                    ),
                    tags=("element", element["id"])
                )

            elif kind == "image":

                self.canvas.create_rectangle(
                    x,
                    y,
                    x + w,
                    y + h,
                    fill="#eeeeee",
                    outline=outline,
                    width=2,
                    tags=("element", element["id"])
                )

                self.canvas.create_text(
                    x + w / 2,
                    y + h / 2,
                    text="Image",
                    fill="#777777",
                    font=("Segoe UI", 14),
                    tags=("element", element["id"])
                )

            elif kind == "divider":

                self.canvas.create_line(
                    x,
                    y + h / 2,
                    x + w,
                    y + h / 2,
                    fill="#555555",
                    width=max(
                        1,
                        int(2 * self.zoom)
                    ),
                    tags=("element", element["id"])
                )

            elif kind == "container":

                self.canvas.create_rectangle(
                    x,
                    y,
                    x + w,
                    y + h,
                    fill="",
                    outline=outline,
                    width=2,
                    dash=(5, 3),
                    tags=("element", element["id"])
                )

                self.canvas.create_text(
                    x + 8,
                    y + 8,
                    anchor="nw",
                    text=element.get(
                        "text",
                        "Container"
                    ),
                    fill="#777777",
                    font=("Segoe UI", 10),
                    tags=("element", element["id"])
                )

    # =========================================================
    # CANVAS CLICK
    # =========================================================

    def canvas_click(self, event):

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        found = None

        for element in reversed(self.elements):

            ex = 20 + element["x"] * self.zoom
            ey = 20 + element["y"] * self.zoom

            ew = element["width"] * self.zoom
            eh = element["height"] * self.zoom

            if (
                ex <= x <= ex + ew
                and
                ey <= y <= ey + eh
            ):
                found = element
                break

        if found:

            self.selected_id = found["id"]

            self.drag_data = {
                "mouse_x": x,
                "mouse_y": y,
                "element_x": found["x"],
                "element_y": found["y"]
            }

            self.show_properties()
            self.draw_canvas()

        else:

            self.selected_id = None
            self.drag_data = None

            self.show_properties()
            self.draw_canvas()

    # =========================================================
    # CANVAS DRAG
    # =========================================================

    def canvas_drag(self, event):

        element = self.get_selected()

        if not element:
            return

        if not self.drag_data:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        dx = (
            x - self.drag_data["mouse_x"]
        ) / self.zoom

        dy = (
            y - self.drag_data["mouse_y"]
        ) / self.zoom

        element["x"] = max(
            0,
            int(
                self.drag_data["element_x"] + dx
            )
        )

        element["y"] = max(
            0,
            int(
                self.drag_data["element_y"] + dy
            )
        )

        self.draw_canvas()

        self.update_property_entries()

    # =========================================================
    # CANVAS RELEASE
    # =========================================================

    def canvas_release(self, event):

        self.drag_data = None

        self.status_var.set(
            "Element moved"
        )

    # =========================================================
    # UPDATE PROPERTY ENTRIES
    # =========================================================

    def update_property_entries(self):

        element = self.get_selected()

        if not element:
            return

        try:
            self.x_entry.delete(0, "end")
            self.x_entry.insert(
                0,
                str(element["x"])
            )

            self.y_entry.delete(0, "end")
            self.y_entry.insert(
                0,
                str(element["y"])
            )
        except:
            pass

    # =========================================================
    # UPDATE ELEMENT
    # =========================================================

    def update_element_property(self):

        element = self.get_selected()

        if not element:
            return

        try:

            if hasattr(self, "text_entry"):
                element["text"] = (
                    self.text_entry.get()
                )

            if hasattr(self, "url_entry"):
                element["url"] = (
                    self.url_entry.get()
                )

            if hasattr(self, "image_entry"):
                element["path"] = (
                    self.image_entry.get()
                )

            if hasattr(self, "font_entry"):
                element["font_size"] = max(
                    1,
                    int(
                        self.font_entry.get()
                    )
                )

            if hasattr(self, "color_entry"):
                element["color"] = (
                    self.color_entry.get()
                )

            if hasattr(self, "x_entry"):
                element["x"] = max(
                    0,
                    int(
                        self.x_entry.get()
                    )
                )

            if hasattr(self, "y_entry"):
                element["y"] = max(
                    0,
                    int(
                        self.y_entry.get()
                    )
                )

        except ValueError:

            messagebox.showerror(
                "Invalid value",
                "Please enter valid numbers."
            )

            return

        self.draw_canvas()

        self.status_var.set(
            "Element updated"
        )

    # =========================================================
    # DELETE
    # =========================================================

    def delete_selected(self):

        if self.selected_id is None:
            return

        self.elements = [
            e
            for e in self.elements
            if e["id"] != self.selected_id
        ]

        self.selected_id = None

        self.show_properties()
        self.draw_canvas()

        self.status_var.set(
            "Element deleted"
        )

    # =========================================================
    # COLORS
    # =========================================================

    def choose_background(self):

        color = colorchooser.askcolor(
            initialcolor=self.page_settings[
                "background"
            ]
        )

        if color[1]:

            self.bg_entry.delete(
                0,
                "end"
            )

            self.bg_entry.insert(
                0,
                color[1]
            )

            self.update_page_setting()

    def choose_text_color(self):

        element = self.get_selected()

        if not element:
            return

        color = colorchooser.askcolor(
            initialcolor=element.get(
                "color",
                "#000000"
            )
        )

        if color[1]:

            self.color_entry.delete(
                0,
                "end"
            )

            self.color_entry.insert(
                0,
                color[1]
            )

            self.update_element_property()

    # =========================================================
    # IMAGE
    # =========================================================

    def choose_image(self):

        path = filedialog.askopenfilename(
            title="Choose Image",
            filetypes=[
                (
                    "Images",
                    "*.png *.jpg *.jpeg *.gif *.webp"
                ),
                (
                    "All files",
                    "*.*"
                )
            ]
        )

        if path:

            self.image_entry.delete(
                0,
                "end"
            )

            self.image_entry.insert(
                0,
                path
            )

            self.update_element_property()

    # =========================================================
    # WEBSITE SETTINGS
    # =========================================================

    def update_page_setting(self):

        try:

            self.page_settings["title"] = (
                self.title_entry.get()
            )

            self.page_settings["background"] = (
                self.bg_entry.get()
            )

            self.page_settings["width"] = max(
                100,
                int(
                    self.width_entry.get()
                )
            )

            self.page_settings["height"] = max(
                100,
                int(
                    self.height_entry.get()
                )
            )

        except ValueError:

            messagebox.showerror(
                "Invalid value",
                "Width and height must be numbers."
            )

            return

        self.draw_canvas()

    # =========================================================
    # ZOOM
    # =========================================================

    def change_zoom(self, event=None):

        value = self.zoom_var.get()

        self.zoom = (
            int(
                value.replace(
                    "%",
                    ""
                )
            ) / 100
        )

        self.draw_canvas()

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

        self.project_file = None
        self.elements = []
        self.selected_id = None
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

        self.show_properties()
        self.draw_canvas()

        self.status_var.set(
            "New project created"
        )

    # =========================================================
    # SAVE PROJECT
    # =========================================================

    def save_project(self):

        data = {
            "version": 2,
            "page_settings": self.page_settings,
            "elements": self.elements,
            "element_counter": self.element_counter
        }

        if not self.project_file:

            self.project_file = filedialog.asksaveasfilename(
                title="Save Project",
                defaultextension=".json",
                filetypes=[
                    (
                        "WebCraft Project",
                        "*.json"
                    ),
                    (
                        "All files",
                        "*.*"
                    )
                ]
            )

        if not self.project_file:
            return

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
    # OPEN PROJECT
    # =========================================================

    def open_project(self):

        path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[
                (
                    "WebCraft Project",
                    "*.json"
                ),
                (
                    "All files",
                    "*.*"
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
                "page_settings",
                {
                    "title": "My Website",
                    "background": "#ffffff",
                    "width": 900,
                    "height": 600
                }
            )

            self.elements = data.get(
                "elements",
                []
            )

            self.element_counter = data.get(
                "element_counter",
                len(self.elements)
            )

            self.selected_id = None

            self.title_entry.delete(0, "end")
            self.title_entry.insert(
                0,
                self.page_settings.get(
                    "title",
                    "My Website"
                )
            )

            self.bg_entry.delete(0, "end")
            self.bg_entry.insert(
                0,
                self.page_settings.get(
                    "background",
                    "#ffffff"
                )
            )

            self.width_entry.delete(0, "end")
            self.width_entry.insert(
                0,
                str(
                    self.page_settings.get(
                        "width",
                        900
                    )
                )
            )

            self.height_entry.delete(0, "end")
            self.height_entry.insert(
                0,
                str(
                    self.page_settings.get(
                        "height",
                        600
                    )
                )
            )

            self.show_properties()
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
    # GENERATE HTML
    # =========================================================

    def generate_html(self):

        title = html.escape(
            self.page_settings.get(
                "title",
                "My Website"
            )
        )

        background = html.escape(
            self.page_settings.get(
                "background",
                "#ffffff"
            )
        )

        width = self.page_settings.get(
            "width",
            900
        )

        height = self.page_settings.get(
            "height",
            600
        )

        elements_html = []

        for element in self.elements:

            kind = element.get(
                "type",
                "text"
            )

            x = element.get("x", 0)
            y = element.get("y", 0)
            w = element.get("width", 180)
            h = element.get("height", 45)

            font_size = element.get(
                "font_size",
                16
            )

            color = html.escape(
                element.get(
                    "color",
                    "#000000"
                )
            )

            text = html.escape(
                element.get(
                    "text",
                    ""
                )
            )

            base_style = (
                f"position:absolute;"
                f"left:{x}px;"
                f"top:{y}px;"
                f"width:{w}px;"
                f"height:{h}px;"
                f"box-sizing:border-box;"
                f"color:{color};"
                f"font-size:{font_size}px;"
                f"font-family:Arial,sans-serif;"
            )

            if kind == "text":

                elements_html.append(
                    f'<div style="{base_style}">'
                    f'{text}'
                    f'</div>'
                )

            elif kind == "heading":

                elements_html.append(
                    f'<h1 style="{base_style};'
                    f'margin:0;font-weight:bold;">'
                    f'{text}'
                    f'</h1>'
                )

            elif kind == "link":

                url = html.escape(
                    element.get(
                        "url",
                        "https://example.com"
                    ),
                    quote=True
                )

                elements_html.append(
                    f'<a href="{url}" '
                    f'target="_blank" '
                    f'style="{base_style};">'
                    f'{text}'
                    f'</a>'
                )

            elif kind == "button":

                elements_html.append(
                    f'<button style="{base_style};'
                    f'cursor:pointer;">'
                    f'{text}'
                    f'</button>'
                )

            elif kind == "input":

                placeholder = html.escape(
                    element.get(
                        "text",
                        "Enter text"
                    ),
                    quote=True
                )

                elements_html.append(
                    f'<input '
                    f'type="text" '
                    f'placeholder="{placeholder}" '
                    f'style="{base_style};'
                    f'padding:8px;">'
                )

            elif kind == "image":

                image_path = element.get(
                    "path",
                    ""
                )

                image_path = html.escape(
                    image_path,
                    quote=True
                )

                elements_html.append(
                    f'<img '
                    f'src="{image_path}" '
                    f'alt="Image" '
                    f'style="{base_style};'
                    f'object-fit:contain;">'
                )

            elif kind == "divider":

                elements_html.append(
                    f'<div style="'
                    f'position:absolute;'
                    f'left:{x}px;'
                    f'top:{y}px;'
                    f'width:{w}px;'
                    f'height:2px;'
                    f'background:#555555;'
                    f'"></div>'
                )

            elif kind == "container":

                elements_html.append(
                    f'<div style="'
                    f'position:absolute;'
                    f'left:{x}px;'
                    f'top:{y}px;'
                    f'width:{w}px;'
                    f'height:{h}px;'
                    f'border:1px dashed #888;'
                    f'box-sizing:border-box;'
                    f'">'
                    f'{text}'
                    f'</div>'
                )

        return f"""<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>{title}</title>

<style>

html,
body {{
    margin: 0;
    padding: 0;
}}

body {{
    background: {background};
}}

#webcraft-page {{
    position: relative;
    width: {width}px;
    height: {height}px;
    margin: 20px auto;
    overflow: hidden;
}}

</style>

</head>

<body>

<div id="webcraft-page">

{chr(10).join(elements_html)}

</div>

</body>

</html>
"""

    # =========================================================
    # EXPORT HTML
    # =========================================================

    def export_html(self):

        path = filedialog.asksaveasfilename(
            title="Export HTML",
            defaultextension=".html",
            initialfile="pannel.html",
            filetypes=[
                (
                    "HTML files",
                    "*.html"
                ),
                (
                    "All files",
                    "*.*"
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

            self.status_var.set(
                "HTML exported"
            )

            messagebox.showinfo(
                "Export HTML",
                "HTML file created successfully."
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

        try:

            content = self.generate_html()

            if self.project_file:

                folder = os.path.dirname(
                    os.path.abspath(
                        self.project_file
                    )
                )

            else:

                folder = os.getcwd()

            preview_path = os.path.join(
                folder,
                "_webcraft_preview.html"
            )

            with open(
                preview_path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(content)

            webbrowser.open(
                "file:///"
                + preview_path.replace(
                    "\\",
                    "/"
                )
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
    # GITHUB WINDOW
    # =========================================================

    def github_window(self):

        win = tk.Toplevel(
            self.root
        )

        win.title(
            "GitHub"
        )

        win.geometry(
            "500x430"
        )

        win.resizable(
            False,
            False
        )

        frame = ttk.Frame(
            win,
            padding=15
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text="GitHub Personal Access Token:"
        ).pack(
            anchor="w"
        )

        token_entry = ttk.Entry(
            frame,
            show="*"
        )

        token_entry.pack(
            fill="x",
            pady=(4, 12)
        )

        if self.github_token:

            token_entry.insert(
                0,
                self.github_token
            )

        ttk.Label(
            frame,
            text="Repository:"
        ).pack(
            anchor="w"
        )

        repo_entry = ttk.Entry(
            frame
        )

        repo_entry.pack(
            fill="x",
            pady=(4, 12)
        )

        repo_entry.insert(
            0,
            self.github_repo_url
        )

        ttk.Label(
            frame,
            text="File path:"
        ).pack(
            anchor="w"
        )

        path_entry = ttk.Entry(
            frame
        )

        path_entry.pack(
            fill="x",
            pady=(4, 12)
        )

        path_entry.insert(
            0,
            self.github_file_path
        )

        ttk.Label(
            frame,
            text="Branch:"
        ).pack(
            anchor="w"
        )

        branch_entry = ttk.Entry(
            frame
        )

        branch_entry.pack(
            fill="x",
            pady=(4, 15)
        )

        branch_entry.insert(
            0,
            self.github_branch
        )

        ttk.Button(
            frame,
            text="Save Settings",
            command=lambda: self.save_github_settings(
                token_entry,
                repo_entry,
                path_entry,
                branch_entry,
                win
            )
        ).pack(
            fill="x",
            pady=4
        )

        ttk.Button(
            frame,
            text="Save HTML to GitHub",
            command=lambda: self.upload_to_github(
                token_entry.get(),
                repo_entry.get(),
                path_entry.get(),
                branch_entry.get()
            )
        ).pack(
            fill="x",
            pady=4
        )

        ttk.Label(
            frame,
            text=(
                "Repository example:\n"
                "HlRUD/WebCraft\n\n"
                "File path:\n"
                "main/pannel.html"
            ),
            justify="center"
        ).pack(
            pady=15
        )

    # =========================================================
    # SAVE GITHUB SETTINGS
    # =========================================================

    def save_github_settings(
        self,
        token_entry,
        repo_entry,
        path_entry,
        branch_entry,
        window
    ):

        self.github_token = (
            token_entry.get().strip()
        )

        self.github_repo_url = (
            repo_entry.get().strip()
        )

        self.github_file_path = (
            path_entry.get().strip()
            or "main/pannel.html"
        )

        self.github_branch = (
            branch_entry.get().strip()
            or "main"
        )

        window.destroy()

        self.status_var.set(
            "GitHub settings saved"
        )

    # =========================================================
    # GITHUB UPLOAD
    # =========================================================

    def upload_to_github(
        self,
        token,
        repo,
        file_path,
        branch
    ):

        token = token.strip()
        repo = repo.strip()
        file_path = file_path.strip()
        branch = branch.strip()

        if not token:

            messagebox.showerror(
                "GitHub",
                "Please enter your GitHub token."
            )

            return

        if not repo:

            messagebox.showerror(
                "GitHub",
                "Please enter your repository.\n\n"
                "Example:\n"
                "HlRUD/WebCraft"
            )

            return

        # Allow full GitHub URL too

        if repo.startswith(
            "https://github.com/"
        ):

            repo = repo[
                len("https://github.com/"):
            ]

        elif repo.startswith(
            "http://github.com/"
        ):

            repo = repo[
                len("http://github.com/"):
            ]

        repo = repo.rstrip("/")

        if repo.count("/") != 1:

            messagebox.showerror(
                "GitHub",
                "Repository format must be:\n\n"
                "username/repository"
            )

            return

        if not file_path:

            file_path = "main/pannel.html"

        if not branch:

            branch = "main"

        try:

            content = self.generate_html()

            encoded_content = base64.b64encode(
                content.encode("utf-8")
            ).decode("ascii")

            api_url = (
                "https://api.github.com/repos/"
                f"{repo}/contents/"
                f"{file_path}"
            )

            headers = {
                "Authorization":
                    f"Bearer {token}",

                "Accept":
                    "application/vnd.github+json",

                "X-GitHub-Api-Version":
                    "2022-11-28",

                "User-Agent":
                    "WebCraft-Website-Builder"
            }

            # Check if file already exists

            response = requests.get(
                api_url,
                headers=headers,
                params={
                    "ref": branch
                },
                timeout=20
            )

            sha = None

            if response.status_code == 200:

                result = response.json()

                sha = result.get(
                    "sha"
                )

            elif response.status_code == 404:

                sha = None

            else:

                try:

                    error_text = response.json().get(
                        "message",
                        response.text
                    )

                except:

                    error_text = response.text

                raise Exception(
                    f"GitHub error "
                    f"{response.status_code}:\n"
                    f"{error_text}"
                )

            payload = {
                "message":
                    "Update pannel.html "
                    "from WebCraft",

                "content":
                    encoded_content,

                "branch":
                    branch
            }

            if sha:

                payload["sha"] = sha

            response = requests.put(
                api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code not in (
                200,
                201
            ):

                try:

                    error_text = response.json().get(
                        "message",
                        response.text
                    )

                except:

                    error_text = response.text

                raise Exception(
                    f"GitHub upload failed "
                    f"{response.status_code}:\n"
                    f"{error_text}"
                )

            self.github_token = token
            self.github_repo_url = repo
            self.github_file_path = file_path
            self.github_branch = branch

            self.status_var.set(
                "Saved to GitHub"
            )

            messagebox.showinfo(
                "GitHub",
                "HTML saved successfully!\n\n"
                f"Repository: {repo}\n"
                f"File: {file_path}\n"
                f"Branch: {branch}"
            )

        except requests.RequestException as e:

            messagebox.showerror(
                "Network Error",
                str(e)
            )

        except Exception as e:

            messagebox.showerror(
                "GitHub Error",
                str(e)
            )

    # =========================================================
    # KEYBOARD SHORTCUTS
    # =========================================================

    def bind_shortcuts(self):

        self.root.bind(
            "<Control-s>",
            lambda event: self.save_project()
        )

        self.root.bind(
            "<Control-o>",
            lambda event: self.open_project()
        )

        self.root.bind(
            "<Control-n>",
            lambda event: self.new_project()
        )

                self.root.bind(
            "<Delete>",
            lambda event: self.delete_selected()
        )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = WebsiteBuilder(
        root
    )

    root.mainloop()