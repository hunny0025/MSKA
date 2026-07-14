"""
Document relationship analyzer.
"""

from typing import List, Dict, Any
from models.document import Document


class RelationshipAnalyzer:
    """
    Derives semantic and version links between documents.
    """

    def analyze_relationships(
        self, 
        target_doc: Document, 
        all_docs: List[Document]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Calculates relations for a specific document.
        - supersedes: older versions of the same file name.
        - superseded_by: newer versions of the same file name.
        - related: documents in the same project scope.
        """
        supersedes = []
        superseded_by = []
        related = []

        for doc in all_docs:
            if doc.id == target_doc.id:
                continue

            # Versioning links
            if doc.filename == target_doc.filename:
                if doc.version < target_doc.version:
                    supersedes.append({
                        "id": doc.id,
                        "filename": doc.filename,
                        "version": f"v{doc.version}",
                        "status": doc.status
                    })
                elif doc.version > target_doc.version:
                    superseded_by.append({
                        "id": doc.id,
                        "filename": doc.filename,
                        "version": f"v{doc.version}",
                        "status": doc.status
                    })
            # Scoped links
            elif doc.project_id == target_doc.project_id:
                related.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "version": f"v{doc.version}",
                    "classification": doc.classification
                })

        return {
            "supersedes": supersedes,
            "superseded_by": superseded_by,
            "related": related[:5]  # Cap related links list
        }


relationship_analyzer = RelationshipAnalyzer()
