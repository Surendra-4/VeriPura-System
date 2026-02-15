from fastapi import APIRouter, HTTPException, status

from app.logger import logger
from app.schemas.consistency_graph import ConsistencyGraphResponse
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/api/v1", tags=["Shipments"])


@router.get(
    "/shipments/{shipment_id}/consistency-graph",
    response_model=ConsistencyGraphResponse,
    responses={404: {"description": "Shipment not found"}},
)
async def get_consistency_graph(shipment_id: str):
    """
    Return the shipment consistency graph built from stored extracted entities.
    """
    service = VerificationService()

    try:
        return await service.get_consistency_graph(shipment_id)
    except ValueError as e:
        logger.warning(f"Shipment consistency graph lookup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": str(e)},
        )
