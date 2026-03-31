from __future__ import annotations

import argparse
import math
from pathlib import Path

from pypdf import PdfReader, PdfWriter, PageObject, Transformation


# Tamaño carta en puntos PDF
LETTER_W = 612   # 8.5 in * 72
LETTER_H = 792   # 11 in * 72

# Salida en horizontal, porque van 2 páginas por hoja
SHEET_W = LETTER_H  # 792
SHEET_H = LETTER_W  # 612


def add_blank_pages(pages: list[PageObject]) -> list[PageObject]:
    """
    Completa hasta múltiplo de 4 para que el cuadernillo cierre bien.
    """
    total = len(pages)
    faltan = (4 - (total % 4)) % 4
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
    Inserta una página dentro de uno de los dos espacios de la hoja.
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


def build_booklet(reader: PdfReader, margin: float = 12) -> PdfWriter:
    """
    Genera un PDF impuesto en formato cuadernillo.
    Salida: hojas carta horizontal, 2 páginas por cara.
    """
    original_pages = list(reader.pages)
    padded_pages = add_blank_pages(original_pages)
    total = len(padded_pages)

    writer = PdfWriter()

    left_slot = (0, 0, SHEET_W / 2, SHEET_H)
    right_slot = (SHEET_W / 2, 0, SHEET_W / 2, SHEET_H)

    num_sheets = total // 4

    for sheet in range(num_sheets):
        # Índices del bloque de 4 páginas del cuadernillo
        left_front_index = total - 1 - (2 * sheet)
        right_front_index = 2 * sheet

        left_back_index = 2 * sheet + 1
        right_back_index = total - 2 - (2 * sheet)

        # Cara frontal
        front = PageObject.create_blank_page(width=SHEET_W, height=SHEET_H)
        merge_page_in_slot(front, padded_pages[left_front_index], *left_slot, margin=margin)
        merge_page_in_slot(front, padded_pages[right_front_index], *right_slot, margin=margin)
        writer.add_page(front)

        # Cara posterior
        back = PageObject.create_blank_page(width=SHEET_W, height=SHEET_H)
        merge_page_in_slot(back, padded_pages[left_back_index], *left_slot, margin=margin)
        merge_page_in_slot(back, padded_pages[right_back_index], *right_slot, margin=margin)
        writer.add_page(back)

    return writer


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convierte un PDF en cuadernillo carta, 2 páginas por cara."
    )
    parser.add_argument("input_pdf", help="Ruta del PDF de entrada")
    parser.add_argument(
        "-o",
        "--output",
        help="Ruta del PDF de salida. Si no se indica, crea un archivo junto al original.",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=12,
        help="Margen interno en puntos PDF. Default: 12",
    )

    args = parser.parse_args()

    input_path = Path(args.input_pdf)
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {input_path}")

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(f"{input_path.stem}_cuadernillo.pdf")

    reader = PdfReader(str(input_path))
    writer = build_booklet(reader, margin=args.margin)

    with output_path.open("wb") as f:
        writer.write(f)

    total_original = len(reader.pages)
    total_padded = math.ceil(total_original / 4) * 4
    blanks_added = total_padded - total_original

    print(f"PDF original: {input_path}")
    print(f"Páginas originales: {total_original}")
    print(f"Páginas finales ajustadas a cuadernillo: {total_padded}")
    print(f"Páginas en blanco agregadas: {blanks_added}")
    print(f"Salida: {output_path}")
    print()
    print("Imprimir así:")
    print("- Tamaño carta")
    print("- Doble cara")
    print("- Voltear por borde corto")
    print("- Escala 100% o tamaño real")


if __name__ == "__main__":
    main()