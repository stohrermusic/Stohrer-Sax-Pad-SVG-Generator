import svgwrite
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import json

# --- Lightburn Color Palette ---
LIGHTBURN_COLORS = [
    ("00 - Black", "#000000"), ("01 - Blue", "#0000FF"), ("02 - Red", "#FF0000"),
    ("03 - Green", "#00E000"), ("04 - Yellow", "#D0D000"), ("05 - Orange", "#FF8000"),
    ("06 - Cyan", "#00E0E0"), ("07 - Magenta", "#FF00FF"), ("08 - Light Gray", "#B4B4B4"),
    ("09 - Dark Blue", "#0000A0"), ("10 - Dark Red", "#A00000"), ("11 - Dark Green", "#00A000"),
    ("12 - Dark Yellow", "#A0A000"), ("13 - Brown", "#C08000"), ("14 - Light Blue", "#00A0FF"),
    ("15 - Dark Magenta", "#A000A0"), ("16 - Gray", "#808080"), ("17 - Periwinkle", "#7D87B9"),
    ("18 - Rose", "#BB7784"), ("19 - Cornflower", "#4A6FE3"), ("20 - Cerise", "#D33F6A"),
    ("21 - Light Green", "#8CD78C"), ("22 - Tan", "#F0B98D"), ("23 - Pink", "#F6C4E1"),
    ("24 - Lavender", "#FA9ED4"), ("25 - Purple", "#500A78"), ("26 - Ochre", "#B45A00"),
    ("27 - Teal", "#004754"), ("28 - Mint", "#86FA88"), ("29 - Pale Yellow", "#FFDB66")
]

# --- Default Configuration ---
DEFAULT_SETTINGS = {
    "units": "in",
    "felt_offset": 0.75,
    "card_to_felt_offset": 2.0,
    "leather_wrap_multiplier": 1.00,
    "sheet_width": "13.5",
    "sheet_height": "10",
    "hole_option": "3.5mm",
    "min_hole_size": 16.5,
    "layer_colors": {
        'felt_outline': '#000000',
        'felt_center_hole': '#0000A0',
        'felt_engraving': '#A00000',
        'card_outline': '#0000FF',
        'card_center_hole': '#00A0FF',
        'card_engraving': '#A000A0',
        'leather_outline': '#FF0000',
        'leather_center_hole': '#00E000',
        'leather_engraving': '#FF8000',
        'exact_size_outline': '#D0D000',
        'exact_size_center_hole': '#A0A000',
        'exact_size_engraving': '#BB7784'
    }
}

PRESET_FILE = "pad_presets.json"
SETTINGS_FILE = "app_settings.json"

class PadSVGGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sax Pad SVG Generator (beta)")
        self.root.geometry("620x640") # Increased height slightly for new checkbox
        self.root.configure(bg="#FFFDD0")

        self.settings = self.load_settings()
        self.presets = self.load_presets()

        self.create_widgets()
        self.create_menu()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self):
        self.settings["sheet_width"] = self.width_entry.get()
        self.settings["sheet_height"] = self.height_entry.get()
        self.settings["hole_option"] = self.hole_var.get()
        self.save_settings()
        self.root.destroy()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    loaded_settings = json.load(f)
                    settings = DEFAULT_SETTINGS.copy()
                    for key, value in loaded_settings.items():
                        if key in settings and isinstance(settings[key], dict) and isinstance(value, dict):
                            settings[key].update(value)
                        else:
                            settings[key] = value
                    return settings
            except (json.JSONDecodeError, TypeError):
                return DEFAULT_SETTINGS.copy()
        return DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error Saving Settings", f"Could not save settings:\n{e}")

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Sizing Rules...", command=self.open_options_window)
        options_menu.add_command(label="Layer Colors...", command=self.open_color_window)
        options_menu.add_separator()
        options_menu.add_command(label="Exit", command=self.on_exit)

    def create_widgets(self):
        tk.Label(self.root, text="Enter pad sizes (e.g. 42.0x3):", bg="#FFFDD0").pack(pady=5)
        self.pad_entry = tk.Text(self.root, height=10)
        self.pad_entry.pack(fill="x", padx=10)

        preset_frame = tk.Frame(self.root, bg="#FFFDD0")
        preset_frame.pack(pady=10)
        
        tk.Button(preset_frame, text="Save as Preset", command=self.on_save_preset).pack(side="left", padx=5)
        
        preset_names = list(self.presets.keys())
        self.preset_var = tk.StringVar()
        self.preset_menu = ttk.Combobox(preset_frame, textvariable=self.preset_var, values=preset_names, state="readonly", width=20)
        self.preset_menu.set("Load Preset")
        self.preset_menu.pack(side="left", padx=5)
        self.preset_menu.bind("<<ComboboxSelected>>", lambda e: self.on_load_preset(self.preset_var.get()))
        
        tk.Button(preset_frame, text="Delete Preset", command=self.on_delete_preset).pack(side="left", padx=5)

        tk.Label(self.root, text="Select materials:", bg="#FFFDD0").pack(pady=5)
        self.material_vars = {
            'felt': tk.BooleanVar(value=True), 
            'card': tk.BooleanVar(value=True), 
            'leather': tk.BooleanVar(value=True),
            'exact_size': tk.BooleanVar(value=False)
        }
        for m in self.material_vars:
            tk.Checkbutton(self.root, text=m.replace('_', ' ').capitalize(), variable=self.material_vars[m], bg="#FFFDD0").pack(anchor='w', padx=20)

        options_frame = tk.Frame(self.root, bg="#FFFDD0")
        options_frame.pack(pady=10, fill='x', padx=10)
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(3, weight=1)

        tk.Label(options_frame, text="Center hole:", bg="#FFFDD0").grid(row=0, column=0, sticky='w', padx=5)
        self.hole_var = tk.StringVar(value=self.settings["hole_option"])
        tk.OptionMenu(options_frame, self.hole_var, "No center holes", "3.5mm", "3.0mm").grid(row=0, column=1, sticky='w')

        self.unit_label = tk.Label(options_frame, text=f"Sheet width ({self.settings['units']}):", bg="#FFFDD0")
        self.unit_label.grid(row=1, column=0, sticky='w', padx=5)
        self.width_entry = tk.Entry(options_frame)
        self.width_entry.insert(0, self.settings["sheet_width"])
        self.width_entry.grid(row=1, column=1, sticky='ew')

        self.height_label = tk.Label(options_frame, text=f"Sheet height ({self.settings['units']}):", bg="#FFFDD0")
        self.height_label.grid(row=2, column=0, sticky='w', padx=5)
        self.height_entry = tk.Entry(options_frame)
        self.height_entry.insert(0, self.settings["sheet_height"])
        self.height_entry.grid(row=2, column=1, sticky='ew')

        tk.Label(self.root, text="Output filename base (no extension):", bg="#FFFDD0").pack(pady=5)
        self.filename_entry = tk.Entry(self.root)
        self.filename_entry.insert(0, "my_pad_job")
        self.filename_entry.pack(fill="x", padx=10)

        tk.Button(self.root, text="Generate SVGs", command=self.on_generate, font=('Helvetica', 10, 'bold')).pack(pady=15)

    def open_options_window(self):
        OptionsWindow(self.root, self.settings, self.update_ui_from_settings, self.save_settings)

    def open_color_window(self):
        LayerColorWindow(self.root, self.settings, self.save_settings)

    def update_ui_from_settings(self):
        self.unit_label.config(text=f"Sheet width ({self.settings['units']}):")
        self.height_label.config(text=f"Sheet height ({self.settings['units']}):")

    def on_generate(self):
        try:
            width_val = float(self.width_entry.get())
            height_val = float(self.height_entry.get())
            
            if self.settings['units'] == 'in':
                width_mm, height_mm = width_val * 25.4, height_val * 25.4
            elif self.settings['units'] == 'cm':
                width_mm, height_mm = width_val * 10, height_val * 10
            elif self.settings['units'] == 'mm':
                width_mm, height_mm = width_val, height_val
            else:
                messagebox.showerror("Error", f"Unknown unit '{self.settings['units']}' in settings.")
                return

            pads = self.parse_pad_list(self.pad_entry.get("1.0", tk.END))
            if not pads:
                messagebox.showerror("Error", "No valid pad sizes entered.")
                return

            base = self.filename_entry.get().strip()
            if not base:
                messagebox.showerror("Error", "Please enter a base filename.")
                return
            
            for material, var in self.material_vars.items():
                if var.get() and not can_all_pads_fit(pads, material, width_mm, height_mm, self.settings):
                    messagebox.showerror("Nesting Error", f"Could not fit all '{material.replace('_',' ')}' pieces on the specified sheet size.")
                    return

            save_dir = filedialog.askdirectory(title="Select Folder to Save SVGs")
            if not save_dir:
                return

            files_generated = False
            for material, var in self.material_vars.items():
                if var.get():
                    filename = os.path.join(save_dir, f"{base}_{material}.svg")
                    generate_svg(pads, material, width_mm, height_mm, filename, self.hole_var.get(), self.settings)
                    files_generated = True
            
            if files_generated:
                messagebox.showinfo("Done", "SVGs generated successfully.")
            else:
                messagebox.showwarning("No Materials Selected", "Please select at least one material.")

        except Exception as e:
            print(f"An error occurred during SVG generation: {e}")
            messagebox.showerror("An Error Occurred", f"Something went wrong during generation:\n\n{e}")

    def parse_pad_list(self, pad_input):
        pad_list = []
        for line in pad_input.strip().splitlines():
            try:
                size, qty = map(float, line.strip().lower().split('x'))
                pad_list.append({'size': size, 'qty': int(qty)})
            except ValueError:
                continue
        return pad_list

    def load_presets(self):
        if os.path.exists(PRESET_FILE):
            try:
                with open(PRESET_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def on_save_preset(self):
        name = simpledialog.askstring("Save Preset", "Enter a name for this preset:")
        if name:
            pad_text = self.pad_entry.get("1.0", tk.END)
            if not pad_text.strip():
                messagebox.showwarning("Save Preset", "Cannot save an empty pad list.")
                return
            
            self.presets[name] = pad_text
            try:
                with open(PRESET_FILE, 'w') as f:
                    json.dump(self.presets, f, indent=2)
                self.preset_menu['values'] = list(self.presets.keys())
                messagebox.showinfo("Preset Saved", f"Preset '{name}' saved successfully.")
            except Exception as e:
                messagebox.showerror("Error Saving Preset", str(e))

    def on_load_preset(self, selected_name):
        if selected_name in self.presets:
            self.pad_entry.delete("1.0", tk.END)
            self.pad_entry.insert(tk.END, self.presets[selected_name])

    def on_delete_preset(self):
        selected = self.preset_var.get()
        if selected and selected != "Load Preset":
            if messagebox.askyesno("Delete Preset", f"Are you sure you want to delete the preset '{selected}'?"):
                del self.presets[selected]
                try:
                    with open(PRESET_FILE, 'w') as f:
                        json.dump(self.presets, f, indent=2)
                    self.preset_menu['values'] = list(self.presets.keys())
                    self.preset_menu.set("Load Preset")
                    self.pad_entry.delete("1.0", tk.END)
                    messagebox.showinfo("Preset Deleted", f"Preset '{selected}' deleted.")
                except Exception as e:
                    messagebox.showerror("Error Deleting Preset", str(e))

class OptionsWindow:
    def __init__(self, parent, settings, update_callback, save_callback):
        self.settings = settings
        self.update_callback = update_callback
        self.save_callback = save_callback
        
        self.top = tk.Toplevel(parent)
        self.top.title("Sizing Rules")
        self.top.geometry("450x280")
        self.top.configure(bg="#F0EAD6")
        self.top.transient(parent)
        self.top.grab_set()

        self.unit_var = tk.StringVar(value=self.settings["units"])
        self.felt_offset_var = tk.DoubleVar(value=self.settings["felt_offset"])
        self.card_offset_var = tk.DoubleVar(value=self.settings["card_to_felt_offset"])
        self.leather_mult_var = tk.DoubleVar(value=self.settings["leather_wrap_multiplier"])
        self.min_hole_size_var = tk.DoubleVar(value=self.settings["min_hole_size"])

        main_frame = tk.Frame(self.top, bg="#F0EAD6", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        unit_frame = tk.LabelFrame(main_frame, text="Sheet Units", bg="#F0EAD6", padx=5, pady=5)
        unit_frame.pack(fill="x", pady=5)
        tk.Radiobutton(unit_frame, text="Inches (in)", variable=self.unit_var, value="in", bg="#F0EAD6").pack(side="left", padx=5)
        tk.Radiobutton(unit_frame, text="Centimeters (cm)", variable=self.unit_var, value="cm", bg="#F0EAD6").pack(side="left", padx=5)
        tk.Radiobutton(unit_frame, text="Millimeters (mm)", variable=self.unit_var, value="mm", bg="#F0EAD6").pack(side="left", padx=5)

        rules_frame = tk.LabelFrame(main_frame, text="Sizing Rules (Advanced)", bg="#F0EAD6", padx=5, pady=5)
        rules_frame.pack(fill="x", pady=5)
        rules_frame.columnconfigure(1, weight=1)

        tk.Label(rules_frame, text="Felt Diameter Reduction (mm):", bg="#F0EAD6").grid(row=0, column=0, sticky='w', pady=2)
        tk.Entry(rules_frame, textvariable=self.felt_offset_var, width=10).grid(row=0, column=1, sticky='w', pady=2)

        tk.Label(rules_frame, text="Card Additional Reduction (mm):", bg="#F0EAD6").grid(row=1, column=0, sticky='w', pady=2)
        tk.Entry(rules_frame, textvariable=self.card_offset_var, width=10).grid(row=1, column=1, sticky='w', pady=2)

        tk.Label(rules_frame, text="Leather Wrap Multiplier (1.00=default):", bg="#F0EAD6").grid(row=2, column=0, sticky='w', pady=2)
        tk.Entry(rules_frame, textvariable=self.leather_mult_var, width=10).grid(row=2, column=1, sticky='w', pady=2)

        tk.Label(rules_frame, text="Min. Pad Size for Hole (mm):", bg="#F0EAD6").grid(row=3, column=0, sticky='w', pady=2)
        tk.Entry(rules_frame, textvariable=self.min_hole_size_var, width=10).grid(row=3, column=1, sticky='w', pady=2)

        button_frame = tk.Frame(main_frame, bg="#F0EAD6")
        button_frame.pack(side="bottom", pady=10, fill='x')
        tk.Button(button_frame, text="Save", command=self.save_options).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=self.top.destroy).pack(side="left", padx=10)
        tk.Button(button_frame, text="Revert to Defaults", command=self.revert_to_defaults).pack(side="right", padx=10)

    def save_options(self):
        self.settings["units"] = self.unit_var.get()
        self.settings["felt_offset"] = self.felt_offset_var.get()
        self.settings["card_to_felt_offset"] = self.card_offset_var.get()
        self.settings["leather_wrap_multiplier"] = self.leather_mult_var.get()
        self.settings["min_hole_size"] = self.min_hole_size_var.get()
        
        self.save_callback()
        self.update_callback()
        self.top.destroy()

    def revert_to_defaults(self):
        if messagebox.askyesno("Revert to Defaults", "Are you sure you want to revert all settings to their original defaults?"):
            self.unit_var.set(DEFAULT_SETTINGS["units"])
            self.felt_offset_var.set(DEFAULT_SETTINGS["felt_offset"])
            self.card_offset_var.set(DEFAULT_SETTINGS["card_to_felt_offset"])
            self.leather_mult_var.set(DEFAULT_SETTINGS["leather_wrap_multiplier"])
            self.min_hole_size_var.set(DEFAULT_SETTINGS["min_hole_size"])

class LayerColorWindow:
    def __init__(self, parent, settings, save_callback):
        self.settings = settings
        self.save_callback = save_callback
        
        self.top = tk.Toplevel(parent)
        self.top.title("Layer Color Mapping")
        self.top.geometry("450x420")
        self.top.configure(bg="#F0EAD6")
        self.top.transient(parent)
        self.top.grab_set()

        self.color_map = {name: hex_val for name, hex_val in LIGHTBURN_COLORS}
        color_names = list(self.color_map.keys())
        self.hex_to_name_map = {hex_val: name for name, hex_val in LIGHTBURN_COLORS}

        self.color_vars = {}

        main_frame = tk.Frame(self.top, bg="#F0EAD6", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(1, weight=1)

        layer_map_keys = [
            'felt_outline', 'felt_center_hole', 'felt_engraving',
            'card_outline', 'card_center_hole', 'card_engraving',
            'leather_outline', 'leather_center_hole', 'leather_engraving',
            'exact_size_outline', 'exact_size_center_hole', 'exact_size_engraving'
        ]
        
        for i, key in enumerate(layer_map_keys):
            label_text = key.replace('_', ' ').capitalize() + ":"
            tk.Label(main_frame, text=label_text, bg="#F0EAD6").grid(row=i, column=0, sticky='w', pady=3)
            
            var = tk.StringVar()
            current_hex = self.settings["layer_colors"].get(key, "#000000")
            current_name = self.hex_to_name_map.get(current_hex, color_names[0])
            var.set(current_name)
            
            combo = ttk.Combobox(main_frame, textvariable=var, values=color_names, state="readonly")
            combo.grid(row=i, column=1, sticky='ew', padx=5)
            self.color_vars[key] = var

        button_frame = tk.Frame(main_frame, bg="#F0EAD6")
        button_frame.grid(row=len(layer_map_keys), column=0, columnspan=2, pady=20)
        tk.Button(button_frame, text="Save", command=self.save_colors).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=self.top.destroy).pack(side="left", padx=10)

    def save_colors(self):
        for key, var in self.color_vars.items():
            selected_name = var.get()
            self.settings["layer_colors"][key] = self.color_map[selected_name]
        
        self.save_callback()
        self.top.destroy()

# --- Core SVG Generation Logic ---

def leather_back_wrap(pad_size, multiplier):
    base_wrap = 0
    if pad_size <= 10: base_wrap = 1.3
    elif pad_size <= 15: base_wrap = 1.3 + (pad_size - 10) * (0.7 / 5.0)
    elif pad_size <= 40: base_wrap = 2.0 + (pad_size - 15) * (1.5 / 25.0)
    else: base_wrap = 3.5
    return base_wrap * multiplier

def should_have_center_hole(pad_size, hole_option, settings):
    min_size = settings.get("min_hole_size", 16.5)
    return hole_option != "No center holes" and pad_size >= min_size

def can_all_pads_fit(pads, material, width_mm, height_mm, settings):
    spacing_mm = 1.0
    discs = []
    
    for pad in pads:
        pad_size, qty = pad['size'], pad['qty']
        diameter = 0
        if material == 'felt': diameter = pad_size - settings["felt_offset"]
        elif material == 'card': diameter = pad_size - (settings["felt_offset"] + settings["card_to_felt_offset"])
        elif material == 'leather':
            wrap = leather_back_wrap(pad_size, settings["leather_wrap_multiplier"])
            diameter = pad_size + 2 * (3.175 + wrap)
            diameter = round(diameter * 2) / 2
        elif material == 'exact_size':
            diameter = pad_size
        else: continue
        for _ in range(qty): discs.append((pad_size, diameter))

    discs.sort(key=lambda x: -x[1])
    placed = []
    for _, dia in discs:
        r = dia / 2
        placed_successfully = False
        y = spacing_mm
        while y + dia + spacing_mm <= height_mm and not placed_successfully:
            x = spacing_mm
            while x + dia + spacing_mm <= width_mm:
                cx, cy = x + r, y + r
                is_collision = any((cx - px)**2 + (cy - py)**2 < (r + pr + spacing_mm)**2 for _, px, py, pr in placed)
                if not is_collision:
                    placed.append((None, cx, cy, r))
                    placed_successfully = True
                    break
                x += 1
            y += 1
    
    return len(placed) == len(discs)

def generate_svg(pads, material, width_mm, height_mm, filename, hole_option, settings):
    spacing_mm = 1.0
    discs = []

    for pad in pads:
        pad_size, qty = pad['size'], pad['qty']
        diameter = 0
        if material == 'felt': diameter = pad_size - settings["felt_offset"]
        elif material == 'card': diameter = pad_size - (settings["felt_offset"] + settings["card_to_felt_offset"])
        elif material == 'leather':
            wrap = leather_back_wrap(pad_size, settings["leather_wrap_multiplier"])
            diameter = pad_size + 2 * (3.175 + wrap)
            diameter = round(diameter * 2) / 2
        elif material == 'exact_size':
            diameter = pad_size
        else: continue
        for _ in range(qty): discs.append((pad_size, diameter))

    discs.sort(key=lambda x: -x[1])
    placed = []
    for pad_size, dia in discs:
        r = dia / 2
        placed_successfully = False
        y = spacing_mm
        while y + dia + spacing_mm <= height_mm and not placed_successfully:
            x = spacing_mm
            while x + dia + spacing_mm <= width_mm:
                cx, cy = x + r, y + r
                is_collision = any((cx - px)**2 + (cy - py)**2 < (r + pr + spacing_mm)**2 for _, px, py, pr in placed)
                if not is_collision:
                    placed.append((pad_size, cx, cy, r))
                    placed_successfully = True
                    break
                x += 1
            y += 1

    dwg = svgwrite.Drawing(filename, size=(f"{width_mm}mm", f"{height_mm}mm"), profile='tiny')
    layer_colors = settings.get("layer_colors", DEFAULT_SETTINGS["layer_colors"])

    for pad_size, cx, cy, r in placed:
        dwg.add(dwg.circle(center=(f"{cx}mm", f"{cy}mm"), r=f"{r}mm", stroke=layer_colors[f'{material}_outline'], fill='none', stroke_width='0.1mm'))

        hole_dia = 0
        if hole_option == "3.5mm" and should_have_center_hole(pad_size, hole_option, settings): hole_dia = 3.5
        elif hole_option == "3.0mm" and should_have_center_hole(pad_size, hole_option, settings): hole_dia = 3.0

        if hole_dia > 0:
            dwg.add(dwg.circle(center=(f"{cx}mm", f"{cy}mm"), r=f"{hole_dia / 2}mm", stroke=layer_colors[f'{material}_center_hole'], fill='none', stroke_width='0.1mm'))

        engraving_y = 0
        if material == 'leather': 
            engraving_y = cy - (r - 1.0)
        else:
            offset_from_center = (r + (hole_dia / 2 if hole_dia > 0 else 1.75)) / 2
            engraving_y = cy - offset_from_center
        
        vertical_adjust = 0.7 
        
        dwg.add(dwg.text(f"{pad_size:.1f}".rstrip('0').rstrip('.'),
                         insert=(f"{cx}mm", f"{engraving_y + vertical_adjust}mm"),
                         text_anchor="middle",
                         font_size="2mm",
                         fill=layer_colors[f'{material}_engraving']))

    dwg.save()

if __name__ == '__main__':
    root = tk.Tk()
    app = PadSVGGeneratorApp(root)
    root.mainloop()


