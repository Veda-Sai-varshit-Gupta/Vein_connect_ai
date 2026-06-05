// ── VeinConnect AI — Global TypeScript Types ────────────────────────────────

export type UserRole = "patient" | "donor" | "coordinator" | "hospital" | "admin";

export type BloodGroup = "A+" | "A-" | "B+" | "B-" | "AB+" | "AB-" | "O+" | "O-";

export type ThalassemiaType = "major" | "intermedia" | "minor" | "hb_e" | "hb_s";

export type TransfusionStatus =
  | "predicted"
  | "patient_confirmed"
  | "matching_donors"
  | "donor_confirmed"
  | "coordinator_confirmed"
  | "hospital_confirmed"
  | "scheduled"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "failed";

export type UrgencyLevel = "routine" | "urgent" | "emergency";

export type IncidentSeverity = "low" | "medium" | "high" | "critical";

export type IncidentStatus = "open" | "investigating" | "resolved";

export interface User {
  id: string;
  email: string;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  is_onboarded?: boolean;
}

export interface Patient {
  id: string;
  user_id: string;
  name: string;
  age: number;
  gender: string;
  blood_group: BloodGroup;
  thalassemia_type: ThalassemiaType;
  avg_transfusion_interval_days: number;
  last_transfusion_date: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  consents_data_sharing: boolean;
  consents_emergency_escalation: boolean;
}

export interface Donor {
  id: string;
  user_id: string;
  name: string;
  age: number;
  gender: string;
  blood_group: BloodGroup;
  last_donation_date: string | null;
  is_available: boolean;
  upi_id: string | null;
  max_travel_distance_km: number;
  preferred_days: string[];
  preferred_times: string[];
  preferred_language: string;
  notification_channels: string[];
  location_lat: number | null;
  location_lng: number | null;
  reliability_score: number;
  medical_clearance_url?: string | null;
  medical_clearance_at?: string | null;
}

export interface Coordinator {
  id: string;
  user_id: string;
  name: string;
  organization: string;
  assigned_region: string;
  is_approved: boolean;
}

export interface Hospital {
  id: string;
  user_id: string;
  name: string;
  registration_number: string;
  address: string;
  city: string;
  state: string;
  operating_hours_start: string;
  operating_hours_end: string;
  location_lat: number | null;
  location_lng: number | null;
  contact_name: string | null;
  contact_phone: string | null;
  is_active: boolean;
}

export interface Transfusion {
  id: string;
  patient_id: string;
  hospital_id: string;
  donor_id: string | null;
  status: TransfusionStatus;
  urgency_level: UrgencyLevel;
  scheduled_date: string;
  completed_at: string | null;
  cancellation_reason: string | null;
  patient?: Patient;
  hospital?: Hospital;
  donor?: Donor;
  coordinator?: any;
  friendship_score?: number | null;
}

export interface Confirmation {
  id: string;
  transfusion_id: string;
  actor_role: UserRole;
  actor_id: string;
  is_confirmed: boolean;
  confirmed_at: string | null;
  rejection_reason: string | null;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  content: string;
  category: string;
  is_read: boolean;
  created_at: string;
}

export interface Wallet {
  id: string;
  user_id: string;
  balance: number;
  total_credits: number;
  total_debits: number;
  updated_at: string;
}

export interface WalletTransaction {
  id: string;
  wallet_id: string;
  amount: number;
  transaction_type: "credit" | "debit";
  description: string;
  reference_type: string | null;
  reference_id: string | null;
  created_at: string;
}

export interface Reward {
  id: string;
  donor_id: string;
  points_balance: number;
  lifetime_points: number;
  tier: "bronze" | "silver" | "gold" | "platinum";
}

export interface FriendshipScore {
  id: string;
  patient_id: string;
  donor_id: string;
  score: number;
  total_shared_transfusions: number;
  last_interaction_date: string;
}

export interface Incident {
  id: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  category: string;
  description: string;
  transfusion_id: string | null;
  affected_component: string;
  created_at: string;
  resolved_at: string | null;
}
