"""Cross-platform GUI for Pycamo."""

from __future__ import annotations

from pathlib import Path
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

try:
    from . import Camologic as camologic
except ImportError:
    import Camologic as camologic


HEX_COLOR_RE = re.compile(r"^[0-9a-fA-F]{6}$")
MAX_COLORS = 5

REFERENCE_PRESETS = {
    "Custom (Manual)": None,
    "CADPAT (Temperate Woodland)": {
        "colors": ["25301f", "3e4a2a", "5c6840", "7e7f58", "1e2519"],
        "ratios": [18.0, 25.0, 24.0, 19.0, 14.0],
        "c_value": "1.8",
        "pixel_style": True,
        "pixel_size": "4",
        "num_colors": "5",
    },
    "CADPAT (Arid Region)": {
        "colors": ["6d684c", "91886b", "b8a98a", "d2c4a5", "4f4938"],
        "ratios": [19.0, 24.0, 27.0, 18.0, 12.0],
        "c_value": "1.7",
        "pixel_style": True,
        "pixel_size": "4",
        "num_colors": "5",
    },
    "UCP (Urban Gray)": {
        "colors": ["585c59", "767a74", "8e948a", "aab0a5", "c6cabf"],
        "ratios": [22.0, 25.0, 22.0, 18.0, 13.0],
        "c_value": "1.55",
        "pixel_style": True,
        "pixel_size": "5",
        "num_colors": "5",
    },
    "MARPAT (Woodland)": {
        "colors": ["2b3426", "4b5a3f", "687a4f", "8e8b63", "191f17"],
        "ratios": [18.0, 24.0, 26.0, 18.0, 14.0],
        "c_value": "1.75",
        "pixel_style": True,
        "pixel_size": "4",
        "num_colors": "5",
    },
    "AOR2 (Navy Woodland)": {
        "colors": ["273522", "405233", "5c6b49", "7f865f", "1c2418"],
        "ratios": [20.0, 23.0, 24.0, 19.0, 14.0],
        "c_value": "1.78",
        "pixel_style": True,
        "pixel_size": "4",
        "num_colors": "5",
    },
    "EMR (Digital Flora)": {
        "colors": ["3a4d2f", "5a6b43", "78845a", "99a070", "232e1e"],
        "ratios": [19.0, 24.0, 23.0, 18.0, 16.0],
        "c_value": "1.7",
        "pixel_style": True,
        "pixel_size": "4",
        "num_colors": "5",
    },
    "MM-14 (Ukrainian Pixel)": {
        "colors": ["6d6b47", "89845f", "a39d73", "c0b891", "4f4d36"],
        "ratios": [19.0, 24.0, 23.0, 20.0, 14.0],
        "c_value": "1.65",
        "pixel_style": True,
        "pixel_size": "5",
        "num_colors": "5",
    },
    "Type 03 (Chinese Digital)": {
        "colors": ["384935", "546548", "6f8059", "90956c", "b1ad87"],
        "ratios": [18.0, 23.0, 25.0, 20.0, 14.0],
        "c_value": "1.72",
        "pixel_style": True,
        "pixel_size": "4",
        "num_colors": "5",
    },
}


class CamoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Pycamo: Camo Generator")
        self.root.geometry("1200x760")
        self.root.minsize(1100, 720)

        self.input_image_path: Path | None = None
        self.generated_image: Image.Image | None = None
        self._input_preview_tk: ImageTk.PhotoImage | None = None
        self._output_preview_tk: ImageTk.PhotoImage | None = None

        self.num_colors_var = tk.StringVar(value="5")
        self.c_value_var = tk.StringVar(value="1.2")
        self.width_var = tk.StringVar(value="500")
        self.height_var = tk.StringVar(value="500")
        self.pixel_style_var = tk.BooleanVar(value=False)
        self.seamless_var = tk.BooleanVar(value=True)
        self.pixel_size_var = tk.StringVar(value="10")
        self.image_path_var = tk.StringVar(value="No image selected")
        self.reference_preset_var = tk.StringVar(value="Custom (Manual)")

        self.color_vars = [tk.StringVar() for _ in range(MAX_COLORS)]
        self.ratio_vars = [tk.StringVar() for _ in range(MAX_COLORS)]
        self.swatches: list[tk.Label] = []

        self._build_ui()
        self._bind_color_updates()
        self._apply_equal_ratios(MAX_COLORS)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill="both", expand=True)

        left = ttk.Frame(container)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = ttk.Frame(container)
        right.pack(side="right", fill="y")

        self._build_controls(left)
        self._build_previews(right)

    def _build_controls(self, parent: ttk.Frame) -> None:
        image_frame = ttk.LabelFrame(parent, text="Input Image", padding=10)
        image_frame.pack(fill="x", pady=(0, 12))

        ttk.Button(image_frame, text="Load Image + Extract Colors", command=self.load_image).pack(
            side="left"
        )
        ttk.Label(image_frame, textvariable=self.image_path_var).pack(side="left", padx=(10, 0))

        params_frame = ttk.LabelFrame(parent, text="Parameters", padding=10)
        params_frame.pack(fill="x", pady=(0, 12))

        ttk.Label(params_frame, text="Extract colors (1-5):").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(params_frame, textvariable=self.num_colors_var, width=6).grid(
            row=0, column=1, sticky="w", pady=4, padx=(8, 14)
        )

        ttk.Label(params_frame, text="C value:").grid(row=0, column=2, sticky="w", pady=4)
        ttk.Entry(params_frame, textvariable=self.c_value_var, width=10).grid(
            row=0, column=3, sticky="w", pady=4, padx=(8, 14)
        )
        ttk.Checkbutton(params_frame, text="Seamless tile", variable=self.seamless_var).grid(
            row=0, column=4, columnspan=2, sticky="w", pady=4
        )

        ttk.Label(params_frame, text="Size (W x H):").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(params_frame, textvariable=self.width_var, width=8).grid(
            row=1, column=1, sticky="w", pady=4, padx=(8, 4)
        )
        ttk.Label(params_frame, text="x").grid(row=1, column=1, sticky="e", pady=4, padx=(0, 40))
        ttk.Entry(params_frame, textvariable=self.height_var, width=8).grid(
            row=1, column=2, sticky="w", pady=4, padx=(8, 0)
        )

        ttk.Checkbutton(params_frame, text="Pixel style", variable=self.pixel_style_var).grid(
            row=1, column=3, sticky="w", pady=4
        )
        ttk.Label(params_frame, text="Pixel size:").grid(row=1, column=4, sticky="w", pady=4, padx=(12, 0))
        ttk.Entry(params_frame, textvariable=self.pixel_size_var, width=8).grid(
            row=1, column=5, sticky="w", pady=4, padx=(8, 0)
        )

        ttk.Label(params_frame, text="Reference pattern:").grid(row=2, column=0, sticky="w", pady=4)
        preset_combo = ttk.Combobox(
            params_frame,
            textvariable=self.reference_preset_var,
            values=list(REFERENCE_PRESETS.keys()),
            state="readonly",
            width=30,
        )
        preset_combo.grid(row=2, column=1, columnspan=3, sticky="w", pady=4, padx=(8, 0))
        preset_combo.bind("<<ComboboxSelected>>", lambda _event: self.apply_reference_preset())
        ttk.Button(params_frame, text="Apply", command=self.apply_reference_preset).grid(
            row=2, column=4, sticky="w", padx=(12, 0), pady=4
        )
        ttk.Label(
            params_frame,
            text="Reference presets are structural approximations; adjust to taste.",
        ).grid(row=3, column=0, columnspan=6, sticky="w", pady=(2, 0))

        colors_frame = ttk.LabelFrame(parent, text="Colors and Ratios", padding=10)
        colors_frame.pack(fill="both", expand=True)

        ttk.Label(colors_frame, text="Color (hex)").grid(row=0, column=0, sticky="w")
        ttk.Label(colors_frame, text="Preview").grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(colors_frame, text="Ratio %").grid(row=0, column=2, sticky="w", padx=(12, 0))

        for idx in range(MAX_COLORS):
            color_entry = ttk.Entry(colors_frame, textvariable=self.color_vars[idx], width=14)
            color_entry.grid(row=idx + 1, column=0, sticky="w", pady=6)

            swatch = tk.Label(colors_frame, bg="#000000", width=4, relief="solid", borderwidth=1)
            swatch.grid(row=idx + 1, column=1, sticky="w", padx=(8, 0))
            self.swatches.append(swatch)

            ratio_entry = ttk.Entry(colors_frame, textvariable=self.ratio_vars[idx], width=8)
            ratio_entry.grid(row=idx + 1, column=2, sticky="w", padx=(12, 0), pady=6)

        actions = ttk.Frame(parent)
        actions.pack(fill="x", pady=(12, 0))

        ttk.Button(actions, text="Generate Preview", command=self.generate).pack(side="left")
        ttk.Button(actions, text="Save Generated Camo", command=self.save_generated).pack(
            side="left", padx=(8, 0)
        )

    def _build_previews(self, parent: ttk.Frame) -> None:
        input_frame = ttk.LabelFrame(parent, text="Input Preview", padding=8)
        input_frame.pack(fill="both", pady=(0, 12))

        self.input_preview = tk.Label(input_frame, width=200, height=200, bg="#d9d9d9", relief="sunken")
        self.input_preview.pack()

        output_frame = ttk.LabelFrame(parent, text="Generated Preview (500x500)", padding=8)
        output_frame.pack(fill="both")

        self.output_preview = tk.Label(output_frame, width=500, height=500, bg="#d9d9d9", relief="sunken")
        self.output_preview.pack()

    def _bind_color_updates(self) -> None:
        for var in self.color_vars:
            var.trace_add("write", lambda *_: self._update_swatches())
        self._update_swatches()

    def _update_swatches(self) -> None:
        for idx, var in enumerate(self.color_vars):
            raw = var.get().strip()
            if raw.startswith("#"):
                raw = raw[1:]
            if HEX_COLOR_RE.fullmatch(raw):
                self.swatches[idx].configure(bg=f"#{raw}")
            else:
                self.swatches[idx].configure(bg="#000000")

    def load_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Input Image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        self.input_image_path = Path(file_path)
        self.image_path_var.set(str(self.input_image_path))
        self._show_input_preview(self.input_image_path)
        self._extract_palette(self.input_image_path)

    def _show_input_preview(self, image_path: Path) -> None:
        try:
            img = Image.open(image_path).convert("RGB")
            preview = img.resize((200, 200), Image.LANCZOS)
            self._input_preview_tk = ImageTk.PhotoImage(preview)
            self.input_preview.configure(image=self._input_preview_tk)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load image preview:\n{exc}")

    def _extract_palette(self, image_path: Path) -> None:
        try:
            num_colors = int(self.num_colors_var.get().strip() or "5")
        except ValueError:
            messagebox.showerror("Error", "Extract colors must be an integer between 1 and 5.")
            return

        if not (1 <= num_colors <= MAX_COLORS):
            messagebox.showerror("Error", "Extract colors must be between 1 and 5.")
            return

        try:
            colors = camologic.extract_palette(str(image_path), num_colors=num_colors)
        except Exception as exc:
            messagebox.showerror("Error", f"Color extraction failed:\n{exc}")
            return

        for idx in range(MAX_COLORS):
            self.color_vars[idx].set("")
        for idx, color in enumerate(colors[:MAX_COLORS]):
            self.color_vars[idx].set(color.lower())

        self._apply_equal_ratios(max(1, len(colors[:MAX_COLORS])))

    def _apply_equal_ratios(self, n_colors: int) -> None:
        if n_colors <= 0:
            return
        equal_ratio = round(100.0 / n_colors, 4)
        for idx in range(MAX_COLORS):
            self.ratio_vars[idx].set(str(equal_ratio) if idx < n_colors else "0")

    def apply_reference_preset(self) -> None:
        preset_name = self.reference_preset_var.get()
        preset = REFERENCE_PRESETS.get(preset_name)

        if preset is None:
            return

        self.num_colors_var.set(str(preset["num_colors"]))
        self.c_value_var.set(str(preset["c_value"]))
        self.pixel_style_var.set(bool(preset["pixel_style"]))
        self.pixel_size_var.set(str(preset["pixel_size"]))

        for idx in range(MAX_COLORS):
            color_value = preset["colors"][idx] if idx < len(preset["colors"]) else ""
            ratio_value = str(preset["ratios"][idx]) if idx < len(preset["ratios"]) else "0"
            self.color_vars[idx].set(color_value)
            self.ratio_vars[idx].set(ratio_value)

        self._update_swatches()

    def _collect_colors(self) -> tuple[list[str], list[int]]:
        colors: list[str] = []
        indices: list[int] = []
        for idx, var in enumerate(self.color_vars):
            raw = var.get().strip()
            if not raw:
                continue
            if raw.startswith("#"):
                raw = raw[1:]
            if not HEX_COLOR_RE.fullmatch(raw):
                raise ValueError(f"Color {idx + 1} must be a 6-digit hex value (example: 7f8a52).")
            colors.append(raw.lower())
            indices.append(idx)
        return colors, indices

    def _collect_ratios(self, indices: list[int]) -> list[float]:
        ratios: list[float] = []
        for idx in indices:
            raw = self.ratio_vars[idx].get().strip()
            if not raw:
                ratios.append(0.0)
                continue
            try:
                ratios.append(float(raw))
            except ValueError as exc:
                raise ValueError(f"Ratio {idx + 1} must be numeric.") from exc

        ratio_sum = sum(ratios)
        if len(ratios) == 0:
            return ratios
        if ratio_sum <= 0 or abs(ratio_sum - 100.0) > 1e-3:
            self._apply_equal_ratios(len(indices))
            ratios = [float(self.ratio_vars[idx].get()) for idx in indices]
            messagebox.showinfo("Info", "Ratios were auto-filled to balance 100%.")
        return ratios

    def generate(self) -> None:
        try:
            colors, color_indices = self._collect_colors()
            if not colors:
                raise ValueError("Enter at least one valid color.")

            ratios = self._collect_ratios(color_indices)

            width = int(self.width_var.get().strip())
            height = int(self.height_var.get().strip())
            if width <= 0 or height <= 0:
                raise ValueError("Size must use positive integers.")

            c_value = float(self.c_value_var.get().strip())
            if c_value <= 0:
                raise ValueError("C value must be greater than 0.")

            image = camologic.generate_pattern(
                colors_hex=colors,
                output_filename=None,
                size=(width, height),
                c=c_value,
                ratios=ratios,
                seamless=self.seamless_var.get(),
            )

            if self.pixel_style_var.get():
                pixel_size = int(self.pixel_size_var.get().strip())
                if pixel_size <= 0:
                    raise ValueError("Pixel size must be a positive integer.")
                image = camologic.pixelize_image(image, pixel_size=pixel_size)

            self.generated_image = image
            self._show_output_preview(image)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _show_output_preview(self, image: Image.Image) -> None:
        preview = image.convert("RGB").resize((500, 500), Image.NEAREST)
        self._output_preview_tk = ImageTk.PhotoImage(preview)
        self.output_preview.configure(image=self._output_preview_tk)

    def _save_as_svg(self, image: Image.Image, output_path: str) -> None:
        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        pixels = rgb_image.load()

        svg_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">'
            ),
        ]

        # Compress contiguous horizontal pixels into single vector rectangles.
        for y in range(height):
            x = 0
            while x < width:
                r, g, b = pixels[x, y]
                run_width = 1
                while x + run_width < width and pixels[x + run_width, y] == (r, g, b):
                    run_width += 1
                svg_lines.append(
                    f'<rect x="{x}" y="{y}" width="{run_width}" height="1" fill="#{r:02x}{g:02x}{b:02x}" />'
                )
                x += run_width

        svg_lines.append("</svg>")
        Path(output_path).write_text("\n".join(svg_lines), encoding="utf-8")

    def save_generated(self) -> None:
        if self.generated_image is None:
            messagebox.showerror("Error", "Generate a camo pattern before saving.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Camo Pattern",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("SVG files", "*.svg"), ("All files", "*.*")],
        )
        if not output_path:
            return

        try:
            suffix = Path(output_path).suffix.lower()
            if suffix == ".svg":
                self._save_as_svg(self.generated_image, output_path)
            else:
                self.generated_image.save(output_path)
            messagebox.showinfo("Success", f"Saved to:\n{output_path}")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to save image:\n{exc}")


def main() -> None:
    root = tk.Tk()
    CamoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
