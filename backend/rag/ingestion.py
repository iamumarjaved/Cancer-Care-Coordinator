"""Data ingestion for RAG pipeline."""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .embeddings import EmbeddingService
from .vector_store import VectorStore


class DataIngestion:
    """Load and index documents into vector stores.

    Handles:
    - Loading mock data from JSON files
    - Chunking documents
    - Metadata extraction
    - Batch indexing
    """

    # Chunking parameters
    DEFAULT_CHUNK_SIZE = 512  # tokens (approx 4 chars per token)
    DEFAULT_OVERLAP = 50

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_stores: Dict[str, VectorStore],
        data_dir: Optional[str] = None
    ):
        """Initialize data ingestion.

        Args:
            embedding_service: Service for generating embeddings
            vector_stores: Dict of namespace -> VectorStore
            data_dir: Directory containing mock data files
        """
        self.embedding_service = embedding_service
        self.vector_stores = vector_stores
        self.logger = logging.getLogger("rag.ingestion")

        # Default data directory
        if data_dir is None:
            self.data_dir = Path(__file__).parent / "mock_data"
        else:
            self.data_dir = Path(data_dir)

    async def load_all_mock_data(self) -> Dict[str, int]:
        """Load all mock data files into vector stores.

        Returns:
            Dict mapping namespace to number of documents indexed
        """
        results = {}

        # Load each data source
        data_sources = [
            ("evidence", "mock_pubmed_articles.json", self._process_pubmed_article),
            ("trials", "mock_clinical_trials.json", self._process_clinical_trial),
            ("genomics", "mock_oncokb_mutations.json", self._process_mutation_entry),
            ("guidelines", "mock_nccn_guidelines.json", self._process_guideline),
        ]

        for namespace, filename, processor in data_sources:
            if namespace not in self.vector_stores:
                self.logger.warning(f"No vector store for namespace: {namespace}")
                continue

            filepath = self.data_dir / filename
            if not filepath.exists():
                self.logger.warning(f"Data file not found: {filepath}")
                results[namespace] = 0
                continue

            count = await self._load_json_file(filepath, namespace, processor)
            results[namespace] = count
            self.logger.info(f"Loaded {count} documents into {namespace}")

        return results

    async def _load_json_file(
        self,
        filepath: Path,
        namespace: str,
        processor: callable
    ) -> int:
        """Load a JSON file and index its contents.

        Args:
            filepath: Path to JSON file
            namespace: Vector store namespace
            processor: Function to process each entry

        Returns:
            Number of documents indexed
        """
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            store = self.vector_stores[namespace]
            count = 0

            for entry in data:
                documents = processor(entry)
                for doc in documents:
                    await store.upsert(
                        doc_id=doc["doc_id"],
                        content=doc["content"],
                        metadata=doc["metadata"]
                    )
                    count += 1

            return count

        except Exception as e:
            self.logger.error(f"Error loading {filepath}: {e}")
            return 0

    def _process_pubmed_article(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a PubMed article entry.

        Args:
            entry: Article data

        Returns:
            List of document chunks
        """
        documents = []

        # Create document ID
        doc_id = f"pubmed_{entry.get('pmid', entry.get('id', 'unknown'))}"

        # Build content
        title = entry.get("title", "")
        abstract = entry.get("abstract", "")
        key_finding = entry.get("key_finding", "")

        full_content = f"{title}\n\n{abstract}\n\nKey Finding: {key_finding}"

        # Chunk if needed
        chunks = self._chunk_text(full_content)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk{i}" if len(chunks) > 1 else doc_id

            documents.append({
                "doc_id": chunk_id,
                "content": chunk,
                "metadata": {
                    "source_type": "pubmed",
                    "pmid": entry.get("pmid"),
                    "title": title,
                    "authors": entry.get("authors", ""),
                    "journal": entry.get("journal", ""),
                    "year": entry.get("year"),
                    "biomarker": entry.get("biomarker"),
                    "cancer_type": entry.get("cancer_type"),
                }
            })

        return documents

    def _process_clinical_trial(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a clinical trial entry.

        Args:
            entry: Trial data

        Returns:
            List of document chunks
        """
        documents = []

        doc_id = f"trial_{entry.get('nct_id', entry.get('id', 'unknown'))}"

        # Build content
        title = entry.get("title", "")
        description = entry.get("description", entry.get("brief_summary", ""))
        intervention = entry.get("intervention", "")
        eligibility = entry.get("eligibility", "")

        full_content = f"""Clinical Trial: {title}

Intervention: {intervention}

Description: {description}

Eligibility: {eligibility}"""

        chunks = self._chunk_text(full_content)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk{i}" if len(chunks) > 1 else doc_id

            documents.append({
                "doc_id": chunk_id,
                "content": chunk,
                "metadata": {
                    "source_type": "clinical_trial",
                    "nct_id": entry.get("nct_id"),
                    "title": title,
                    "phase": entry.get("phase"),
                    "status": entry.get("status"),
                    "sponsor": entry.get("sponsor"),
                    "biomarker": entry.get("biomarker"),
                    "mutations": entry.get("mutations", []),
                    "cancer_type": entry.get("cancer_type"),
                }
            })

        return documents

    def _process_mutation_entry(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a mutation/genomics entry.

        Args:
            entry: Mutation data

        Returns:
            List of document chunks
        """
        documents = []

        gene = entry.get("gene", "unknown")
        variant = entry.get("variant", "unknown")
        doc_id = f"mutation_{gene}_{variant}".replace(" ", "_")

        # Build content
        therapies = entry.get("therapies", [])
        therapy_text = ", ".join(therapies) if therapies else "No targeted therapies"

        content = f"""Gene: {gene}
Variant: {variant}
Classification: {entry.get('classification', 'Unknown')}
Cancer Type: {entry.get('cancer_type', 'Various')}

Targeted Therapies: {therapy_text}

Clinical Significance: {entry.get('clinical_significance', 'See oncologist for interpretation')}

Notes: {entry.get('notes', '')}"""

        documents.append({
            "doc_id": doc_id,
            "content": content,
            "metadata": {
                "source_type": "oncokb",
                "gene": gene,
                "variant": variant,
                "classification": entry.get("classification"),
                "cancer_type": entry.get("cancer_type"),
                "therapies": therapies,
            }
        })

        return documents

    def _process_guideline(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a guideline entry.

        Args:
            entry: Guideline data

        Returns:
            List of document chunks
        """
        documents = []

        doc_id = f"guideline_{entry.get('id', 'unknown')}"

        title = entry.get("title", "")
        content = entry.get("content", entry.get("recommendation", ""))
        evidence_level = entry.get("evidence_level", "")

        full_content = f"""NCCN Guideline: {title}

Evidence Level: {evidence_level}

Recommendation:
{content}

Source: {entry.get('source', 'NCCN Guidelines')}"""

        chunks = self._chunk_text(full_content)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk{i}" if len(chunks) > 1 else doc_id

            documents.append({
                "doc_id": chunk_id,
                "content": chunk,
                "metadata": {
                    "source_type": "nccn_guidelines",
                    "title": title,
                    "cancer_type": entry.get("cancer_type"),
                    "evidence_level": evidence_level,
                    "year": entry.get("year", 2024),
                }
            })

        return documents

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = None,
        overlap: int = None
    ) -> List[str]:
        """Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Max characters per chunk
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE * 4  # chars
        overlap = overlap or self.DEFAULT_OVERLAP * 4

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end near chunk boundary
                for sep in [". ", ".\n", "\n\n"]:
                    last_sep = text.rfind(sep, start + chunk_size // 2, end)
                    if last_sep != -1:
                        end = last_sep + len(sep)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks

    async def index_single_document(
        self,
        namespace: str,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Index a single document.

        Args:
            namespace: Vector store namespace
            doc_id: Document ID
            content: Document content
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if namespace not in self.vector_stores:
            self.logger.error(f"Unknown namespace: {namespace}")
            return False

        store = self.vector_stores[namespace]
        return await store.upsert(doc_id, content, metadata)

    async def clear_namespace(self, namespace: str) -> bool:
        """Clear all documents in a namespace.

        Args:
            namespace: Namespace to clear

        Returns:
            True if successful
        """
        if namespace not in self.vector_stores:
            return False

        return await self.vector_stores[namespace].clear()
