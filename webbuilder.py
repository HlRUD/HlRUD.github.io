import tkinter as tk
from tkinter import messagebox
import requests
import base64
from urllib.parse import urlparse


# =========================
# GitHub
# =========================

def get_github_info():
    repo_url = repo_entry.get().strip()
    file_path = file_entry.get().strip()
    token = token_entry.get().strip()

    if not token:
        messagebox.showerror("Error", "GitHub Token را وارد کن.")
        return None

    if not repo_url:
        messagebox.showerror("Error", "آدرس Repository را وارد کن.")
        return None

    if not file_path:
        messagebox.showerror("Error", "مسیر فایل را وارد کن.")
        return None

    try:
        parsed = urlparse(repo_url)

        parts = parsed.path.strip("/").split("/")

        if len(parts) < 2:
            raise ValueError()

        owner = parts[0]
        repo = parts[1]

        # حذف .git اگر وجود داشت
        if repo.endswith(".git"):
            repo = repo[:-4]

        return token, owner, repo, file_path

    except:
        messagebox.showerror(
            "Error",
            "آدرس Repository صحیح نیست.\n\n"
            "مثال:\n"
            "https://github.com/HlRUD/HlRUD.GITHUB.IO"
        )
        return None


# =========================
# Load
# =========================

def load_file():

    info = get_github_info()

    if not info:
        return

    token, owner, repo, file_path = info

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/contents/{file_path}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:

        response = requests.get(url, headers=headers)

        if response.status_code == 200:

            data = response.json()

            content = base64.b64decode(
                data["content"]
            ).decode("utf-8")

            editor.delete("1.0", tk.END)
            editor.insert("1.0", content)

            status.config(
                text="✓ File loaded from GitHub",
                fg="#00ff88"
            )

        elif response.status_code == 404:

            messagebox.showinfo(
                "File not found",
                "این فایل هنوز در GitHub وجود ندارد.\n"
                "با Save ساخته خواهد شد."
            )

        else:

            messagebox.showerror(
                "GitHub Error",
                response.text
            )

    except Exception as e:

        messagebox.showerror(
            "Connection Error",
            str(e)
        )


# =========================
# Save
# =========================

def save_file():

    info = get_github_info()

    if not info:
        return

    token, owner, repo, file_path = info

    html = editor.get("1.0", tk.END).rstrip()

    if not html:

        messagebox.showwarning(
            "Warning",
            "محتوای HTML خالی است."
        )
        return

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/contents/{file_path}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:

        # بررسی فایل موجود
        response = requests.get(
            url,
            headers=headers
        )

        sha = None

        if response.status_code == 200:

            sha = response.json().get("sha")

        elif response.status_code != 404:

            messagebox.showerror(
                "GitHub Error",
                response.text
            )
            return

        # تبدیل HTML به Base64
        encoded = base64.b64encode(
            html.encode("utf-8")
        ).decode("utf-8")

        data = {
            "message": "Update pannel.html from Web Builder 2",
            "content": encoded
        }

        # اگر فایل قبلاً وجود داشته باشد
        if sha:
            data["sha"] = sha

        result = requests.put(
            url,
            headers=headers,
            json=data
        )

        if result.status_code in (200, 201):

            status.config(
                text="✓ Saved to GitHub",
                fg="#00ff88"
            )

            messagebox.showinfo(
                "Success",
                "فایل با موفقیت در GitHub ذخیره شد."
            )

        else:

            status.config(
                text="✗ Save failed",
                fg="#ff4444"
            )

            messagebox.showerror(
                "GitHub Error",
                result.text
            )

    except Exception as e:

        status.config(
            text="✗ Connection error",
            fg="#ff4444"
        )

        messagebox.showerror(
            "Error",
            str(e)
        )


# =========================
# GUI
# =========================

root = tk.Tk()

root.title("Web Builder 2")
root.geometry("1100x750")
root.configure(bg="#101010")


# Header
header = tk.Frame(
    root,
    bg="#181818",
    height=65
)

header.pack(
    fill="x"
)

title = tk.Label(
    header,
    text="WEB BUILDER 2",
    bg="#181818",
    fg="white",
    font=("Arial", 20, "bold")
)

title.pack(
    side="left",
    padx=20,
    pady=15
)


# Settings
settings = tk.Frame(
    root,
    bg="#151515"
)

settings.pack(
    fill="x",
    padx=15,
    pady=10
)


# Token
tk.Label(
    settings,
    text="GitHub Token",
    bg="#151515",
    fg="white"
).grid(
    row=0,
    column=0,
    padx=8,
    pady=7,
    sticky="w"
)

token_entry = tk.Entry(
    settings,
    bg="#252525",
    fg="white",
    insertbackground="white",
    show="*",
    width=80
)

token_entry.grid(
    row=0,
    column=1,
    padx=8,
    pady=7
)


# Repository
tk.Label(
    settings,
    text="Repository URL",
    bg="#151515",
    fg="white"
).grid(
    row=1,
    column=0,
    padx=8,
    pady=7,
    sticky="w"
)

repo_entry = tk.Entry(
    settings,
    bg="#252525",
    fg="white",
    insertbackground="white",
    width=80
)

repo_entry.grid(
    row=1,
    column=1,
    padx=8,
    pady=7
)

repo_entry.insert(
    0,
    "https://github.com/HlRUD/HlRUD.GITHUB.IO"
)


# File
tk.Label(
    settings,
    text="File Path",
    bg="#151515",
    fg="white"
).grid(
    row=2,
    column=0,
    padx=8,
    pady=7,
    sticky="w"
)

file_entry = tk.Entry(
    settings,
    bg="#252525",
    fg="white",
    insertbackground="white",
    width=80
)

file_entry.grid(
    row=2,
    column=1,
    padx=8,
    pady=7
)

file_entry.insert(
    0,
    "main/pannel.html"
)


# Buttons
buttons = tk.Frame(
    root,
    bg="#101010"
)

buttons.pack(
    fill="x",
    padx=15,
    pady=5
)


load_button = tk.Button(
    buttons,
    text="LOAD FROM GITHUB",
    command=load_file,
    bg="#333333",
    fg="white",
    activebackground="#444444",
    activeforeground="white",
    padx=20,
    pady=10
)

load_button.pack(
    side="left",
    padx=5
)


save_button = tk.Button(
    buttons,
    text="SAVE TO GITHUB",
    command=save_file,
    bg="white",
    fg="black",
    font=("Arial", 10, "bold"),
    padx=25,
    pady=10
)

save_button.pack(
    side="left",
    padx=5
)


# Editor
editor_frame = tk.Frame(
    root,
    bg="#101010"
)

editor_frame.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=10
)


editor = tk.Text(
    editor_frame,
    bg="#090909",
    fg="#eeeeee",
    insertbackground="white",
    selectbackground="#444444",
    font=("Consolas", 11),
    undo=True,
    wrap="none"
)

editor.pack(
    fill="both",
    expand=True
)


# Default HTML
editor.insert(
    "1.0",
"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Web Builder 2</title>
</head>

<body>

<h1>Hello World</h1>

</body>
</html>
"""
)


# Status
status = tk.Label(
    root,
    text="Ready",
    bg="#101010",
    fg="#aaaaaa",
    anchor="w"
)

status.pack(
    fill="x",
    padx=20,
    pady=8
)


root.mainloop()