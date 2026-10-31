"""
Generate a sample PDF for testing the AI Tutor system.
Topic: Biology — Cells

Run: python create_sample_pdf.py
"""

from fpdf import FPDF
import os


def create_sample_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ─── Page 1: Introduction to Cells ───
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "Biology: Introduction to Cells", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 12)
    content_page1 = """What is a Cell?

A cell is the smallest unit of life. All living things are made of cells. Some organisms have just one cell. These are called unicellular organisms. Examples include bacteria and amoeba. Other organisms have many cells. These are called multicellular organisms. Humans are multicellular. The human body has about 37 trillion cells.

Cells were first discovered by Robert Hooke in 1665. He looked at a thin slice of cork under a microscope. He saw tiny box-like structures. He called them cells because they looked like small rooms. The word cell comes from the Latin word cella which means small room.

Cell Theory

Cell theory is one of the most important ideas in biology. It has three main parts:

1. All living things are made of one or more cells.
2. The cell is the basic unit of life.
3. All cells come from existing cells.

This theory was developed by scientists Matthias Schleiden, Theodor Schwann, and Rudolf Virchow in the 1800s.

Types of Cells

There are two main types of cells:

1. Prokaryotic cells - These are simple cells. They do not have a nucleus. The DNA floats freely inside the cell. Bacteria are prokaryotic cells. They are very small, usually 1 to 10 micrometers.

2. Eukaryotic cells - These are complex cells. They have a nucleus that holds the DNA. They also have other organelles. Plant cells, animal cells, and fungal cells are eukaryotic. They are larger, usually 10 to 100 micrometers."""

    pdf.multi_cell(0, 7, content_page1)

    # ─── Page 2: Cell Parts ───
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "Parts of a Cell", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 12)
    content_page2 = """Every cell has important parts called organelles. Each organelle has a specific job.

Cell Membrane

The cell membrane is the outer covering of the cell. It is like a gatekeeper. It controls what goes in and out of the cell. It is made of a double layer of lipids (fats) with proteins embedded in it. This is called the phospholipid bilayer. The membrane is selectively permeable. This means it allows some substances to pass through but not others.

Nucleus

The nucleus is the control center of the cell. It contains DNA, which carries genetic information. DNA tells the cell what to do and how to make proteins. The nucleus is surrounded by a nuclear membrane with tiny pores. These pores allow materials to move between the nucleus and the rest of the cell. Inside the nucleus, there is a smaller structure called the nucleolus. The nucleolus makes ribosomes.

Cytoplasm

The cytoplasm is a jelly-like substance that fills the inside of the cell. It is mostly made of water. All the organelles float in the cytoplasm. Many important chemical reactions happen in the cytoplasm.

Mitochondria

Mitochondria are called the powerhouse of the cell. They produce energy for the cell. They convert food (glucose) into energy (ATP) through a process called cellular respiration. Cells that need more energy, like muscle cells, have more mitochondria.

Ribosomes

Ribosomes are tiny structures that make proteins. Proteins are essential for the cell. They help with growth, repair, and many cell functions. Ribosomes can be found floating freely in the cytoplasm or attached to the endoplasmic reticulum.

Endoplasmic Reticulum (ER)

The ER is a network of membranes inside the cell. There are two types:
- Rough ER: Has ribosomes attached to it. It makes and transports proteins.
- Smooth ER: Does not have ribosomes. It makes lipids and detoxifies harmful substances.

Golgi Apparatus

The Golgi apparatus is like the post office of the cell. It packages proteins and lipids into vesicles. Then it sends them to where they are needed, either inside or outside the cell."""

    pdf.multi_cell(0, 7, content_page2)

    # ─── Page 3: Plant vs Animal Cells ───
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "Plant Cells vs Animal Cells", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 12)
    content_page3 = """Both plant cells and animal cells are eukaryotic. They share many features. But they also have important differences.

Features only in Plant Cells:

1. Cell Wall: A rigid outer layer made of cellulose. It gives the plant cell its shape and provides support. It is found outside the cell membrane.

2. Chloroplasts: These organelles contain chlorophyll, a green pigment. Chloroplasts carry out photosynthesis. This is the process where plants use sunlight, water, and carbon dioxide to make glucose (food) and oxygen.

3. Large Central Vacuole: Plant cells have one large vacuole that takes up most of the cell space. It stores water, nutrients, and waste products. It also helps maintain the shape of the cell.

Features only in Animal Cells:

1. Centrioles: These help with cell division. They organize the spindle fibers that separate chromosomes during mitosis.

2. Lysosomes: These are more common in animal cells. They contain digestive enzymes. They break down old organelles, food particles, and invading bacteria.

Shared Features:

Both plant and animal cells have:
- Cell membrane
- Nucleus
- Cytoplasm
- Mitochondria
- Ribosomes
- Endoplasmic Reticulum
- Golgi Apparatus

Cell Division

Cells reproduce by dividing. There are two main types of cell division:

1. Mitosis: This produces two identical daughter cells. It is used for growth and repair. Each new cell has the same number of chromosomes as the parent cell.

2. Meiosis: This produces four cells, each with half the number of chromosomes. It is used to make sex cells (eggs and sperm). This is important for sexual reproduction.

The Cell Cycle

The cell cycle is the life cycle of a cell. It has several stages:
- Interphase: The cell grows and copies its DNA. This is the longest phase.
- Mitosis: The nucleus divides.
- Cytokinesis: The cytoplasm divides, creating two new cells.

Summary

Cells are the building blocks of all living things. They come in different types and sizes. Each part of the cell has an important job. Understanding cells helps us understand how life works at the most basic level."""

    pdf.multi_cell(0, 7, content_page3)

    # Save PDF
    output_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "biology_cells.pdf")
    pdf.output(output_path)
    print(f"Sample PDF created: {output_path}")
    return output_path


if __name__ == "__main__":
    create_sample_pdf()
