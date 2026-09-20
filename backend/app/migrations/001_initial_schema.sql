CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enums
CREATE TYPE user_role AS ENUM ('officer', 'admin', 'retailer');
CREATE TYPE contact_channel_type AS ENUM ('email', 'phone', 'none');
CREATE TYPE area_type AS ENUM ('area', 'ward', 'district');
CREATE TYPE inspection_status AS ENUM ('pending_quality_check', 'quality_rejected', 'processing', 'completed', 'needs_review', 'failed');
CREATE TYPE compliance_status AS ENUM ('compliant', 'non_compliant', 'needs_review');
CREATE TYPE public_compliance_status AS ENUM ('compliant', 'non_compliant', 'under_review', 'resolved');
CREATE TYPE inspection_source AS ENUM ('officer');
CREATE TYPE rule_type AS ENUM ('presence', 'pattern', 'computed', 'visual');
CREATE TYPE severity_level AS ENUM ('critical', 'major', 'minor', 'info');
CREATE TYPE rule_verification_status AS ENUM ('demo', 'verified');
CREATE TYPE rule_audit_action AS ENUM ('created', 'updated', 'activated', 'deactivated');
CREATE TYPE audit_result_type AS ENUM ('pass', 'fail', 'needs_review', 'not_applicable');
CREATE TYPE violation_status AS ENUM ('open', 'under_review', 'appealed', 'resolved', 'dismissed');
CREATE TYPE appeal_status AS ENUM ('submitted', 'under_review', 'accepted', 'rejected');
CREATE TYPE notification_type AS ENUM ('violation_new', 'violation_resolved', 'appeal_submitted', 'appeal_outcome', 'report_assigned', 'report_resolved', 'system');
CREATE TYPE email_status AS ENUM ('pending', 'sent', 'failed');

-- 1. Profiles (1:1 with Supabase auth.users)
CREATE TABLE profiles (
    id UUID PRIMARY KEY, -- Matches Supabase auth.users.id
    role user_role NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(32),
    email VARCHAR(255),
    employee_id VARCHAR(64),
    is_active BOOLEAN DEFAULT true,
    onboarding_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_profiles_employee_id ON profiles (employee_id) WHERE employee_id IS NOT NULL;

-- 2. Areas (Hierarchical: district -> ward -> area)
CREATE TABLE areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    area_type area_type NOT NULL,
    parent_id UUID REFERENCES areas(id) ON DELETE RESTRICT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Retailers (Business profile)
CREATE TABLE retailers (
    id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    business_name VARCHAR(255) NOT NULL,
    shop_address TEXT NOT NULL,
    area_id UUID NOT NULL REFERENCES areas(id) ON DELETE RESTRICT,
    license_number VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. Customers (Anonymous auth with separate contact channel)
CREATE TABLE customers (
    id UUID PRIMARY KEY, -- Matches Supabase auth.users.id (Anonymous Auth session)
    customer_code VARCHAR(32) NOT NULL UNIQUE, -- Human-readable reference code only
    contact_channel_encrypted BYTEA, -- Standard AES-256-GCM envelope
    contact_channel_type contact_channel_type DEFAULT 'none',
    onboarding_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. Officer Area Assignments
CREATE TABLE officer_area_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    officer_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    area_id UUID NOT NULL REFERENCES areas(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    CONSTRAINT uq_officer_area UNIQUE(officer_id, area_id)
);

-- 6. Officer Signatures (Historical archive with single active signature)
CREATE TABLE officer_signatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    officer_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    signature_storage_path TEXT NOT NULL,
    signature_hash VARCHAR(64) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_active_officer_signature ON officer_signatures (officer_id) WHERE is_active = true;

-- 7. Compliance Rules (Logical identity)
CREATE TABLE compliance_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_code VARCHAR(64) NOT NULL UNIQUE,
    category VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 8. Compliance Rule Versions (Immutable version snapshots)
CREATE TABLE compliance_rule_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID NOT NULL REFERENCES compliance_rules(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    statutory_reference TEXT NOT NULL,
    rule_type rule_type NOT NULL,
    target_field VARCHAR(64) NOT NULL,
    check_definition JSONB NOT NULL,
    severity severity_level NOT NULL,
    description_en TEXT NOT NULL,
    description_hi TEXT,
    failure_message_template TEXT NOT NULL,
    requires_visual_measurement BOOLEAN DEFAULT false,
    measurement_unit VARCHAR(16),
    verification_status rule_verification_status NOT NULL DEFAULT 'demo',
    is_active BOOLEAN DEFAULT true,
    created_by UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_rule_version UNIQUE (rule_id, version)
);

-- 9. Rule Audit Logs
CREATE TABLE rule_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID NOT NULL REFERENCES compliance_rules(id) ON DELETE CASCADE,
    action rule_audit_action NOT NULL,
    changed_by UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    old_values JSONB,
    new_values JSONB NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 10. Customer Reports (Citizen submissions - strict privacy boundaries)
CREATE TABLE customer_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    image_storage_path TEXT NOT NULL,
    description TEXT NOT NULL, -- Internal investigation only; never exposed publicly
    product_name VARCHAR(255),
    area_id UUID REFERENCES areas(id) ON DELETE SET NULL,
    gps_lat DOUBLE PRECISION, -- Internal investigation only; never exposed publicly
    gps_lng DOUBLE PRECISION, -- Internal investigation only; never exposed publicly
    status VARCHAR(32) DEFAULT 'submitted',
    assigned_officer_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    resolution_summary TEXT, -- Sanitized feedback for citizen
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 11. Inspections (Core audit record)
CREATE TABLE inspections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_submission_id UUID NOT NULL UNIQUE, -- Offline idempotency key
    officer_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    retailer_id UUID REFERENCES retailers(id) ON DELETE SET NULL,
    area_id UUID NOT NULL REFERENCES areas(id) ON DELETE RESTRICT,
    gps_lat DOUBLE PRECISION,
    gps_lng DOUBLE PRECISION,
    image_storage_path TEXT NOT NULL,
    image_original_filename TEXT,
    product_name VARCHAR(255),
    brand_name VARCHAR(255),
    status inspection_status DEFAULT 'pending_quality_check',
    automated_compliance compliance_status, -- Immutable engine output
    final_compliance compliance_status, -- Aggregated verdict
    extracted_facts JSONB,
    ocr_raw_text TEXT,
    ocr_confidence_overall REAL,
    ocr_field_confidences JSONB,
    visual_measurements JSONB,
    officer_notes TEXT,
    is_finalized BOOLEAN DEFAULT false,
    finalized_at TIMESTAMPTZ,
    signature_id UUID REFERENCES officer_signatures(id) ON DELETE RESTRICT,
    signature_hash_at_finalization VARCHAR(64),
    report_hash VARCHAR(71), -- sha256:...
    report_storage_path TEXT,
    source inspection_source DEFAULT 'officer',
    triggered_by_report_id UUID REFERENCES customer_reports(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 12. Image Quality Assessments
CREATE TABLE image_quality_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inspection_id UUID NOT NULL UNIQUE REFERENCES inspections(id) ON DELETE CASCADE,
    is_acceptable BOOLEAN NOT NULL,
    is_borderline BOOLEAN DEFAULT false,
    overall_quality_score REAL,
    issues JSONB DEFAULT '[]'::jsonb,
    preprocessing_applied JSONB,
    assessed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 13. Audit Results (Evaluation flow: automated_result -> manual_review_result -> effective_result)
CREATE TABLE audit_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inspection_id UUID NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    rule_version_id UUID NOT NULL REFERENCES compliance_rule_versions(id) ON DELETE RESTRICT,
    rule_code VARCHAR(64) NOT NULL,
    rule_version INTEGER NOT NULL,
    statutory_reference TEXT NOT NULL,
    automated_result audit_result_type NOT NULL, -- Immutable engine output
    actual_value TEXT,
    expected_value TEXT,
    fact_confidence REAL,
    measurement_reliable BOOLEAN,
    automated_reason TEXT NOT NULL,
    severity severity_level NOT NULL,
    manual_review_result audit_result_type, -- Separate officer assessment
    manual_review_reason TEXT,
    manual_reviewed_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    manual_reviewed_at TIMESTAMPTZ,
    effective_result audit_result_type NOT NULL, -- manual_review_result ?? automated_result
    evaluated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_audit_result_inspection_rule_version UNIQUE(inspection_id, rule_version_id)
);

-- 14. Violations
CREATE TABLE violations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inspection_id UUID NOT NULL UNIQUE REFERENCES inspections(id) ON DELETE RESTRICT,
    retailer_id UUID REFERENCES retailers(id) ON DELETE SET NULL,
    area_id UUID NOT NULL REFERENCES areas(id) ON DELETE RESTRICT,
    officer_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    status violation_status DEFAULT 'open',
    failing_rule_codes VARCHAR(64)[] NOT NULL,
    summary TEXT NOT NULL,
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 15. Appeals
CREATE TABLE appeals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    violation_id UUID NOT NULL REFERENCES violations(id) ON DELETE CASCADE,
    retailer_id UUID NOT NULL REFERENCES retailers(id) ON DELETE RESTRICT,
    appeal_text TEXT NOT NULL,
    evidence_storage_paths TEXT[] DEFAULT ARRAY[]::TEXT[],
    status appeal_status DEFAULT 'submitted',
    reviewed_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    review_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 16. Public Compliance Records (Sanitized public safe view; retention protected)
CREATE TABLE public_compliance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inspection_id UUID NOT NULL UNIQUE REFERENCES inspections(id) ON DELETE RESTRICT,
    product_name VARCHAR(255),
    brand_name VARCHAR(255),
    area_id UUID REFERENCES areas(id) ON DELETE SET NULL,
    compliance_status public_compliance_status NOT NULL,
    last_verified_date TIMESTAMPTZ NOT NULL,
    public_checks JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 17. Notifications
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- Maps to auth.users.id
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type notification_type NOT NULL,
    reference_type VARCHAR(64),
    reference_id UUID,
    is_read BOOLEAN DEFAULT false,
    email_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 18. Email Queue
CREATE TABLE email_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    to_email_encrypted BYTEA NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body_html TEXT NOT NULL,
    status email_status DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    related_notification_id UUID REFERENCES notifications(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMPTZ
);

-- Performance & Integrity Indexes
CREATE INDEX idx_inspections_officer_id ON inspections(officer_id);
CREATE INDEX idx_inspections_retailer_id ON inspections(retailer_id);
CREATE INDEX idx_inspections_area_id ON inspections(area_id);
CREATE INDEX idx_inspections_status ON inspections(status);
CREATE INDEX idx_inspections_created_at ON inspections(created_at);

CREATE INDEX idx_audit_results_inspection_id ON audit_results(inspection_id);
CREATE INDEX idx_audit_results_rule_version_id ON audit_results(rule_version_id);

CREATE INDEX idx_violations_officer_id ON violations(officer_id);
CREATE INDEX idx_violations_retailer_id ON violations(retailer_id);
CREATE INDEX idx_violations_status ON violations(status);

CREATE INDEX idx_appeals_violation_id ON appeals(violation_id);
CREATE INDEX idx_appeals_status ON appeals(status);

CREATE INDEX idx_notifications_user_id_unread ON notifications(user_id) WHERE is_read = false;

CREATE INDEX idx_public_compliance_product ON public_compliance_records(product_name);
CREATE INDEX idx_public_compliance_brand ON public_compliance_records(brand_name);
CREATE INDEX idx_public_compliance_status ON public_compliance_records(compliance_status);

