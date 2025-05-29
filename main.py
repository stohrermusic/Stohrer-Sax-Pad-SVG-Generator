
import svgwrite
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

FELT_OFFSET = 0.75
CARD_OFFSET = FELT_OFFSET + 2.0
CENTER_HOLE_DIAMETER = 3.5

LAYER_COLORS = {
    'felt': 'black',
    'card': 'blue',
    'leather': 'red',
    'center_hole': 'dimgray',
    'engraving': 'orange'
}

positions = {}

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
    mat_positions = positions.get(material, [])
    for i, pad in enumerate(pads):
        pad_size = pad['size']
        qty = pad['qty']
        for j in range(qty):
            if material == 'felt':
                diameter = pad_size - FELT_OFFSET
            elif material == 'card':
                diameter = pad_size - CARD_OFFSET
            elif material == 'leather':
                back_wrap = leather_back_wrap(pad_size)
                diameter = pad_size + 2 * (3.175 + back_wrap)
                diameter = round(diameter * 2) / 2
            else:
                continue
            x, y = mat_positions[i][j] if i < len(mat_positions) and j < len(mat_positions[i]) else (10, 10)
            cx = x + diameter / 2
            cy = y + diameter / 2
            dwg.add(dwg.circle(center=(cx, cy), r=diameter/2, stroke=LAYER_COLORS[material], fill='none'))
            if material != 'leather' and should_have_center_hole(pad_size):
                dwg.add(dwg.circle(center=(cx, cy), r=CENTER_HOLE_DIAMETER / 2, stroke=LAYER_COLORS['center_hole'], fill='none'))
            if material in ['felt', 'card']:
                radius = (diameter / 2 + CENTER_HOLE_DIAMETER / 2) / 2
                dwg.add(dwg.text(f"{pad_size:.1f}".rstrip('0').rstrip('.'), insert=(cx, cy - radius), text_anchor="middle", alignment_baseline="middle", font_size="2mm", fill=LAYER_COLORS['engraving']))
            elif material == 'leather':
                radius = diameter / 2 - 1.0
                dwg.add(dwg.text(f"{pad_size:.1f}".rstrip('0').rstrip('.'), insert=(cx, cy - radius), text_anchor="middle", alignment_baseline="middle", font_size="2mm", fill=LAYER_COLORS['engraving']))
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

class PadPreview:
    def __init__(self, master, canvas, width_mm, height_mm):
        self.canvas = canvas
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.drag_data = {}
        self.pads_by_tag = {}

        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)

    def draw_grid_and_scale(self):
        self.canvas.delete("grid")
        for i in range(0, int(self.canvas['width']), 25):
            self.canvas.create_line(i, 0, i, int(self.canvas['height']), fill="#e0e0e0", tags="grid")
        for i in range(0, int(self.canvas['height']), 25):
            self.canvas.create_line(0, i, int(self.canvas['width']), i, fill="#e0e0e0", tags="grid")

    def show(self, pads, material):
        self.canvas.delete("all")
        self.draw_grid_and_scale()
        tag_prefix = material
        material_pos = []
        x, y = 10, 10
        spacing = 1.0
        row_height = 0
        for i, pad in enumerate(pads):
            pad_size = pad['size']
            qty = pad['qty']
            row = []
            for j in range(qty):
                if material == 'felt':
                    diameter = pad_size - FELT_OFFSET
                elif material == 'card':
                    diameter = pad_size - CARD_OFFSET
                elif material == 'leather':
                    back_wrap = leather_back_wrap(pad_size)
                    diameter = pad_size + 2 * (3.175 + back_wrap)
                    diameter = round(diameter * 2) / 2
                else:
                    continue
                if x + diameter > self.width_mm:
                    x = 10
                    y += row_height + spacing
                    row_height = 0
                if y + diameter > self.height_mm:
                    break
                cx = x + diameter / 2
                cy = y + diameter / 2
                radius = diameter / 2
                tag = f"{tag_prefix}_{i}_{j}"
                group = [
                    self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=LAYER_COLORS[material], tags=tag)
                ]
                if material != 'leather' and should_have_center_hole(pad_size):
                    group.append(
                        self.canvas.create_oval(cx - CENTER_HOLE_DIAMETER / 2, cy - CENTER_HOLE_DIAMETER / 2,
                                                cx + CENTER_HOLE_DIAMETER / 2, cy + CENTER_HOLE_DIAMETER / 2,
                                                outline=LAYER_COLORS['center_hole'], tags=tag)
                    )
                group.append(
                    self.canvas.create_text(cx, cy - radius, text=f"{pad_size:.1f}".rstrip('0').rstrip('.'), tags=tag, fill=LAYER_COLORS['engraving'])
                )
                self.pads_by_tag[tag] = group
                row.append((x, y))
                row_height = max(row_height, diameter)
                x += diameter + spacing
            material_pos.append(row)
        positions[material] = material_pos

    def start_drag(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        if tags:
            self.drag_data = {"tag": tags[0], "x": event.x, "y": event.y}

    def do_drag(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        self.canvas.move(self.drag_data["tag"], dx, dy)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

def launch_gui():
    root = tk.Tk()
    root.title("Stohrer Sax Pad SVG Generator")
    root.configure(bg="#FFFDD0")

    left_frame = tk.Frame(root, bg="#FFFDD0")
    left_frame.pack(side="left", fill="y", padx=10, pady=10)
    right_frame = tk.Frame(root, bg="#FFFDD0")
    right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
    preview_canvas = tk.Canvas(right_frame, width=600, height=600, bg="white")
    preview_canvas.pack(fill="both", expand=True)
    preview_shown = [False]
    preview_tool = [None]

    tk.Label(left_frame, text="Enter pad sizes (e.g. 42.0x3):", bg="#FFFDD0").pack()
    pad_entry = tk.Text(left_frame, height=10)
    pad_entry.pack()

    tk.Label(left_frame, text="Select materials:", bg="#FFFDD0").pack(pady=5)
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

    tk.Label(left_frame, text="Output filename base (no extension):", bg="#FFFDD0").pack()
    filename_entry = tk.Entry(left_frame)
    filename_entry.insert(0, "my_pad_job")
    filename_entry.pack()

    mat_selector = ttk.Combobox(left_frame, values=[])
    mat_selector.pack()
    mat_selector.set('Material preview')
    mat_selector.config(state="readonly")

    def update_selector(mats):
        mat_selector['values'] = mats
        if mats:
            mat_selector.set(mats[0])
            preview_tool[0].show(parse_pad_list(pad_entry.get("1.0", tk.END)), mats[0])

    def on_preview():
        if not preview_shown[0]:
            try:
                width_mm = float(width_entry.get()) * 25.4
                height_mm = float(height_entry.get()) * 25.4
                pads = parse_pad_list(pad_entry.get("1.0", tk.END))
                selected_materials = [m for m, v in material_vars.items() if v.get()]
                if not selected_materials or not pads:
                    return
                preview_tool[0] = PadPreview(root, preview_canvas, width_mm, height_mm)
                update_selector(selected_materials)
                preview_shown[0] = True
            except:
                messagebox.showerror("Error", "Invalid sheet or pad data.")
        else:
            preview_canvas.delete("all")
            preview_shown[0] = False

    def on_selector_change(event):
        mats = mat_selector['values']
        sel = mat_selector.get()
        if sel in mats:
            preview_tool[0].show(parse_pad_list(pad_entry.get("1.0", tk.END)), sel)

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
        messagebox.showinfo("Done", "SVGs generated successfully.")

    mat_selector.bind("<<ComboboxSelected>>", on_selector_change)
    tk.Button(left_frame, text="Preview Layout", command=on_preview).pack(pady=5)
    tk.Button(left_frame, text="Generate SVGs", command=on_generate).pack(pady=5)
    root.mainloop()

if __name__ == '__main__':
    launch_gui()
