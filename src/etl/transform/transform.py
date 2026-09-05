from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, HeadingHierarchyOptions
from docling.datamodel.base_models import InputFormat

import os
import time
import re

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

TABLE_REGEX = re.compile(
    r'(?:^|\n)(Table\s+\d+\.[^\n]*\n)?'  # Optional caption
    r'(\|[^\n]+\|\n'                     # Header row
    r'\|[-:\s|]+\|\n'                    # Separator row
    r'(?:\|[^\n]+\|\n?)+)',              # Data rows
    re.MULTILINE | re.IGNORECASE
)


def init_converter():
    """
    Initializes the DocumentConverter instance.

    Returns:
        DocumentConverter: An instance of the DocumentConverter class.
    """
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_code_enrichment = True
    pipeline_options.do_ocr = False

    pipeline_options.heading_hierarchy_options = HeadingHierarchyOptions(
        enabled=True)
    pipeline_options.generate_parsed_pages = True

    converter = DocumentConverter(format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    })
    return converter


def convert_doc2md(filename: str, converter: DocumentConverter, input_dir: str = "./data/pdf"):
    result = converter.convert(f"{input_dir}/{filename}.pdf")
    return result.document.export_to_markdown()


def clean_docling_output(markdown_text: str) -> str:
    # 1. Nuke the First-Page ACM Copyright/Frontmatter
    # Finds "1 INTRODUCTION" and keeps everything from there onwards
    intro_match = re.search(r'^#*\s*1\s+INTRODUCTION',
                            markdown_text, re.MULTILINE | re.IGNORECASE)
    if intro_match:
        markdown_text = markdown_text[intro_match.start():]

    # 2. Nuke the Backmatter (References, Acknowledgments)
    # Finds the first occurrence of "REFERENCES" or "ACKNOWLEDGMENTS" and drops the rest
    backmatter_match = re.search(
        r'^#*\s*(REFERENCES|ACKNOWLEDGMENTS)\b', markdown_text, re.MULTILINE | re.IGNORECASE)
    if backmatter_match:
        markdown_text = markdown_text[:backmatter_match.start()]

    # markdown_text = re.sub(
    #     r'^StatuScale: Status-aware and Elastic Scaling Strategy for Microservice Applications\s*$', '', markdown_text, flags=re.MULTILINE)

    # 2. Remove remaining page numbers like "0:2", "0:15", etc.
    markdown_text = re.sub(
        r'^0:\d+\s*$', '', markdown_text, flags=re.MULTILINE)

    # # 3. Remove any lingering author names or copyright footers
    # markdown_text = re.sub(r'^Wen et al\.\s*$', '',
    #                        markdown_text, flags=re.MULTILINE)
    # markdown_text = re.sub(r'^0, 0, 0\. , 2024\.\s*$',
    #                        '', markdown_text, flags=re.MULTILINE)

    # 4. Collapse the massive blank gaps left behind
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
    return markdown_text.strip()


def chunk_markdown_file(markdown_content: str, additional_metadata: dict) -> list[Document]:
    # 1. Split by Headers (Semantic Boundaries)
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Title"), ("##", "Section"), ("###",
                                                "Subsection"), ("####", "Subsubsection")
        ]
    )
    header_chunks = header_splitter.split_text(markdown_content)

    final_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=100
    )

    for doc in header_chunks:
        merged_metadata = {**additional_metadata, **doc.metadata}
        text_content = doc.page_content

        # Flag equations
        if "<!-- formula-not-decoded -->" in text_content:
            merged_metadata["contains_equation_ref"] = True

        # 2. Extract Tables (The Production Fix)
        tables_in_chunk = TABLE_REGEX.findall(text_content)

        if tables_in_chunk:
            # findall returns tuples of (caption, table) because of the regex groups
            for caption, table in tables_in_chunk:
                table_metadata = merged_metadata.copy()
                table_metadata["doc_type"] = "table"

                # Combine caption and table so the LLM has full context
                full_table_content = (
                    caption + table).strip() if caption else table.strip()

                final_chunks.append(
                    Document(page_content=full_table_content,
                             metadata=table_metadata)
                )

            # Replace tables (and their captions) with a placeholder
            text_content = TABLE_REGEX.sub(
                "\n[Table omitted, see table chunks]\n", text_content)

        # 3. Chunk the remaining text safely
        text_metadata = merged_metadata.copy()
        text_metadata["doc_type"] = "text"

        # FIX: Only create text documents if there's actual text left
        # This prevents creating empty chunks if the section was just a table
        clean_text = text_content.replace(
            "[Table omitted, see table chunks]", "").strip()
        if clean_text:
            text_docs = text_splitter.create_documents(
                [text_content], metadatas=[text_metadata]
            )
            final_chunks.extend(text_docs)

    return final_chunks


if __name__ == "__main__":
    import os

    # Example usage: Convert from ./data dir to markdown
    input_dir = "./data/pdf"
    output_dir = "./data/markdown"

    print(f"Converting PDF files in {input_dir} to Markdown...")
    converter = init_converter()

    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            # Check if the output file already exists
            output_file_path = f"{output_dir}/{filename[:-4]}.md"
            if os.path.exists(output_file_path):
                print(
                    f"Skipping {filename} as it already exists in the output directory.")
                doc = open(output_file_path, "r", encoding="utf-8").read()
            else:
                start = time.perf_counter()
                doc = convert_doc2md(
                    filename[:-4], converter, input_dir=input_dir)
                end = time.perf_counter()
                print(
                    f"Time taken to process {filename}: {end - start:.2f} seconds")
            print(f"Cleaning the markdown content for {filename}...")
            refined_doc = clean_docling_output(doc)
            chunked_docs = chunk_markdown_file(refined_doc, additional_metadata={
                "source_file": filename, "source_path": output_file_path})
            print(chunked_docs)
            with open(f"{output_dir}/{filename[:-4]}.md", "w", encoding="utf-8") as f:
                f.write(refined_doc)  # type: ignore
