from typing import Iterable, List
import os

import arxiv
from urllib.request import urlretrieve


def get_arxiv_paper_by_ids(arxiv_id: List[str], client: arxiv.Client):
    """
    Fetches arXiv papers by their IDs.

    Parameters:
    arxiv_id (List[str]): A list of arXiv IDs of the papers to fetch.

    Returns:
    List[arxiv.Result]: A list of dictionaries containing the papers' metadata.
    """
    try:
        search = arxiv.Search(id_list=arxiv_id)
        results = client.results(search)
        papers = list(results)
        metadata_map = {
            paper.get_short_id(): {
                "title": paper.title,
                "authors": ", ".join(author.name for author in paper.authors),
                "arxiv_id": paper.get_short_id(),
                "published": paper.published.strftime("%Y-%m-%d") if paper.published else "Unknown",
                "category": paper.primary_category,
            } for paper in papers
        }
        if results:
            return papers, metadata_map
        else:
            return None, {}
    except Exception as e:
        print(f"Error fetching paper with ID {arxiv_id}: {e}")
        return None, {}


def download_arxiv_papers_pdf(list_of_papers: list[arxiv.Result], download_dir: str):
    """
    Downloads the PDFs of the given arXiv papers.

    Parameters:
    list_of_papers (list[arxiv.Result]): An list of arXiv paper results.
    download_dir (str): The directory where the PDFs will be saved.
    """
    for paper in list_of_papers:
        print(f"Downloading PDF for {paper.title}...")
        os.makedirs(download_dir, exist_ok=True)
        if os.path.exists(f"{download_dir}/{paper.get_short_id()}.pdf"):
            print(
                f"Skipping {paper.title} as it already exists in the download directory.")
            continue
        try:
            filename = f"{download_dir}/{paper.get_short_id()}.pdf"
            urlretrieve(paper.pdf_url, filename)  # type: ignore
            print(f"Downloaded PDF for {paper.title} to {filename}")
        except Exception as e:
            print(f"Error downloading PDF for {paper.title}: {e}")


if __name__ == "__main__":
    # Example usage
    client = arxiv.Client()
    paper_ids = ["2407.10173", "1706.03762"]
    papers, _ = get_arxiv_paper_by_ids(paper_ids, client)
    if papers:
        print("Downloading PDFs...")
        download_arxiv_papers_pdf(papers, "./data/pdf")
    else:
        print("No papers found.")
