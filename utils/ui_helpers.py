"""
Utilidades compartidas para la interfaz gráfica.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime


# ── Paleta de colores ────────────────────────────────────────────────────────
COLORS = {
    "bg_app":     "#f0f4f8",
    "bg_panel":   "#ffffff",
    "bg_sidebar": "#1a3a5c",
    "accent":     "#2b6cb0",
    "accent2":    "#ebf4ff",
    "success":    "#276749",
    "danger":     "#c0392b",
    "warning":    "#b7791f",
    "text":       "#1a202c",
    "text_light": "#718096",
    "border":     "#cbd5e0",
    "row_alt":    "#f7fafc",
    "header_bg":  "#1a3a5c",
    "header_fg":  "#ffffff",
}

FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 11)


def configure_treeview_style():
    """Aplica estilo visual moderno al Treeview."""
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("Treeview",
        background=COLORS["bg_panel"],
        foreground=COLORS["text"],
        rowheight=32,
        fieldbackground=COLORS["bg_panel"],
        font=FONT_NORMAL,
        borderwidth=0,
    )
    style.configure("Treeview.Heading",
        background=COLORS["header_bg"],
        foreground=COLORS["header_fg"],
        font=FONT_HEADER,
        relief="flat",
    )
    style.map("Treeview",
        background=[("selected", COLORS["accent"])],
        foreground=[("selected", "white")],
    )
    style.map("Treeview.Heading",
        background=[("active", COLORS["accent"])],
    )

    style.configure("TButton",
        font=FONT_NORMAL,
        padding=(10, 6),
        background=COLORS["accent"],
        foreground="white",
        borderwidth=0,
        relief="flat",
    )
    style.map("TButton",
        background=[("active", "#1a5090"), ("pressed", "#153e75")],
    )

    style.configure("Danger.TButton",
        background=COLORS["danger"],
        foreground="white",
    )
    style.map("Danger.TButton",
        background=[("active", "#992d22")],
    )

    style.configure("Success.TButton",
        background=COLORS["success"],
        foreground="white",
    )
    style.map("Success.TButton",
        background=[("active", "#1c5136")],
    )

    style.configure("TLabel",
        background=COLORS["bg_panel"],
        foreground=COLORS["text"],
        font=FONT_NORMAL,
    )
    style.configure("TEntry",
        font=FONT_NORMAL,
        padding=5,
    )
    style.configure("TCombobox",
        font=FONT_NORMAL,
        padding=5,
    )
    style.configure("TNotebook",
        background=COLORS["bg_app"],
        borderwidth=0,
    )
    style.configure("TNotebook.Tab",
        font=FONT_NORMAL,
        padding=(12, 6),
        background=COLORS["bg_app"],
    )
    style.map("TNotebook.Tab",
        background=[("selected", COLORS["bg_panel"])],
        foreground=[("selected", COLORS["accent"])],
    )


def make_label_entry(parent, label_text, row, col=0, width=25, colspan=1):
    """Crea un par Label + Entry en un grid."""
    ttk.Label(parent, text=label_text, style="FormLabel.TLabel").grid(
        row=row, column=col, sticky="w", padx=(0, 8), pady=3)
    entry = ttk.Entry(parent, width=width)
    entry.grid(row=row, column=col + 1, sticky="ew", pady=3,
               columnspan=colspan, padx=(0, 12))
    return entry


def make_label_combo(parent, label_text, row, values, col=0, width=23):
    ttk.Label(parent, text=label_text, style="FormLabel.TLabel").grid(
        row=row, column=col, sticky="w", padx=(0, 8), pady=3)
    combo = ttk.Combobox(parent, values=values, width=width, state="readonly")
    combo.grid(row=row, column=col + 1, sticky="ew", pady=3, padx=(0, 12))
    return combo


def set_entry(entry, value):
    entry.delete(0, tk.END)
    if value is not None:
        entry.insert(0, str(value))


def get_entry(entry) -> str:
    return entry.get().strip()


def format_date(dt) -> str:
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y")
    return str(dt)


def parse_date_str(s: str):
    s = s.strip()
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def parse_float_str(s: str) -> float:
    try:
        return float(s.strip().replace(",", ".")) if s.strip() else 0.0
    except ValueError:
        return 0.0


def center_window(window, width, height):
    """Centra una ventana en la pantalla."""
    window.update_idletasks()
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    x  = (sw - width) // 2
    y  = (sh - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def scrolled_treeview(parent, columns, headings, col_widths, height=18):
    """Crea un Treeview con scrollbars verticales y horizontales."""
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True)

    vsb = ttk.Scrollbar(frame, orient="vertical")
    hsb = ttk.Scrollbar(frame, orient="horizontal")

    tree = ttk.Treeview(
        frame,
        columns=columns,
        show="headings",
        height=height,
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set,
    )
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    for col, heading, width in zip(columns, headings, col_widths):
        tree.heading(col, text=heading, anchor="w")
        tree.column(col, width=width, minwidth=50, anchor="w")

    tree.tag_configure("pagado",  background="#e6f4ea", foreground=COLORS["success"])
    tree.tag_configure("impago",  background="#fde8e8", foreground=COLORS["danger"])
    tree.tag_configure("baja",    background="#f0f0f0", foreground=COLORS["text_light"])
    tree.tag_configure("vencido", background="#fff3cd", foreground=COLORS["warning"])

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    return tree, frame


def confirm_dialog(parent, title, message) -> bool:
    from tkinter import messagebox
    return messagebox.askyesno(title, message, parent=parent)


def info_dialog(parent, title, message):
    from tkinter import messagebox
    messagebox.showinfo(title, message, parent=parent)


def error_dialog(parent, title, message):
    from tkinter import messagebox
    messagebox.showerror(title, message, parent=parent)
