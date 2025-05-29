
# Stohrer Sax Pad SVG Generator - Full GUI and SVG Export Tool with Docked Preview and Enhanced Interaction

import svgwrite
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

FELT_OFFSET = 0.75
CARD_OFFSET = FELT_OFFSET + 2.0  # Tapered card
CENTER_HOLE_DIAMETER = 3.5

LAYER_COLORS = {
    'felt': 'black',
    'card': 'blue',
    'leather': 'red',
    'center_hole': 'dimgray',
    'engraving': 'orange'
}

positions = {}  # key = (material, index), value = list of positions


def leather_back_wrap(pad_size):
    if pad_size <= 10:
        return 1.3
    elif pad_size <= 15:
        return 1.3 + (pad_size - 10) * (0.7 / 5.0)
    elif pad_size <= 40:
        return 2.0 + (pad_size - 15) * (1.5 / 25.0)
    else:
        return 3.5


def should_have_center_hole(pad_size):
    return pad_size >= 16.5


def generate_svg(pads, material, width_mm, height_mm, filename):
    dwg = svgwrite.Drawing(filename, size=(f"{width_mm}mm", f"{height_mm}mm"))
    for i, pad in enumerate(pads):
        pad_size = pad['size']
        qty = pad['qty']
        for j in range(qty):
            if material == 'felt':
                diameter = pad_size - FELT_OFFSET
            elif material == 'card':
                diameter = pad_size - CARD_OFFSET
            elif material == 'leather':
                diameter = pad_size + 2 * (3.175 + leather_back_wrap(pad_size))
                diameter = round(diameter * 2) / 2
            else:
                continue

            pos_key = (material, i)
            x, y = positions.get(pos_key, [(10 + j * (diameter + 1), 10)])[j % len(positions.get(pos_key, [(10, 10)]))]
            cx = x + diameter / 2
            cy = y + diameter / 2
            dwg.add(dwg.circle(center=(cx, cy), r=diameter/2, stroke=LAYER_COLORS[material], fill='none'))

            if material != 'leather' and should_have_center_hole(pad_size):
                dwg.add(dwg.circle(center=(cx, cy), r=CENTER_HOLE_DIAMETER / 2, stroke=LAYER_COLORS['center_hole'], fill='none'))

            if material in ['felt', 'card']:
                radius = (diameter / 2 + CENTER_HOLE_DIAMETER / 2) / 2
                dwg.add(dwg.text(f"{pad_size:.1f}".rstrip('0').rstrip('.'),
                                 insert=(cx, cy - radius),
                                 text_anchor="middle", alignment_baseline="middle",
                                 font_size="2mm", fill=LAYER_COLORS['engraving']))
            elif material == 'leather':
                radius = diameter / 2 - 1.0
                dwg.add(dwg.text(f"{pad_size:.1f}".rstrip('0').rstrip('.'),
                                 insert=(cx, cy - radius),
                                 text_anchor="middle", alignment_baseline="middle",
                                 font_size="2mm", fill=LAYER_COLORS['engraving']))
    dwg.save()


def parse_pad_list(pad_input):
    pad_list = []
    for line in pad_input.strip().splitlines():
        try:
            size, qty = map(float, line.strip().split('x'))
            pad_list.append({'size': size, 'qty': int(qty)})
        except:
            continue
    return pad_list


class PadPreview(tk.Canvas):
    def __init__(self, parent, width, height, material, pads, *args, **kwargs):
        super().__init__(parent, width=width, height=height, bg='white', *args, **kwargs)
        self.scale = 2
        self.material = material
        self.pads = pads
        self.discs = {}
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        self.drag_data = {'item': None, 'start_x': 0, 'start_y': 0}
        self.draw_grid(width, height)
        self.draw_discs()

    def draw_grid(self, w, h):
        inch = 25.4 * self.scale
        for x in range(0, int(w), int(inch)):
            self.create_line(x, 0, x, h, fill='lightgray')
        for y in range(0, int(h), int(inch)):
            self.create_line(0, y, w, y, fill='lightgray')

    def draw_discs(self):
        self.delete("disc")
        for i, pad in enumerate(self.pads):
            pad_size = pad['size']
            qty = pad['qty']
            for j in range(qty):
                if self.material == 'felt':
                    diameter = pad_size - FELT_OFFSET
                elif self.material == 'card':
                    diameter = pad_size - CARD_OFFSET
                elif self.material == 'leather':
                    diameter = pad_size + 2 * (3.175 + leather_back_wrap(pad_size))
                    diameter = round(diameter * 2) / 2
                else:
                    continue

                x = 10 + (j * (diameter + 2))
                y = 10 + i * (diameter + 10)
                cx = x + diameter / 2
                cy = y + diameter / 2
                r = diameter / 2

                pos_key = (self.material, i)
                if pos_key not in positions:
                    positions[pos_key] = []
                if len(positions[pos_key]) <= j:
                    positions[pos_key].append((x, y))

                disc = self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=LAYER_COLORS[self.material], fill='', tags=("disc", f"disc_{i}_{j}"))
                self.discs[disc] = (self.material, i, j)

    def start_drag(self, event):
        item = self.find_closest(event.x, event.y)[0]
        if item in self.discs:
            self.drag_data['item'] = item
            self.drag_data['start_x'] = event.x
            self.drag_data['start_y'] = event.y

    def do_drag(self, event):
        item = self.drag_data['item']
        if item:
            dx = (event.x - self.drag_data['start_x']) / self.scale
            dy = (event.y - self.drag_data['start_y']) / self.scale
            self.move(item, dx * self.scale, dy * self.scale)
            mat, i, j = self.discs[item]
            old_x, old_y = positions[(mat, i)][j]
            positions[(mat, i)][j] = (old_x + dx, old_y + dy)
            self.drag_data['start_x'] = event.x
            self.drag_data['start_y'] = event.y


def launch_gui():
    root = tk.Tk()
    root.title("Stohrer Sax Pad SVG Generator")
    root.geometry("1200x600")
    root.configure(bg="#FFFDD0")

    left_frame = tk.Frame(root, bg="#FFFDD0")
    left_frame.pack(side='left', fill='y', padx=10, pady=10)

    right_frame = tk.Frame(root)
    right_frame.pack(side='right', fill='both', expand=True)

    tk.Label(left_frame, text="Enter pad sizes (e.g. 42.0x3):", bg="#FFFDD0").pack()
    pad_entry = tk.Text(left_frame, height=10)
    pad_entry.pack(fill="x", pady=5)

    tk.Label(left_frame, text="Select materials:", bg="#FFFDD0").pack()
    material_vars = {'felt': tk.BooleanVar(), 'card': tk.BooleanVar(), 'leather': tk.BooleanVar()}
    for m in material_vars:
        tk.Checkbutton(left_frame, text=m.capitalize(), variable=material_vars[m], bg="#FFFDD0").pack(anchor='w')

    tk.Label(left_frame, text="Sheet width (inches):", bg="#FFFDD0").pack()
    width_entry = tk.Entry(left_frame)
    width_entry.insert(0, "13.5")
    width_entry.pack()

    tk.Label(left_frame, text="Sheet height (inches):", bg="#FFFDD0").pack()
    height_entry = tk.Entry(left_frame)
    height_entry.insert(0, "10")
    height_entry.pack()

    tk.Label(left_frame, text="Output filename base:", bg="#FFFDD0").pack()
    filename_entry = tk.Entry(left_frame)
    filename_entry.insert(0, "my_pad_job")
    filename_entry.pack(fill="x", pady=5)

    preview_canvas = None

    def on_preview():
        nonlocal preview_canvas
        if preview_canvas:
            preview_canvas.destroy()
            preview_canvas = None
            return
        try:
            width_mm = float(width_entry.get()) * 25.4
            height_mm = float(height_entry.get()) * 25.4
        except:
            messagebox.showerror("Error", "Invalid dimensions.")
            return

        pads = parse_pad_list(pad_entry.get("1.0", tk.END))
        for material, var in material_vars.items():
            if var.get():
                preview_canvas = PadPreview(right_frame, int(width_mm * 2), int(height_mm * 2), material, pads)
                preview_canvas.pack()

    def on_generate():
        try:
            width_mm = float(width_entry.get()) * 25.4
            height_mm = float(height_entry.get()) * 25.4
        except:
            messagebox.showerror("Error", "Invalid sheet dimensions.")
            return

        pads = parse_pad_list(pad_entry.get("1.0", tk.END))
        if not pads:
            messagebox.showerror("Error", "No valid pad sizes entered.")
            return

        base = filename_entry.get().strip()
        save_dir = filedialog.askdirectory(title="Select Folder to Save SVGs")
        if not save_dir:
            return

        for material, var in material_vars.items():
            if var.get():
                filename = os.path.join(save_dir, f"{base}_{material}.svg")
                generate_svg(pads, material, width_mm, height_mm, filename)

        messagebox.showinfo("Done", "SVGs generated.")

    tk.Button(left_frame, text="Preview Layout", command=on_preview).pack(pady=5)
    tk.Button(left_frame, text="Generate SVGs", command=on_generate).pack(pady=5)

    root.mainloop()


if __name__ == '__main__':
    launch_gui()
