-- ===================================================================================
-- MAARS Lens: Production Statutory Rules Seed (Verified Rules Migration)
--
-- IMPORTANT NOTICES:
-- 1. THIS SCRIPT IS SEPARATE FROM SCHEMA DEFINITIONS (001_initial_schema.sql)
--    AND DEMO SEED FIXTURES (seed_demo_rules.sql).
-- 2. ALL RULES SEEDED HERE MUST BE STATUTORY AND MARKED verification_status = 'verified'.
-- 3. DO NOT CONFLATE WITH DEMO RULES. Demo rules use verification_status = 'demo'.
-- 4. INSERTION TARGET: Replace the placeholder comment block below with the verified
--    Legal Metrology statutory rule entries provided tomorrow morning.
-- ===================================================================================

DO $$
DECLARE
    v_admin_id UUID;
BEGIN
    -- 1. Validate that an active admin profile exists to author the verified rule versions.
    SELECT id INTO v_admin_id 
    FROM profiles 
    WHERE role = 'admin' AND is_active = true 
    ORDER BY created_at ASC 
    LIMIT 1;
    
    IF v_admin_id IS NULL THEN
        RAISE EXCEPTION 'Cannot seed statutory rules: No active admin profile found in the "profiles" table. Please create a valid administrator account first.';
    END IF;

    -- ===============================================================================
    -- PLACEHOLDER: INSERT VERIFIED STATUTORY RULES HERE TOMORROW MORNING
    -- Format:
    --
    -- INSERT INTO compliance_rules (id, rule_code, category)
    -- VALUES
    --     ('...', 'PCR-2011-RULE-XX', 'Category Name')
    -- ON CONFLICT (rule_code) DO NOTHING;
    --
    -- INSERT INTO compliance_rule_versions (
    --     id,
    --     rule_id,
    --     version,
    --     statutory_reference,
    --     rule_type,
    --     target_field,
    --     check_definition,
    --     severity,
    --     description_en,
    --     description_hi,
    --     failure_message_template,
    --     requires_visual_measurement,
    --     measurement_unit,
    --     verification_status,
    --     is_active,
    --     created_by
    -- ) VALUES (
    --     '...',
    --     '...',
    --     1,
    --     'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule XX',
    --     'presence' | 'pattern' | 'computed' | 'visual',
    --     'field_name',
    --     '{"operator": "exists"}'::jsonb,
    --     'critical' | 'major' | 'minor' | 'info',
    --     'English description',
    --     'Hindi description (optional)',
    --     'Failure message template',
    --     false,
    --     NULL,
    --     'verified', -- MUST BE 'verified'
    --     true,
    --     v_admin_id
    -- ) ON CONFLICT (rule_id, version) DO NOTHING;
    -- ===============================================================================

    RAISE NOTICE 'Statutory rules seed script executed successfully. Admin profile % used as author.', v_admin_id;
END $$;
