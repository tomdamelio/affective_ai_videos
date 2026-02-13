"""Herramienta simple para dibujar máscaras sobre imágenes.

Permite cargar una imagen, pintar sobre ella (máscara blanca) y guardar
la imagen de la máscara resultante (blanco y negro).

Uso:
    python scripts/create_mask.py --image "img/mi_imagen.jpg"

Controles:
    - Click Izquierdo + Arrastrar: Pintar (Blanco).
    - Click Derecho + Arrastrar: Borrar (Negro).
    - Rueda del mouse: Cambiar tamaño del pincel.
    - S: Guardar máscara (mismo nombre + _mask.png) y salir.
    - Q / Esc: Salir sin guardar.
"""

import argparse
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
from pathlib import Path

class MaskCreator:
    def __init__(self, root, image_path):
        self.root = root
        self.root.title("Creador de Máscaras - Affective AI Videos")
        
        self.image_path = Path(image_path)
        self.output_path = self.image_path.parent / f"{self.image_path.stem}_mask.png"
        
        # Cargar imagen original
        try:
            self.original_image = Image.open(self.image_path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")
            self.root.destroy()
            return

        self.width, self.height = self.original_image.size
        
        # Ajustar tamaño de ventana si es muy grande
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        scale = 1.0
        if self.width > screen_width * 0.9 or self.height > screen_height * 0.9:
            scale = min(screen_width * 0.9 / self.width, screen_height * 0.9 / self.height)
            self.display_width = int(self.width * scale)
            self.display_height = int(self.height * scale)
            self.display_image = self.original_image.resize((self.display_width, self.display_height), Image.Resampling.LANCZOS)
        else:
            self.display_width = self.width
            self.display_height = self.height
            self.display_image = self.original_image
            
        self.scale = scale
        
        # Crear imagen para la máscara (negro fondo)
        self.mask_image = Image.new("L", (self.width, self.height), 0)
        self.draw = ImageDraw.Draw(self.mask_image)
        
        # Configuración de pincel
        self.brush_size = 30
        self.last_x, self.last_y = None, None
        
        # UI Setup
        self.setup_ui()
        
        # Bindings
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset_last)
        
        self.canvas.bind("<Button-3>", self.start_erase)
        self.canvas.bind("<B3-Motion>", self.erase)
        
        self.root.bind("<MouseWheel>", self.change_brush_size)
        self.root.bind("<s>", self.save_mask)
        self.root.bind("<q>", self.close)
        self.root.bind("<Escape>", self.close)

    def setup_ui(self):
        # Frame principal
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas
        self.canvas = tk.Canvas(self.frame, width=self.display_width, height=self.display_height, cursor="cross")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Imagen de fondo
        self.tk_image = ImageTk.PhotoImage(self.display_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
        # Capa de máscara (semi-transparente para visualizar)
        self.overlay_image_tk = None
        self.overlay_id = None
        
        # Info label
        self.info_label = tk.Label(
            self.root, 
            text=f"Pincel: {self.brush_size} px | Click Izq: Pintar | Click Der: Borrar | 'S': Guardar | 'Q': Salir",
            bg="black", fg="white", font=("Arial", 10)
        )
        self.info_label.pack(side=tk.BOTTOM, fill=tk.X)

    def update_overlay(self):
        # Crear una visualización de la máscara sobre la imagen original
        # Convertir máscara a RGBA con rojo semitransparente donde sea blanco
        mask_rgba = self.mask_image.convert("RGBA")
        # Columna alpha = mascara * 0.5
        
        # Crear overlay rojo
        overlay = Image.new("RGBA", (self.width, self.height), (255, 0, 0, 0)) # Transparente
        
        # Donde la máscara es blanca (255), ponemos rojo semi-transparente (255, 0, 0, 100)
        # Manera rápida: usar mask como canal alpha de un color sólido
        red_layer = Image.new("RGBA", (self.width, self.height), (255, 0, 0, 100))
        # Usar la mask_image como máscara para pegar red_layer
        overlay.paste(red_layer, (0, 0), self.mask_image)
        
        # Redimensionar para display
        if self.scale != 1.0:
            overlay_display = overlay.resize((self.display_width, self.display_height), Image.Resampling.NEAREST)
        else:
            overlay_display = overlay
            
        self.overlay_tk = ImageTk.PhotoImage(overlay_display)
        
        if self.overlay_id:
            self.canvas.delete(self.overlay_id)
            
        self.overlay_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.overlay_tk)

    def get_coords(self, event):
        x = int(event.x / self.scale)
        y = int(event.y / self.scale)
        return x, y

    def start_draw(self, event):
        self.last_x, self.last_y = self.get_coords(event)
        self.paint(event)

    def start_erase(self, event):
        self.last_x, self.last_y = self.get_coords(event)
        self.erase(event)

    def paint(self, event):
        x, y = self.get_coords(event)
        if self.last_x and self.last_y:
            self.draw.line([self.last_x, self.last_y, x, y], fill=255, width=self.brush_size)
            self.draw.ellipse([x - self.brush_size//2, y - self.brush_size//2, 
                               x + self.brush_size//2, y + self.brush_size//2], fill=255)
        self.last_x, self.last_y = x, y
        # Update visual feedback (podría ser lento en computadoras viejas, optimizar si es necesario)
        # Para performance, podríamos dibujar en el canvas directamente con rojo, pero PIL es la verdad
        self.update_overlay()

    def erase(self, event):
        x, y = self.get_coords(event)
        if self.last_x and self.last_y:
            self.draw.line([self.last_x, self.last_y, x, y], fill=0, width=self.brush_size)
            self.draw.ellipse([x - self.brush_size//2, y - self.brush_size//2, 
                               x + self.brush_size//2, y + self.brush_size//2], fill=0)
        self.last_x, self.last_y = x, y
        self.update_overlay()

    def reset_last(self, event):
        self.last_x, self.last_y = None, None

    def change_brush_size(self, event):
        if event.delta > 0:
            self.brush_size += 5
        else:
            self.brush_size = max(5, self.brush_size - 5)
        self.info_label.config(text=f"Pincel: {self.brush_size} px | Click Izq: Pintar | Click Der: Borrar | 'S': Guardar | 'Q': Salir")

    def save_mask(self, event=None):
        try:
            self.mask_image.save(self.output_path)
            messagebox.showinfo("Guardado", f"Máscara guardada en:\n{self.output_path}")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))

    def close(self, event=None):
        self.root.destroy()

def main():
    parser = argparse.ArgumentParser(description="Dibujar máscara para inpainting.")
    parser.add_argument("--image", "-i", type=str, required=True, help="Imagen base")
    args = parser.parse_args()
    
    root = tk.Tk()
    app = MaskCreator(root, args.image)
    root.mainloop()

if __name__ == "__main__":
    main()
