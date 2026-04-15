from __future__ import annotations

import argparse
import math
from pathlib import Path

from pypdf import PdfReader, PdfWriter, PageObject, Transformation


# Tamaño carta en puntos PDF
LETTER_W = 612   # 8.5 in * 72
LETTER_H = 792   # 11 in * 72

# Salida en horizontal
SHEET_W = LETTER_H  # 792
SHEET_H = LETTER_W  # 612


def add_blank_pages(pages: list[PageObject], multiple: int) -> list[PageObject]:
    """
    Completa hasta múltiplo de `multiple`.
    Para cuadernillo 2-up: múltiplo de 4
    Para cuadernillo 4-up: múltiplo de 8
    """
    total = len(pages)
    faltan = (multiple - (total % multiple)) % multiple
    resultado = list(pages)

    for _ in range(faltan):
        blank = PageObject.create_blank_page(width=LETTER_W, height=LETTER_H)
        resultado.append(blank)

    return resultado


def fit_page_to_slot(
    src_page: PageObject,
    slot_x: float,
    slot_y: float,
    slot_w: float,
    slot_h: float,
    margin: float = 12,
) -> tuple[PageObject, Transformation]:
    """
    Calcula la transformación para escalar y centrar una página dentro de un espacio.
    """
    src_w = float(src_page.mediabox.width)
    src_h = float(src_page.mediabox.height)

    usable_w = slot_w - 2 * margin
    usable_h = slot_h - 2 * margin

    scale = min(usable_w / src_w, usable_h / src_h)

    placed_w = src_w * scale
    placed_h = src_h * scale

    x = slot_x + (slot_w - placed_w) / 2
    y = slot_y + (slot_h - placed_h) / 2

    transform = Transformation().scale(scale).translate(tx=x, ty=y)
    return src_page, transform


def merge_page_in_slot(
    dest_page: PageObject,
    src_page: PageObject,
    slot_x: float,
    slot_y: float,
    slot_w: float,
    slot_h: float,
    margin: float = 12,
) -> None:
    """
    Inserta una página dentro de uno de los espacios de la hoja.
    """
    _, transform = fit_page_to_slot(
        src_page=src_page,
        slot_x=slot_x,
        slot_y=slot_y,
        slot_w=slot_w,
        slot_h=slot_h,
        margin=margin,
    )
    dest_page.merge_transformed_page(src_page, transform)


def booklet_sheet_indices(total_pages: int, sheet_index: int) -> dict[str, int]:
    """
    Devuelve los índices de una hoja de cuadernillo clásica (2 páginas por cara).
    """
    return {
        "front_left": total_pages - 1 - (2 * sheet_index),
        "front_right": 2 * sheet_index,
        "back_left": 2 * sheet_index + 1,
        "back_right": total_pages - 2 - (2 * sheet_index),
    }


def build_booklet_2up(reader: PdfReader, margin: float = 12) -> PdfWriter:
    """
    Genera un PDF impuesto en formato cuadernillo.
    Salida: hojas carta horizontal, 2 páginas por cara.
    """
    original_pages = list(reader.pages)
    padded_pages = add_blank_pages(original_pages, multiple=4)
    total = len(padded_pages)

    writer = PdfWriter()

    left_slot = (0, 0, SHEET_W / 2, SHEET_H)
    right_slot = (SHEET_W / 2, 0, SHEET_W / 2, SHEET_H)

    num_sheets = total // 4

    for sheet in range(num_sheets):
        idx = booklet_sheet_indices(total, sheet)

        # Cara frontal
        front = PageObject.create_blank_page(width=SHEET_W, height=SHEET_H)
        merge_page_in_slot(front, padded_pages[idx["front_left"]], *left_slot, margin=margin)
        merge_page_in_slot(front, padded_pages[idx["front_right"]], *right_slot, margin=margin)
        writer.add_page(front)

        # Cara posterior
        back = PageObject.create_blank_page(width=SHEET_W, height=SHEET_H)
        merge_page_in_slot(back, padded_pages[idx["back_left"]], *left_slot, margin=margin)
        merge_page_in_slot(back, padded_pages[idx["back_right"]], *right_slot, margin=margin)
        writer.add_page(back)

    return writer


def build_booklet_4up(reader: PdfReader, margin: float = 12) -> PdfWriter:
    """
    Genera un cuadernillo 4-up para doblar solo una vez (sin cortes).
    Cada cara de la hoja tiene 2 páginas arriba y 2 abajo.
    Al doblar, cada página del libro muestra 2 páginas del PDF original.
    """
    original_pages = list(reader.pages)
    # Para este formato, el total de páginas debe ser múltiplo de 8 
    # (ya que cada hoja física contiene 8 páginas del PDF)
    padded_pages = add_blank_pages(original_pages, multiple=8)
    total = len(padded_pages)
    
    writer = PdfWriter()

    # Definimos los cuadrantes (slots)
    half_w = SHEET_W / 2
    half_h = SHEET_H / 2

    # Slots: (x, y, ancho, alto)
    slot_tl = (0,      half_h, half_w, half_h) # Superior Izquierda
    slot_tr = (half_w, half_h, half_w, half_h) # Superior Derecha
    slot_bl = (0,      0,      half_w, half_h) # Inferior Izquierda
    slot_br = (half_w, 0,      half_w, half_h) # Inferior Derecha

    # Calculamos cuántas hojas físicas de papel usaremos
    num_sheets = total // 8
    # Tratamos el documento como si fueran pares de páginas (total // 2)
    num_pairs = total // 2

    for sheet in range(num_sheets):
        # Usamos la lógica de 2-up pero aplicada a pares de páginas
        # El par 0 contiene PDF pag 0 y 1. El par 1 contiene PDF pag 2 y 3...
        p_idx = booklet_sheet_indices(num_pairs, sheet)

        # --- CARA FRONTAL (Anverso) ---
        front = PageObject.create_blank_page(width=SHEET_W, height=SHEET_H)
        
        # Par Izquierdo (Páginas del final del PDF)
        merge_page_in_slot(front, padded_pages[2 * p_idx["front_left"]],     *slot_tl, margin=margin)
        merge_page_in_slot(front, padded_pages[2 * p_idx["front_left"] + 1], *slot_bl, margin=margin)
        
        # Par Derecho (Páginas del inicio del PDF - Portada)
        merge_page_in_slot(front, padded_pages[2 * p_idx["front_right"]],     *slot_tr, margin=margin)
        merge_page_in_slot(front, padded_pages[2 * p_idx["front_right"] + 1], *slot_br, margin=margin)
        
        writer.add_page(front)

        # --- CARA POSTERIOR (Reverso) ---
        back = PageObject.create_blank_page(width=SHEET_W, height=SHEET_H)
        
        # Par Izquierdo
        merge_page_in_slot(back, padded_pages[2 * p_idx["back_left"]],     *slot_tl, margin=margin)
        merge_page_in_slot(back, padded_pages[2 * p_idx["back_left"] + 1], *slot_bl, margin=margin)
        
        # Par Derecho
        merge_page_in_slot(back, padded_pages[2 * p_idx["back_right"]],     *slot_tr, margin=margin)
        merge_page_in_slot(back, padded_pages[2 * p_idx["back_right"] + 1], *slot_br, margin=margin)
        
        writer.add_page(back)

    return writer



def build_booklet(reader: PdfReader, margin: float = 12, pages_per_side: int = 2) -> PdfWriter:
    if pages_per_side == 2:
        return build_booklet_2up(reader, margin=margin)
    if pages_per_side == 4:
        return build_booklet_4up(reader, margin=margin)
    raise ValueError("pages_per_side debe ser 2 o 4")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convierte un PDF en cuadernillo carta, con 2 o 4 páginas por cara."
    )
    parser.add_argument("input_pdf", help="Ruta del PDF de entrada, relativa a pdf/input/")
    parser.add_argument(
        "-o",
        "--output",
        help="Ruta del PDF de salida. Si no se indica, crea un archivo en pdf/output/",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=12,
        help="Margen interno en puntos PDF. Default: 12",
    )
    parser.add_argument(
        "--pages-per-side",
        type=int,
        choices=[2, 4],
        default=2,
        help="Cantidad de páginas por cara: 2 o 4. Default: 2",
    )

    args = parser.parse_args()

    input_path = Path("pdf/input") / args.input_pdf
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {input_path}")

    output_dir = Path("pdf/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        suffix = f"_cuadernillo_{args.pages_per_side}up.pdf"
        output_path = output_dir / f"{input_path.stem}{suffix}"

    if output_path.parent != Path("."):
        output_path.parent.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(input_path))
    writer = build_booklet(
        reader,
        margin=args.margin,
        pages_per_side=args.pages_per_side,
    )

    with output_path.open("wb") as f:
        writer.write(f)

    total_original = len(reader.pages)
    multiple = 4 if args.pages_per_side == 2 else 8
    total_padded = math.ceil(total_original / multiple) * multiple
    blanks_added = total_padded - total_original

    print(f"PDF original: {input_path}")
    print(f"Páginas originales: {total_original}")
    print(f"Páginas finales ajustadas: {total_padded}")
    print(f"Páginas en blanco agregadas: {blanks_added}")
    print(f"Páginas por cara: {args.pages_per_side}")
    print(f"Salida: {output_path}")
    print()
    print("Imprimir así:")
    print("- Tamaño carta")
    print("- Doble cara")
    print("- Voltear por borde corto")
    print("- Escala 100% o tamaño real")


if __name__ == "__main__":
    main()