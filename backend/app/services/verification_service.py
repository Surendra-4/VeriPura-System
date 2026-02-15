import hashlib
from collections import Counter

from app.infra.batch_id import BatchIDGenerator
from app.infra.ledger import Ledger
from app.infra.qr_generator import QRGenerator
from app.logger import logger
from app.schemas.consistency_graph import ConsistencyGraphResponse, GraphEdge, GraphNode
from app.schemas.ledger import (
    DocumentMetadataSummary,
    ExtractedEntityFields,
    LedgerRecord,
    ValidationResultSummary,
)
from app.schemas.upload import FileMetadata
from app.schemas.validation import ValidationResponse


class VerificationService:
    """
    Service layer for verification and ledger operations.
    Orchestrates batch ID generation and ledger writes.
    """

    def __init__(self):
        self.ledger = Ledger()
        self.batch_id_generator = BatchIDGenerator()
        self.qr_generator = QRGenerator()

    @staticmethod
    def _normalize_scalar(value: str | None) -> tuple[str | None, str | None]:
        if value is None:
            return None, None

        cleaned = " ".join(value.strip().split())
        if not cleaned:
            return None, None

        return cleaned.lower(), cleaned

    @staticmethod
    def _normalize_dates(dates: list[str] | None) -> tuple[str | None, str | None]:
        if not dates:
            return None, None

        cleaned = [d.strip() for d in dates if d and d.strip()]
        if not cleaned:
            return None, None

        unique = list(dict.fromkeys(cleaned))
        return "|".join(sorted(unique)), ", ".join(unique)

    @staticmethod
    def _choose_consensus(values: list[str]) -> str | None:
        if not values:
            return None

        counts = Counter(values)
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return ranked[0][0]

    @staticmethod
    def _entity_node_id(field_name: str, normalized_value: str) -> str:
        if normalized_value == "__missing__":
            return f"entity:{field_name}:missing"

        digest = hashlib.sha1(f"{field_name}:{normalized_value}".encode("utf-8")).hexdigest()[:10]
        return f"entity:{field_name}:{digest}"

    async def record_verification(
        self, metadata: FileMetadata, validation: ValidationResponse
    ) -> LedgerRecord:
        """
        Record a verification event in the ledger.

        Args:
            metadata: File metadata from upload
            validation: Validation result from ML pipeline

        Returns:
            LedgerRecord that was written
        """
        # Generate batch ID
        batch_id = self.batch_id_generator.generate()

        logger.info(f"Recording verification: {batch_id}")

        # Prepare summaries for ledger
        doc_summary = DocumentMetadataSummary(
            original_filename=metadata.original_filename,
            file_size=metadata.file_size,
            document_type=metadata.document_type.value,
            mime_type=metadata.mime_type,
            extracted_entities=ExtractedEntityFields(
                batch_id=validation.structured_fields.batch_id,
                exporter=validation.structured_fields.exporter,
                quantity=validation.structured_fields.quantity,
                dates=validation.structured_fields.dates,
                certificate_id=validation.structured_fields.certificate_id,
            ),
        )

        validation_summary = ValidationResultSummary(
            fraud_score=validation.fraud_score,
            risk_level=validation.risk_level,
            is_anomaly=validation.is_anomaly,
            rule_violation_count=len(validation.rule_violations),
        )

        # Append to ledger
        record = await self.ledger.append_record(
            batch_id=batch_id,
            file_id=metadata.file_id,
            document_metadata=doc_summary,
            validation_result=validation_summary,
        )

        # Generate QR code (ADD THIS BLOCK)
        try:
            self.qr_generator.generate(batch_id)
            logger.info(f"QR code generated for {batch_id}")
        except Exception as e:
            # Log error but don't fail the entire verification
            # QR can be generated on-demand later
            logger.error(f"QR generation failed for {batch_id}: {str(e)}")

        return record

    async def get_verification_by_batch_id(self, batch_id: str) -> LedgerRecord:
        """
        Retrieve verification record by batch ID.

        Raises:
            ValueError: If batch ID not found
        """
        record = await self.ledger.get_record_by_batch_id(batch_id)

        if record is None:
            raise ValueError(f"Batch ID not found: {batch_id}")

        return record

    async def verify_ledger_integrity(self):
        """
        Verify entire ledger integrity.

        Returns:
            LedgerIntegrityReport
        """
        return await self.ledger.verify_integrity()

    async def get_consistency_graph(self, shipment_id: str) -> ConsistencyGraphResponse:
        """
        Build consistency graph for all records associated with a shipment ID.
        """
        all_records = await self.ledger.get_all_records(limit=10000)

        matching_records = [
            record
            for record in all_records
            if record.batch_id == shipment_id
            or record.document_metadata.extracted_entities.batch_id == shipment_id
        ]

        if not matching_records:
            raise ValueError(f"Shipment not found: {shipment_id}")

        grouped_batch_ids = {
            record.document_metadata.extracted_entities.batch_id
            for record in matching_records
            if record.document_metadata.extracted_entities.batch_id
        }
        if grouped_batch_ids:
            for record in all_records:
                if record in matching_records:
                    continue
                if record.document_metadata.extracted_entities.batch_id in grouped_batch_ids:
                    matching_records.append(record)

        fields = ["batch_id", "exporter", "quantity", "dates", "certificate_id"]
        field_values: dict[str, list[str]] = {field: [] for field in fields}
        display_values: dict[str, dict[str, str]] = {field: {} for field in fields}
        per_doc_values: dict[str, dict[str, tuple[str | None, str | None]]] = {}

        for record in matching_records:
            extracted = record.document_metadata.extracted_entities
            doc_values: dict[str, tuple[str | None, str | None]] = {}

            scalar_fields = {
                "batch_id": extracted.batch_id,
                "exporter": extracted.exporter,
                "quantity": extracted.quantity,
                "certificate_id": extracted.certificate_id,
            }
            for field_name, raw_value in scalar_fields.items():
                normalized, display = self._normalize_scalar(raw_value)
                doc_values[field_name] = (normalized, display)
                if normalized is not None:
                    field_values[field_name].append(normalized)
                    display_values[field_name][normalized] = display or normalized

            normalized_dates, display_dates = self._normalize_dates(extracted.dates)
            doc_values["dates"] = (normalized_dates, display_dates)
            if normalized_dates is not None:
                field_values["dates"].append(normalized_dates)
                display_values["dates"][normalized_dates] = display_dates or normalized_dates

            per_doc_values[record.batch_id] = doc_values

        consensus = {
            field_name: self._choose_consensus(values) for field_name, values in field_values.items()
        }

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        node_ids: set[str] = set()

        for record in matching_records:
            doc_node_id = f"document:{record.batch_id}"
            if doc_node_id not in node_ids:
                nodes.append(
                    GraphNode(
                        id=doc_node_id,
                        label=record.document_metadata.original_filename,
                        node_type="document",
                        metadata={
                            "record_batch_id": record.batch_id,
                            "timestamp": record.timestamp.isoformat(),
                        },
                    )
                )
                node_ids.add(doc_node_id)

            for field_name in fields:
                normalized_value, display_value = per_doc_values[record.batch_id][field_name]

                if normalized_value is None:
                    entity_norm = "__missing__"
                    entity_label = f"Missing {field_name}"
                    edge_type = "MISMATCH"
                    explanation = (
                        f"{field_name} was not extracted from document "
                        f"'{record.document_metadata.original_filename}'."
                    )
                else:
                    entity_norm = normalized_value
                    entity_label = display_value or normalized_value
                    expected = consensus[field_name]
                    if expected is None:
                        edge_type = "MATCH"
                        explanation = (
                            f"Only one value for {field_name} is available "
                            "in this shipment group."
                        )
                    elif normalized_value == expected:
                        edge_type = "MATCH"
                        expected_display = display_values[field_name].get(expected, expected)
                        explanation = (
                            f"{field_name} matches shipment value '{expected_display}'."
                        )
                    else:
                        edge_type = "MISMATCH"
                        expected_display = display_values[field_name].get(expected, expected)
                        explanation = (
                            f"{field_name} value '{display_value}' does not match "
                            f"shipment value '{expected_display}'."
                        )

                entity_node_id = self._entity_node_id(field_name, entity_norm)
                if entity_node_id not in node_ids:
                    nodes.append(
                        GraphNode(
                            id=entity_node_id,
                            label=entity_label,
                            node_type="entity",
                            metadata={"field_name": field_name, "value": entity_label},
                        )
                    )
                    node_ids.add(entity_node_id)

                edges.append(
                    GraphEdge(
                        id=f"edge:{record.batch_id}:{field_name}",
                        source=doc_node_id,
                        target=entity_node_id,
                        type=edge_type,
                        field_name=field_name,
                        explanation=explanation,
                    )
                )

        return ConsistencyGraphResponse(shipment_id=shipment_id, nodes=nodes, edges=edges)
