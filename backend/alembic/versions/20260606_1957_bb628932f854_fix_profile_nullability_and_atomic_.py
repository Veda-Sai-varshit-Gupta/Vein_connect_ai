"""fix_profile_nullability_and_atomic_signup

Revision ID: bb628932f854
Revises: 3b17b226578e
Create Date: 2026-06-06 19:57:06.096465+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb628932f854'
down_revision: Union[str, None] = '3b17b226578e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- patients nullability & constraints ---
    op.alter_column('patients', 'name', existing_type=sa.String(length=255), nullable=True)
    op.alter_column('patients', 'age', existing_type=sa.Integer(), nullable=True)
    op.alter_column('patients', 'gender', existing_type=sa.Enum('male', 'female', 'other', name='gender'), nullable=True)
    op.alter_column('patients', 'blood_group', existing_type=sa.Enum('A_POS', 'A_NEG', 'B_POS', 'B_NEG', 'AB_POS', 'AB_NEG', 'O_POS', 'O_NEG', name='bloodgroup'), nullable=True)
    op.alter_column('patients', 'thalassemia_type', existing_type=sa.Enum('major', 'intermedia', 'minor', 'hb_e', 'hb_s', name='thalassemiatype'), nullable=True)
    
    op.drop_constraint('ck_patients_age_positive', 'patients', type_='check')
    op.create_check_constraint('ck_patients_age_positive', 'patients', 'age IS NULL OR age > 0')

    # --- donors nullability & constraints ---
    op.alter_column('donors', 'name', existing_type=sa.String(length=255), nullable=True)
    op.alter_column('donors', 'age', existing_type=sa.Integer(), nullable=True)
    op.alter_column('donors', 'gender', existing_type=sa.Enum('male', 'female', 'other', name='gender'), nullable=True)
    op.alter_column('donors', 'blood_group', existing_type=sa.Enum('A_POS', 'A_NEG', 'B_POS', 'B_NEG', 'AB_POS', 'AB_NEG', 'O_POS', 'O_NEG', name='bloodgroup'), nullable=True)
    
    op.drop_constraint('ck_donors_age_min_18', 'donors', type_='check')
    op.create_check_constraint('ck_donors_age_min_18', 'donors', 'age IS NULL OR age >= 18')

    # --- coordinators nullability ---
    op.alter_column('coordinators', 'name', existing_type=sa.String(length=255), nullable=True)
    op.alter_column('coordinators', 'phone', existing_type=sa.String(length=20), nullable=True)

    # --- hospitals nullability ---
    op.alter_column('hospitals', 'name', existing_type=sa.String(length=255), nullable=True)
    op.alter_column('hospitals', 'registration_number', existing_type=sa.String(length=100), nullable=True)
    op.alter_column('hospitals', 'address', existing_type=sa.String(length=500), nullable=True)
    op.alter_column('hospitals', 'city', existing_type=sa.String(length=100), nullable=True)
    op.alter_column('hospitals', 'state', existing_type=sa.String(length=100), nullable=True)


def downgrade() -> None:
    # --- hospitals nullability ---
    op.alter_column('hospitals', 'state', existing_type=sa.String(length=100), nullable=False)
    op.alter_column('hospitals', 'city', existing_type=sa.String(length=100), nullable=False)
    op.alter_column('hospitals', 'address', existing_type=sa.String(length=500), nullable=False)
    op.alter_column('hospitals', 'registration_number', existing_type=sa.String(length=100), nullable=False)
    op.alter_column('hospitals', 'name', existing_type=sa.String(length=255), nullable=False)

    # --- coordinators nullability ---
    op.alter_column('coordinators', 'phone', existing_type=sa.String(length=20), nullable=False)
    op.alter_column('coordinators', 'name', existing_type=sa.String(length=255), nullable=False)

    # --- donors nullability & constraints ---
    op.drop_constraint('ck_donors_age_min_18', 'donors', type_='check')
    op.create_check_constraint('ck_donors_age_min_18', 'donors', 'age >= 18')

    op.alter_column('donors', 'blood_group', existing_type=sa.Enum('A_POS', 'A_NEG', 'B_POS', 'B_NEG', 'AB_POS', 'AB_NEG', 'O_POS', 'O_NEG', name='bloodgroup'), nullable=False)
    op.alter_column('donors', 'gender', existing_type=sa.Enum('male', 'female', 'other', name='gender'), nullable=False)
    op.alter_column('donors', 'age', existing_type=sa.Integer(), nullable=False)
    op.alter_column('donors', 'name', existing_type=sa.String(length=255), nullable=False)

    # --- patients nullability & constraints ---
    op.drop_constraint('ck_patients_age_positive', 'patients', type_='check')
    op.create_check_constraint('ck_patients_age_positive', 'patients', 'age > 0')

    op.alter_column('patients', 'thalassemia_type', existing_type=sa.Enum('major', 'intermedia', 'minor', 'hb_e', 'hb_s', name='thalassemiatype'), nullable=False)
    op.alter_column('patients', 'blood_group', existing_type=sa.Enum('A_POS', 'A_NEG', 'B_POS', 'B_NEG', 'AB_POS', 'AB_NEG', 'O_POS', 'O_NEG', name='bloodgroup'), nullable=False)
    op.alter_column('patients', 'gender', existing_type=sa.Enum('male', 'female', 'other', name='gender'), nullable=False)
    op.alter_column('patients', 'age', existing_type=sa.Integer(), nullable=False)
    op.alter_column('patients', 'name', existing_type=sa.String(length=255), nullable=False)
