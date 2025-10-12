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
    "custom_hole_size": "4.0",
    "min_hole_size": 16.5,
    "felt_thickness": 3.175,
    "felt_thickness_unit": "mm",
    "engraving_on": True,
    "show_engraving_warning": True,
    "last_output_dir": "",
    "engraving_font_size": {
        "felt": 2.0,
        "card": 2.0,
        "leather": 2.0,
        "exact_size": 2.0
    },
    "engraving_location": {
        "felt": {"mode": "centered", "value": 0.0},
        "card": {"mode": "centered", "value": 0.0},
        "leather": {"mode": "from_outside", "value": 1.0},
        "exact_size": {"mode": "centered", "value": 0.0}
    },
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

class ConfirmationDialog(tk.Toplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x150")
        self.configure(bg="#F0EAD6")
        self.transient(parent)
        self.grab_set()

        self.result = False
        self.dont_show_again = tk.BooleanVar()

        tk.Label(self, text=message, wraplength=430, bg="#F0EAD6", justify="left").pack(padx=10, pady=10)
        
        checkbox_frame = tk.Frame(self, bg="#F0EAD6")
        checkbox_frame.pack(pady=5)
        tk.Checkbutton(checkbox_frame, text="Don't show this message again", variable=self.dont_show_again, bg="#F0EAD6").pack()
        
        button_frame = tk.Frame(self, bg="#F0EAD6")
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Yes, Proceed", command=self.on_yes).pack(side="left", padx=10)
        tk.Button(button_frame, text="No, Cancel", command=self.on_no).pack(side="left", padx=10)

        self.protocol("WM_DELETE_WINDOW", self.on_no)
        self.wait_window(self)

    def on_yes(self):
        self.result = True
        self.destroy()

    def on_no(self):
        self.result = False
        self.destroy()

class PadSVGGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stohrer Sax Pad SVG Generator")
        self.root.geometry("620x640")
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
        if self.hole_var.get() == "Custom":
            self.settings["custom_hole_size"] = self.custom_hole_entry.get()
        self.save_settings()
        self.root.destroy()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    loaded_settings = json.load(f)
                    settings = DEFAULT_SETTINGS.copy()
                    for key, default_value in DEFAULT_SETTINGS.items():
                        if key in loaded_settings:
                            if isinstance(default_value, dict):
                                settings[key] = default_value.copy()
                                settings[key].update(loaded_settings[key])
                            else:
                                settings[key] = loaded_settings[key]
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

        # Center Hole Selection UI
        hole_frame = tk.LabelFrame(options_frame, text="Center Hole", bg="#FFFDD0", padx=5, pady=5)
        hole_frame.pack(fill="x")
        self.hole_var = tk.StringVar(value=self.settings["hole_option"])
        
        tk.Radiobutton(hole_frame, text="None", variable=self.hole_var, value="No center holes", bg="#FFFDD0", command=self.toggle_custom_hole_entry).pack(side="left")
        tk.Radiobutton(hole_frame, text="3.0mm", variable=self.hole_var, value="3.0mm", bg="#FFFDD0", command=self.toggle_custom_hole_entry).pack(side="left")
        tk.Radiobutton(hole_frame, text="3.5mm", variable=self.hole_var, value="3.5mm", bg="#FFFDD0", command=self.toggle_custom_hole_entry).pack(side="left")
        tk.Radiobutton(hole_frame, text="Custom:", variable=self.hole_var, value="Custom", bg="#FFFDD0", command=self.toggle_custom_hole_entry).pack(side="left")
        
        self.custom_hole_entry = tk.Entry(hole_frame, width=6)
        self.custom_hole_entry.insert(0, self.settings.get("custom_hole_size", "4.0"))
        self.custom_hole_entry.pack(side="left", padx=2)
        tk.Label(hole_frame, text="mm", bg="#FFFDD0").pack(side="left")
        self.toggle_custom_hole_entry()


        # Sheet Size UI
        sheet_frame = tk.LabelFrame(options_frame, text="Sheet Size", bg="#FFFDD0", padx=5, pady=5)
        sheet_frame.pack(fill="x", pady=(10,0))
        # REMOVED columnconfigure weight to prevent expansion

        self.unit_label = tk.Label(sheet_frame, text=f"Width ({self.settings['units']}):", bg="#FFFDD0")
        self.unit_label.grid(row=0, column=0, sticky='w', padx=5)
        self.width_entry = tk.Entry(sheet_frame)
        self.width_entry.insert(0, self.settings["sheet_width"])
        self.width_entry.grid(row=0, column=1, sticky='w') # Changed to sticky='w'

        self.height_label = tk.Label(sheet_frame, text=f"Height ({self.settings['units']}):", bg="#FFFDD0")
        self.height_label.grid(row=1, column=0, sticky='w', padx=5)
        self.height_entry = tk.Entry(sheet_frame)
        self.height_entry.insert(0, self.settings["sheet_height"])
        self.height_entry.grid(row=1, column=1, sticky='w') # Changed to sticky='w'

        tk.Label(self.root, text="Output filename base (no extension):", bg="#FFFDD0").pack(pady=5)
        self.filename_entry = tk.Entry(self.root)
        self.filename_entry.insert(0, "my_pad_job")
        self.filename_entry.pack(padx=10) # REMOVED fill="x"

        tk.Button(self.root, text="Generate SVGs", command=self.on_generate, font=('Helvetica', 10, 'bold')).pack(pady=15)

    def toggle_custom_hole_entry(self):
        if self.hole_var.get() == "Custom":
            self.custom_hole_entry.config(state='normal')
        else:
            self.custom_hole_entry.config(state='disabled')

    def open_options_window(self):
        OptionsWindow(self.root, self.settings, self.update_ui_from_settings, self.save_settings)

    def open_color_window(self):
        LayerColorWindow(self.root, self.settings, self.save_settings)

    def update_ui_from_settings(self):
        self.unit_label.config(text=f"Width ({self.settings['units']}):")
        self.height_label.config(text=f"Height ({self.settings['units']}):")

    def get_hole_dia(self):
        hole_option = self.hole_var.get()
        if hole_option == "3.5mm": return 3.5
        if hole_option == "3.0mm": return 3.0
        if hole_option == "Custom":
            try:
                return float(self.custom_hole_entry.get())
            except (ValueError, TypeError):
                messagebox.showerror("Invalid Input", "Custom hole size must be a valid number.")
                return None
        return 0

    def on_generate(self):
        try:
            hole_dia = self.get_hole_dia()
            if hole_dia is None: return

            pads = self.parse_pad_list(self.pad_entry.get("1.0", tk.END))
            if not pads:
                messagebox.showerror("Error", "No valid pad sizes entered.")
                return

            # --- Pre-generation check for oversized engravings ---
            if self.settings.get("engraving_on", True):
                oversized_engravings = check_for_oversized_engravings(pads, self.material_vars, self.settings)
                if oversized_engravings and self.settings.get("show_engraving_warning", True):
                    message = "Warning: The current font size is too large for some pads and the engraving will be skipped:\n\n"
                    for mat, sizes in oversized_engravings.items():
                        message += f"- {mat.replace('_', ' ').capitalize()}: {', '.join(map(str, sorted(sizes)))}\n"
                    message += "\nDo you want to proceed?"

                    dialog = ConfirmationDialog(self.root, "Engraving Size Warning", message)
                    if not dialog.result:
                        return # User clicked No/Cancel
                    if dialog.dont_show_again.get():
                        self.settings["show_engraving_warning"] = False

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


            base = self.filename_entry.get().strip()
            if not base:
                messagebox.showerror("Error", "Please enter a base filename.")
                return
            
            for material, var in self.material_vars.items():
                if var.get() and not can_all_pads_fit(pads, material, width_mm, height_mm, self.settings):
                    messagebox.showerror("Nesting Error", f"Could not fit all '{material.replace('_',' ')}' pieces on the specified sheet size.")
                    return

            save_dir = filedialog.askdirectory(title="Select Folder to Save SVGs", initialdir=self.settings.get("last_output_dir", ""))
            if not save_dir:
                return
            
            self.settings["last_output_dir"] = save_dir # Save new path

            files_generated = False
            for material, var in self.material_vars.items():
                if var.get():
                    filename = os.path.join(save_dir, f"{base}_{material}.svg")
                    generate_svg(pads, material, width_mm, height_mm, filename, hole_dia, self.settings)
                    files_generated = True
            
            if files_generated:
                self.save_settings() # Save all settings, including new path
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
        self.top.geometry("500x700")
        self.top.configure(bg="#F0EAD6")
        self.top.transient(parent)
        self.top.grab_set()
        
        # Create a canvas and a scrollbar
        self.canvas = tk.Canvas(self.top, bg="#F0EAD6", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.top, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F0EAD6", padx=10, pady=10)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.top.bind('<MouseWheel>', self._on_mousewheel)


        # --- Sizing variables ---
        self.unit_var = tk.StringVar(value=self.settings["units"])
        self.felt_offset_var = tk.DoubleVar(value=self.settings["felt_offset"])
        self.card_offset_var = tk.DoubleVar(value=self.settings["card_to_felt_offset"])
        self.leather_mult_var = tk.DoubleVar(value=self.settings["leather_wrap_multiplier"])
        self.min_hole_size_var = tk.DoubleVar(value=self.settings["min_hole_size"])
        self.felt_thickness_var = tk.DoubleVar(value=self.settings["felt_thickness"])
        self.felt_thickness_unit_var = tk.StringVar(value=self.settings["felt_thickness_unit"])
        
        # --- Engraving variables ---
        self.engraving_on_var = tk.BooleanVar(value=self.settings["engraving_on"])
        self.engraving_font_size_vars = {}
        self.engraving_loc_vars = {}

        self.create_option_widgets()
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_option_widgets(self):
        main_frame = self.scrollable_frame
        
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
        
        felt_thickness_frame = tk.Frame(rules_frame, bg="#F0EAD6")
        felt_thickness_frame.grid(row=4, column=0, columnspan=2, sticky='w', pady=2)
        tk.Label(felt_thickness_frame, text="Felt Thickness:", bg="#F0EAD6").pack(side="left")
        tk.Entry(felt_thickness_frame, textvariable=self.felt_thickness_var, width=10).pack(side="left", padx=5)
        tk.Radiobutton(felt_thickness_frame, text="in", variable=self.felt_thickness_unit_var, value="in", bg="#F0EAD6").pack(side="left")
        tk.Radiobutton(felt_thickness_frame, text="mm", variable=self.felt_thickness_unit_var, value="mm", bg="#F0EAD6").pack(side="left")

        # --- Engraving Section ---
        engraving_frame = tk.LabelFrame(main_frame, text="Engraving Settings", bg="#F0EAD6", padx=5, pady=5)
        engraving_frame.pack(fill="x", pady=5)
        
        tk.Checkbutton(engraving_frame, text="Show Size Label (Engraving)", variable=self.engraving_on_var, bg="#F0EAD6").pack(anchor='w')

        font_size_frame = tk.LabelFrame(engraving_frame, text="Font Sizes (mm)", bg="#F0EAD6", padx=5, pady=5)
        font_size_frame.pack(fill='x', pady=5)
        
        materials = ['felt', 'card', 'leather', 'exact_size']
        for i, material in enumerate(materials):
            tk.Label(font_size_frame, text=f"{material.replace('_', ' ').capitalize()}:", bg="#F0EAD6").grid(row=i, column=0, sticky='w', padx=5, pady=2)
            font_size_var = tk.DoubleVar(value=self.settings["engraving_font_size"].get(material, 2.0))
            self.engraving_font_size_vars[material] = font_size_var
            tk.Entry(font_size_frame, textvariable=font_size_var, width=8).grid(row=i, column=1, sticky='w', padx=5, pady=2)


        engraving_loc_frame = tk.LabelFrame(main_frame, text="Engraving Placement", bg="#F0EAD6", padx=5, pady=5)
        engraving_loc_frame.pack(fill="x", pady=5)
        
        for material in materials:
            frame = tk.Frame(engraving_loc_frame, bg="#F0EAD6")
            frame.pack(fill='x', pady=2)
            tk.Label(frame, text=material.replace('_', ' ').capitalize() + ":", bg="#F0EAD6", width=10, anchor='w').pack(side="left")

            mode_var = tk.StringVar(value=self.settings["engraving_location"][material]['mode'])
            val_var = tk.DoubleVar(value=self.settings["engraving_location"][material]['value'])
            self.engraving_loc_vars[material] = {'mode': mode_var, 'value': val_var}

            tk.Radiobutton(frame, text="from outside", variable=mode_var, value="from_outside", bg="#F0EAD6").pack(side="left")
            tk.Radiobutton(frame, text="from inside", variable=mode_var, value="from_inside", bg="#F0EAD6").pack(side="left")
            tk.Radiobutton(frame, text="centered", variable=mode_var, value="centered", bg="#F0EAD6").pack(side="left")
            
            tk.Entry(frame, textvariable=val_var, width=6).pack(side="left", padx=5)
            tk.Label(frame, text="mm", bg="#F0EAD6").pack(side="left")


        button_frame = tk.Frame(main_frame, bg="#F0EAD6")
        button_frame.pack(side="bottom", pady=10, fill='x')
        tk.Button(button_frame, text="Save", command=self.save_options).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=self.top.destroy).pack(side="left", padx=10)
        tk.Button(button_frame, text="Revert to Defaults", command=self.revert_to_defaults).pack(side="right", padx=10)

    def save_options(self):
        # Sizing
        self.settings["units"] = self.unit_var.get()
        self.settings["felt_offset"] = self.felt_offset_var.get()
        self.settings["card_to_felt_offset"] = self.card_offset_var.get()
        self.settings["leather_wrap_multiplier"] = self.leather_mult_var.get()
        self.settings["min_hole_size"] = self.min_hole_size_var.get()
        self.settings["felt_thickness"] = self.felt_thickness_var.get()
        self.settings["felt_thickness_unit"] = self.felt_thickness_unit_var.get()
        
        # Engraving
        self.settings["engraving_on"] = self.engraving_on_var.get()
        for material, var in self.engraving_font_size_vars.items():
            self.settings["engraving_font_size"][material] = var.get()

        for material, vars in self.engraving_loc_vars.items():
            self.settings["engraving_location"][material]['mode'] = vars['mode'].get()
            self.settings["engraving_location"][material]['value'] = vars['value'].get()

        self.save_callback()
        self.update_callback()
        self.top.destroy()

    def revert_to_defaults(self):
        if messagebox.askyesno("Revert to Defaults", "Are you sure you want to revert all settings to their original defaults?"):
            # Sizing
            self.unit_var.set(DEFAULT_SETTINGS["units"])
            self.felt_offset_var.set(DEFAULT_SETTINGS["felt_offset"])
            self.card_offset_var.set(DEFAULT_SETTINGS["card_to_felt_offset"])
            self.leather_mult_var.set(DEFAULT_SETTINGS["leather_wrap_multiplier"])
            self.min_hole_size_var.set(DEFAULT_SETTINGS["min_hole_size"])
            self.felt_thickness_var.set(DEFAULT_SETTINGS["felt_thickness"])
            self.felt_thickness_unit_var.set(DEFAULT_SETTINGS["felt_thickness_unit"])
            
            # Engraving
            self.engraving_on_var.set(DEFAULT_SETTINGS["engraving_on"])
            for material, var in self.engraving_font_size_vars.items():
                 var.set(DEFAULT_SETTINGS["engraving_font_size"][material])
            
            for material, vars in self.engraving_loc_vars.items():
                 vars['mode'].set(DEFAULT_SETTINGS["engraving_location"][material]['mode'])
                 vars['value'].set(DEFAULT_SETTINGS["engraving_location"][material]['value'])


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
def get_disc_diameter(pad_size, material, settings):
    if material == 'felt': return pad_size - settings["felt_offset"]
    if material == 'card': return pad_size - (settings["felt_offset"] + settings["card_to_felt_offset"])
    if material == 'leather':
        wrap = leather_back_wrap(pad_size, settings["leather_wrap_multiplier"])
        felt_thickness_mm = get_felt_thickness_mm(settings)
        diameter = pad_size + 2 * (felt_thickness_mm + wrap)
        return round(diameter * 2) / 2
    if material == 'exact_size': return pad_size
    return 0

def check_for_oversized_engravings(pads, material_vars, settings):
    oversized = {}
    for material, var in material_vars.items():
        if not var.get(): continue
        
        font_size = settings["engraving_font_size"].get(material, 2.0)
        oversized_sizes = set()

        for pad in pads:
            pad_size = pad['size']
            diameter = get_disc_diameter(pad_size, material, settings)
            radius = diameter / 2
            # A simple heuristic: check if font height is > 80% of the radius
            if font_size >= radius * 0.8:
                oversized_sizes.add(pad_size)
        
        if oversized_sizes:
            oversized[material] = oversized_sizes
    return oversized


def leather_back_wrap(pad_size, multiplier):
    base_wrap = 0
    if pad_size >= 45:
        base_wrap = 3.2
    elif pad_size >= 12:
        base_wrap = 1.2 + (pad_size - 12) * (2.0 / 33.0)
    elif pad_size >= 6:
        base_wrap = 1.0 + (pad_size - 6) * (0.2 / 6.0)
    else:
        base_wrap = 1.0
    return base_wrap * multiplier

def should_have_center_hole(pad_size, hole_dia, settings):
    min_size = settings.get("min_hole_size", 16.5)
    return hole_dia > 0 and pad_size >= min_size

def get_felt_thickness_mm(settings):
    thickness = settings.get("felt_thickness", 3.175)
    if settings.get("felt_thickness_unit") == "in":
        return thickness * 25.4
    return thickness

def can_all_pads_fit(pads, material, width_mm, height_mm, settings):
    spacing_mm = 1.0
    discs = []
    
    for pad in pads:
        pad_size, qty = pad['size'], pad['qty']
        diameter = get_disc_diameter(pad_size, material, settings)
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

def generate_svg(pads, material, width_mm, height_mm, filename, hole_dia_preset, settings):
    spacing_mm = 1.0
    discs = []

    for pad in pads:
        pad_size, qty = pad['size'], pad['qty']
        diameter = get_disc_diameter(pad_size, material, settings)
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
        if should_have_center_hole(pad_size, hole_dia_preset, settings):
            hole_dia = hole_dia_preset

        if hole_dia > 0:
            dwg.add(dwg.circle(center=(f"{cx}mm", f"{cy}mm"), r=f"{hole_dia / 2}mm", stroke=layer_colors[f'{material}_center_hole'], fill='none', stroke_width='0.1mm'))

        font_size = settings.get("engraving_font_size", {}).get(material, 2.0)
        # Final check to prevent drawing oversized engravings
        if settings.get("engraving_on", True) and (font_size < r * 0.8):
            engraving_settings = settings["engraving_location"][material]
            mode = engraving_settings['mode']
            value = engraving_settings['value']
            
            engraving_y = 0
            if mode == 'from_outside':
                engraving_y = cy - (r - value)
            elif mode == 'from_inside':
                hole_r = hole_dia / 2 if hole_dia > 0 else 0
                engraving_y = cy - (hole_r + value)
            else: # centered
                hole_r = hole_dia / 2 if hole_dia > 0 else 1.75 # Use a small default if no hole for centering
                offset_from_center = (r + hole_r) / 2
                engraving_y = cy - offset_from_center

            # Adjust Y for better visual centering
            vertical_adjust = font_size * 0.35
            
            dwg.add(dwg.text(f"{pad_size:.1f}".rstrip('0').rstrip('.'),
                             insert=(f"{cx}mm", f"{engraving_y + vertical_adjust}mm"),
                             text_anchor="middle",
                             font_size=f"{font_size}mm",
                             fill=layer_colors[f'{material}_engraving']))

    dwg.save()

if __name__ == '__main__':
    root = tk.Tk()
    app = PadSVGGeneratorApp(root)
    root.mainloop()
