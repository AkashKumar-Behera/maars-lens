-- ===================================================================================
-- MAARS Lens: Optional Demo Rules Seed Fixture
--
-- IMPORTANT NOTICES:
-- 1. THIS SCRIPT IS OPTIONAL AND SEPARATE FROM PRODUCTION SCHEMA MIGRATIONS.
-- 2. THESE RULES ARE DEMO FIXTURES INTENDED ONLY FOR PIPELINE VERIFICATION.
-- 3. THEY DO NOT CONTAIN OR CLAIM TO REPRESENT ACTUAL STATUTORY LEGAL METROLOGY RULES.
-- 4. DO NOT RUN THIS SCRIPT IN A STRICT PRODUCTION ENVIRONMENT WITHOUT REVIEW.
-- ===================================================================================

DO $$
DECLARE
    v_admin_id UUID;
BEGIN
    -- 1. Validate that an active admin profile exists to author the demo rule versions.
    -- This script NEVER creates fake auth users or fabricated admin profiles.
    SELECT id INTO v_admin_id 
    FROM profiles 
    WHERE role = 'admin' AND is_active = true 
    ORDER BY created_at ASC 
    LIMIT 1;
    
    IF v_admin_id IS NULL THEN
        RAISE EXCEPTION 'Cannot seed demo rules: No active admin profile found in the "profiles" table. Please create a valid administrator account first before running this optional demo seed.';
    END IF;

    -- 2. Insert Logical Demo Rules (Idempotent)
    INSERT INTO compliance_rules (id, rule_code, category)
    VALUES 
        ('d0000001-0000-0000-0000-000000000001', 'DEMO-TEST-MRP-PRESENCE', 'MRP'),
        ('d0000001-0000-0000-0000-000000000002', 'DEMO-TEST-NET-QTY', 'Net Quantity'),
        ('d0000001-0000-0000-0000-000000000003', 'DEMO-TEST-MFG-DATE', 'Date Declarations')
    ON CONFLICT (rule_code) DO NOTHING;

    -- 3. Insert Immutable Rule Version 1 for each Demo Rule
    INSERT INTO compliance_rule_versions (
        id,
        rule_id,
        version,
        statutory_reference,
        rule_type,
        target_field,
        check_definition,
        severity,
        description_en,
        failure_message_template,
        requires_visual_measurement,
        verification_status,
        is_active,
        created_by
    ) VALUES 
    (
        'e0000001-0000-0000-0000-000000000001',
        'd0000001-0000-0000-0000-000000000001',
        1,
        '[DEMO FIXTURE - NOT A STATUTORY REQUIREMENT] Pipeline Test Check',
        'presence',
        'mrp',
        '{"operator": "exists"}'::jsonb,
        'critical',
        '[DEMO] Package must have an extracted MRP value for pipeline demonstration.',
        'MRP declaration is missing from extracted package facts.',
        false,
        'demo',
        true,
        v_admin_id
    ),
    (
        'e0000001-0000-0000-0000-000000000002',
        'd0000001-0000-0000-0000-000000000002',
        1,
        '[DEMO FIXTURE - NOT A STATUTORY REQUIREMENT] Pipeline Test Check',
        'presence',
        'net_quantity_g',
        '{"operator": "exists"}'::jsonb,
        'major',
        '[DEMO] Package must have an extracted net quantity for pipeline demonstration.',
        'Net quantity declaration is missing from extracted package facts.',
        false,
        'demo',
        true,
        v_admin_id
    ),
    (
        'e0000001-0000-0000-0000-000000000003',
        'd0000001-0000-0000-0000-000000000003',
        1,
        '[DEMO FIXTURE - NOT A STATUTORY REQUIREMENT] Pipeline Test Check',
        'presence',
        'mfg_date',
        '{"operator": "exists"}'::jsonb,
        'minor',
        '[DEMO] Package must declare manufacturing date for pipeline demonstration.',
        'Manufacturing date declaration is missing from extracted package facts.',
        false,
        'demo',
        true,
        v_admin_id
    )
    ON CONFLICT (rule_id, version) DO NOTHING;
END $$;
