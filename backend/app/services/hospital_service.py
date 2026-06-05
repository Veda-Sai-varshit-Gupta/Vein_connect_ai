"""
Hospital Service
=================
Registration, capacity updates, and schedule queries.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.hospital import Hospital
from app.repositories.hospital_repo import HospitalRepository
from app.schemas.hospital import HospitalCreate, HospitalUpdate, CapacityUpdate
from app.ai.capacity_forecaster import CapacityForecaster

hospital_repo = HospitalRepository()
forecaster = CapacityForecaster()


class HospitalService:

    async def register(self, db: AsyncSession, user_id: UUID, data: HospitalCreate) -> Hospital:
        existing = await hospital_repo.get_by_user_id(db, user_id)
        if existing:
            raise ConflictException("Hospital profile already exists for this account")

        hospital = await hospital_repo.create(db, {
            "user_id": user_id,
            "name": data.name,
            "registration_number": data.registration_number,
            "address": data.address,
            "city": data.city,
            "state": data.state,
            "total_transfusion_beds": data.total_transfusion_beds,
            "total_transfusion_chairs": data.total_transfusion_chairs,
            "emergency_capacity": data.emergency_capacity,
            "coordinator_name": data.coordinator_name,
            "coordinator_email": data.coordinator_email,
            "coordinator_phone": data.coordinator_phone,
            "operating_hours_start": data.operating_hours_start,
            "operating_hours_end": data.operating_hours_end,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "is_active": True,
        })

        # Create initial capacity record
        await hospital_repo.upsert_capacity(db, hospital.id, {
            "available_beds": data.total_transfusion_beds,
            "occupied_beds": 0,
            "available_chairs": data.total_transfusion_chairs,
            "occupied_chairs": 0,
            "staff_available": True,
            "emergency_capacity_available": data.emergency_capacity,
        })
        return hospital

    async def get_hospital(self, db: AsyncSession, hospital_id: UUID) -> Hospital:
        hospital = await hospital_repo.get_by_id(db, hospital_id)
        if not hospital:
            raise NotFoundException("Hospital", str(hospital_id))
        return hospital

    async def update_capacity(self, db: AsyncSession, hospital_id: UUID, data: CapacityUpdate):
        hospital = await hospital_repo.get_by_id(db, hospital_id)
        if not hospital:
            raise NotFoundException("Hospital", str(hospital_id))
            
        total_beds = data.available_beds + data.occupied_beds
        total_chairs = data.available_chairs + data.occupied_chairs
        
        from app.core.exceptions import BadRequestException
        if total_beds > 0 and data.occupied_beds >= total_beds:
            raise BadRequestException("Occupied beds must be less than total beds")
        if total_chairs > 0 and data.occupied_chairs >= total_chairs:
            raise BadRequestException("Occupied chairs must be less than total chairs")
            
        return await hospital_repo.upsert_capacity(db, hospital_id, data.model_dump())

    async def get_capacity(self, db: AsyncSession, hospital_id: UUID):
        cap = await hospital_repo.get_capacity(db, hospital_id)
        if not cap:
            raise NotFoundException("Capacity record for hospital", str(hospital_id))
        return cap

    async def list_hospitals(self, db: AsyncSession, city: str | None = None, skip: int = 0, limit: int = 20):
        if city:
            hospitals = await hospital_repo.get_by_city(db, city)
            return hospitals, len(hospitals)
        hospitals = await hospital_repo.get_all(db, skip=skip, limit=limit)
        total = await hospital_repo.count(db)
        return hospitals, total
