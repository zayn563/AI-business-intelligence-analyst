export type ComparisonKpi = {

    label:
        string;

    current:
        number | null;

    previous?:
        number | null;

    change_pct?:
        number | null;

    change_pp?:
        number | null;

    direction?:
        string;

    unit:
        string;

    actual_sales?:
        number | null;

    sales_target?:
        number | null;

    gap?:
        number | null;
};


export type PriorityEvidence = {

    metric:
        string;

    label:
        string;

    change:
        string;

    direction?:
        string;

    severity?:
        string;

    impact?:
        string;
};


export type EvidenceReferencePeriod = {

    start:
        string;

    end:
        string;
};


export type BusinessPriority = {

    insight_id?:
        number | null;

    fingerprint:
        string;

    lifecycle_status?:
        string | null;

    type:
        "risk"
        |
        "opportunity";

    title:
        string;

    entity:
        string;

    dimension:
        string;

    severity:
        string;

    priority_score:
        number;

    primary_metric:
        string;

    primary_change:
        string;

    direction?:
        string;

    diagnosis?:
        string | null;

    confidence?:
        string | null;

    evidence:
        PriorityEvidence[];

    recommended_action:
        string;

    analyst_question:
        string;

    evidence_status?:
        string | null;

    resolution_allowed?:
        boolean;

    required_datasets?:
        string[];

    blocking_datasets?:
        string[];

    resolution_blocked?:
        boolean;

    resolution_decision?:
        string | null;

    evidence_reference_period?:
        EvidenceReferencePeriod | null;

    evidence_reference_data_through?:
        string | null;

    period_start?:
        string;

    period_end?:
        string;

    comparison_start?:
        string;

    comparison_end?:
        string;

    first_detected_at?:
        string | null;

    last_detected_at?:
        string | null;

    resolved_at?:
        string | null;

    occurrence_count?:
        number;

    actual_sales?:
        number | null;

    sales_target?:
        number | null;

    sales_gap?:
        number | null;
};


export type TrendPoint = {

    month:
        string;

    net_sales:
        number;

    gross_profit:
        number;

    margin_pct:
        number | null;

    units_sold:
        number;
};


export type RegionPerformance = {

    region:
        string;

    net_sales:
        number;

    sales_change_pct:
        number | null;

    target_attainment_pct:
        number | null;
};


export type BusinessBrief = {

    headline:
        string;

    risk_count:
        number;

    current_risk_count?:
        number;

    active_risk_count?:
        number;

    evidence_blocked_risk_count?:
        number;

    opportunity_count:
        number;

    current_opportunity_count?:
        number;

    active_opportunity_count?:
        number;

    evidence_blocked_opportunity_count?:
        number;

    recommended_focus?: {

        title:
            string;

        reason:
            string;

        recommended_action?:
            string;

        insight_id?:
            number | null;

        evidence_status?:
            string | null;

        resolution_blocked?:
            boolean;

        blocking_datasets?:
            string[];

    } | null;

    key_risks:
        Array<{

            insight_id?:
                number | null;

            title:
                string;

            change:
                string;

            status?:
                string | null;

            resolution_blocked?:
                boolean;
        }>;

    key_opportunities:
        Array<{

            insight_id?:
                number | null;

            title:
                string;

            change:
                string;

            resolution_blocked?:
                boolean;
        }>;
};


export type DashboardEvidence = {

    status?:
        string | null;

    reference_data_through?:
        string | null;

    blocking_datasets:
        string[];

    mixed_period_warning:
        boolean;

    blocked_insight_count:
        number;

    blocked_risk_count:
        number;

    blocked_opportunity_count:
        number;
};


export type DashboardSummary = {

    data_through:
        string;

    current_period: {

        start:
            string;

        end:
            string;
    };

    comparison_period: {

        start:
            string;

        end:
            string;
    };

    evidence?:
        DashboardEvidence;

    kpis: {

        net_sales:
            ComparisonKpi;

        gross_profit:
            ComparisonKpi;

        margin_pct:
            ComparisonKpi;

        units_sold:
            ComparisonKpi;

        target_attainment:
            ComparisonKpi;
    };

    brief:
        BusinessBrief;

    priorities: {

        risk_count:
            number;

        active_risk_count?:
            number;

        evidence_blocked_risk_count?:
            number;

        opportunity_count:
            number;

        active_opportunity_count?:
            number;

        evidence_blocked_opportunity_count?:
            number;

        risks:
            BusinessPriority[];

        opportunities:
            BusinessPriority[];
    };

    trend:
        TrendPoint[];

    regions:
        RegionPerformance[];
};


export type AnalystResponse = {

    status?:
        string;

    question?:
        string;

    answer?:
        string;

    parser?:
        string;

    tool_used?:
        string | null;

    used_llm?:
        boolean;

    execution_mode?:
        string;

    response_time_ms?:
        number | null;

    warnings?:
        string[];
};


export type BreakdownRow = {

    entity:
        string;

    current_sales:
        number;

    previous_sales:
        number;

    sales_change:
        number;

    sales_change_pct:
        number | null;

    gross_profit_change:
        number;

    margin_change_pp:
        number | null;

    units_change_pct:
        number | null;
};


export type Recommendation = {

    priority:
        string;

    title:
        string;

    reason:
        string;
};


export type InvestigationResponse = {

    insight:
        BusinessPriority;

    period: {

        current_start:
            string;

        current_end:
            string;

        comparison_start:
            string;

        comparison_end:
            string;
    };

    breakdowns:
        Record<
            string,
            BreakdownRow[]
        >;

    recommendations:
        Recommendation[];
};


export type PriorityListResponse = {

    count:
        number;

    results:
        BusinessPriority[];
};


export type ScenarioResult = {

    scope: {

        dimension:
            string;

        value:
            string;

        start_date:
            string;

        end_date:
            string;
    };

    baseline: {

        net_sales:
            number;

        gross_profit:
            number;

        margin_pct:
            number;

        units_sold:
            number;

        discount_rate_pct:
            number;

        cost_per_unit:
            number;
    };

    scenario: {

        net_sales:
            number;

        gross_profit:
            number;

        margin_pct:
            number;

        units_sold:
            number;

        discount_rate_pct:
            number;

        cost_per_unit:
            number;
    };

    impact: {

        net_sales_change:
            number;

        gross_profit_change:
            number;

        margin_change_pp:
            number;
    };
};


export type PipelineStatusResponse = {

    status?:
        string;

    checked_at?:
        string;

    sources_total?:
        number;

    active_sources?:
        number;

    healthy_sources?:
        number;

    pending_sources?:
        number;

    unhealthy_sources?:
        number;

    sources?:
        Array<
            Record<
                string,
                unknown
            >
        >;
};


export type RefreshAndAnalyzeResponse = {

    status:
        "completed"
        |
        "failed";

    stage?:
        "refresh"
        |
        "intelligence";

    refresh?:
        Record<
            string,
            unknown
        >;

    intelligence?: {

        status?:
            string;

        data_through?:
            string;

        persisted_count?:
            number;

        detected?: {

            risk_count?:
                number;

            opportunity_count?:
                number;
        };

        active?: {

            risk_count?:
                number;

            opportunity_count?:
                number;

            total?:
                number;

            resolution_blocked_count?:
                number;
        };
    };

    detail?:
        string;
};


export type InsightAction = {

    action_id:
        number;

    insight_id:
        number;

    title:
        string;

    owner:
        string | null;

    status:
        "OPEN"
        |
        "IN_PROGRESS"
        |
        "BLOCKED"
        |
        "COMPLETED";

    due_date:
        string | null;

    notes:
        string | null;

    created_at:
        string;

    updated_at:
        string;

    completed_at:
        string | null;
};


export type DashboardData = {

    summary:
        DashboardSummary | null;
};