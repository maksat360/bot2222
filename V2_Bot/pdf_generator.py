# pdf_generator.py — Генерация PDF-документов
# ==============================================

import os
import time
from fpdf import FPDF
from config import TEMP_DIR


class SalaryPDF(FPDF):
    """Класс для генерации зарплатной ведомости в PDF."""

    def __init__(self):
        super().__init__()
        # Подключаем шрифт с поддержкой кириллицы
        font_path = os.path.join("fonts", "DejaVuSans.ttf")
        if os.path.exists(font_path):
            self.add_font("DejaVu", "", font_path, uni=True)
            self.add_font("DejaVu", "B", font_path.replace(".ttf", "Bold.ttf"), uni=True)
            self.font_name = "DejaVu"
        else:
            # Если шрифт не найден, используем стандартный
            self.font_name = "Helvetica"


def generate_salary_pdf(employee_data, month, year):
    """Создаёт PDF с зарплатной ведомостью сотрудника."""
    os.makedirs(TEMP_DIR, exist_ok=True)

    pdf = SalaryPDF()
    pdf.add_page()

    # Заголовок
    pdf.set_font(pdf.font_name, "B", 16)
    pdf.cell(0, 10, f"Зарплатная ведомость за {month} {year}", ln=True, align="C")
    pdf.ln(10)

    # Данные сотрудника
    pdf.set_font(pdf.font_name, "", 12)

    fields = [
        ("Сотрудник", employee_data.get("ФИО", "")),
        ("Должность", employee_data.get("Должность", "")),
        ("Оклад", str(employee_data.get("Оклад", ""))),
        ("Отработано часов", str(employee_data.get("Отработано часов", ""))),
        ("Премия", str(employee_data.get("Премия", ""))),
        ("Удержания", str(employee_data.get("Удержания", ""))),
        ("Итого к выдаче", str(employee_data.get("Итого к выдаче", ""))),
    ]

    for label, value in fields:
        pdf.set_font(pdf.font_name, "B", 11)
        pdf.cell(60, 10, f"{label}:", border=1)
        pdf.set_font(pdf.font_name, "", 11)
        pdf.cell(0, 10, value, border=1, ln=True)

    # Сохраняем во временную папку
    filename = f"Зарплата_{employee_data.get('Логин', 'unknown')}_{month}_{year}.pdf"
    filepath = os.path.join(TEMP_DIR, filename)
    pdf.output(filepath)

    return filepath


def cleanup_temp_files():
    """Удаляет из временной папки файлы старше 10 минут."""
    if not os.path.exists(TEMP_DIR):
        return

    now = time.time()
    cutoff = now - (10 * 60)  # 10 минут

    for filename in os.listdir(TEMP_DIR):
        filepath = os.path.join(TEMP_DIR, filename)
        if os.path.isfile(filepath):
            file_mtime = os.path.getmtime(filepath)
            if file_mtime < cutoff:
                os.remove(filepath)