# ============================================================
# Cobalt Hospitality Tech — Research Task Definitions
# Project 5: Multi-Agent Research System
#
# This file defines the research task structure.
# Each task is what a subagent receives — nothing more.
#
# EXAM PATTERN: Targeted context passing
# Subagents receive ONLY what they need for their specific task.
# The coordinator's full context is never passed down.
#
# Compare to anti-pattern:
#   ✗ subagent.run(messages=coordinator.full_history)
#   ✓ subagent.run(task=targeted_task_object)
# ============================================================


def build_research_tasks(gm_question: str, property_context: dict) -> list:
    """
    Breaks a GM's complex question into parallel research tasks.
    Each task contains ONLY the context that subagent needs.

    EXAM PATTERN: The coordinator decides task scope.
    Subagents do not see each other's tasks or results.
    Cross-contamination between subagents is an anti-pattern.

    Args:
        gm_question: The original question from the GM
        property_context: Basic property info all tasks need

    Returns:
        List of task dicts — one per subagent
    """

    # Property context is minimal — only what's universally relevant
    # Not the full coordinator context
    property_summary = (
        f"Property: {property_context['name']}, "
        f"{property_context['location']}, "
        f"{property_context['room_count']} rooms, "
        f"Type: {property_context['type']}"
    )

    # -------------------------------------------------------
    # TASK DEFINITIONS
    # Each task is a self-contained research brief.
    # Subagent gets: its task, minimal property context,
    # output schema, and nothing else.
    #
    # Notice what's NOT included:
    #   - The other tasks
    #   - The coordinator's reasoning
    #   - Previous research results
    #   - The full GM question history
    # -------------------------------------------------------

    tasks = [
        {
            "task_id": "revenue_analysis",
            "agent_id": "subagent_1",
            "research_topic": "Revenue Implications",
            "instruction": f"""You are a hospitality revenue analyst.
Research the revenue implications of cruise line partnerships for resort hotels.

Property context: {property_summary}
Original business question: {gm_question}

Your specific research focus: Revenue implications only.
Analyze: revenue sharing models, commission structures, incremental 
revenue opportunities, displacement costs, seasonal revenue impact,
and typical ROI timelines for cruise-hotel partnerships.

Stay focused on revenue. Do not research operations, competition, 
or guest experience — those are handled separately.

Output your findings in the required JSON format.""",

            "output_schema": {
                "key_findings": "list of 3-5 specific revenue findings",
                "revenue_opportunity_estimate": "estimated annual revenue range",
                "primary_risks": "list of top 3 revenue risks",
                "recommendation": "revenue-focused recommendation",
                "confidence": "high|medium|low",
                "sources_consulted": "list of knowledge areas drawn on"
            }
        },

        {
            "task_id": "operational_requirements",
            "agent_id": "subagent_2",
            "research_topic": "Operational Requirements",
            "instruction": f"""You are a hospitality operations specialist.
Research the operational requirements of cruise line partnerships for resort hotels.

Property context: {property_summary}
Original business question: {gm_question}

Your specific research focus: Operational requirements only.
Analyze: staffing requirements, facility modifications needed,
technology integrations (PMS, reservation systems), check-in/out 
process changes, luggage handling, transportation coordination,
and typical implementation timelines.

Stay focused on operations. Do not research revenue, competition,
or guest experience — those are handled separately.

Output your findings in the required JSON format.""",

            "output_schema": {
                "key_findings": "list of 3-5 operational requirements",
                "implementation_timeline": "estimated months to implement",
                "staffing_impact": "FTE additions or role changes needed",
                "technology_requirements": "systems needing integration",
                "primary_risks": "list of top 3 operational risks",
                "confidence": "high|medium|low",
                "sources_consulted": "list of knowledge areas drawn on"
            }
        },

        {
            "task_id": "competitive_landscape",
            "agent_id": "subagent_3",
            "research_topic": "Competitive Landscape",
            "instruction": f"""You are a hospitality competitive intelligence analyst.
Research the competitive landscape for cruise line partnerships in resort hotels.

Property context: {property_summary}
Original business question: {gm_question}

Your specific research focus: Competitive landscape only.
Analyze: which competitor resorts have cruise partnerships,
which cruise lines are most active in hotel partnerships,
market saturation in the Orlando/Florida market, 
first-mover advantages still available, and partnership
exclusivity considerations.

Stay focused on competition. Do not research revenue, operations,
or guest experience — those are handled separately.

Output your findings in the required JSON format.""",

            "output_schema": {
                "key_findings": "list of 3-5 competitive insights",
                "market_saturation": "assessment of market saturation level",
                "key_competitors_with_partnerships": "list of known competitors",
                "recommended_cruise_lines": "best partnership candidates",
                "primary_risks": "list of top 3 competitive risks",
                "confidence": "high|medium|low",
                "sources_consulted": "list of knowledge areas drawn on"
            }
        },

        {
            "task_id": "guest_experience",
            "agent_id": "subagent_4",
            "research_topic": "Guest Experience Impact",
            "instruction": f"""You are a hospitality guest experience specialist.
Research the guest experience impacts of cruise line partnerships for resort hotels.

Property context: {property_summary}
Original business question: {gm_question}

Your specific research focus: Guest experience only.
Analyze: how cruise guests differ from typical resort guests,
amenity and service expectation differences, potential friction
points in the guest journey, loyalty program implications,
review and reputation impacts, and upsell opportunities.

Stay focused on guest experience. Do not research revenue, 
operations, or competition — those are handled separately.

Output your findings in the required JSON format.""",

            "output_schema": {
                "key_findings": "list of 3-5 guest experience insights",
                "guest_profile_differences": "how cruise guests differ",
                "friction_points": "list of potential guest journey issues",
                "upsell_opportunities": "revenue-adjacent guest opportunities",
                "loyalty_impact": "effect on existing loyalty program",
                "primary_risks": "list of top 3 guest experience risks",
                "confidence": "high|medium|low",
                "sources_consulted": "list of knowledge areas drawn on"
            }
        }
    ]

    return tasks


# ============================================================
# PROPERTY CONTEXT
# Minimal context shared across all tasks.
# In production: pulled from your PMS or property database.
# ============================================================

GRAND_PALMS_CONTEXT = {
    "name": "Grand Palms Resort & Spa",
    "location": "Orlando, Florida",
    "room_count": 450,
    "type": "Full-service resort",
    "loyalty_program": "Palms Rewards",
    "star_rating": 4,
    "current_segments": ["leisure", "groups", "corporate"]
}

# The GM's question that drives the research
GM_QUESTION = (
    "We are evaluating a potential partnership with a major cruise line "
    "that would make Grand Palms a preferred pre/post cruise hotel. "
    "Cruise guests would stay 1-2 nights before or after their sailing. "
    "We expect 8,000-12,000 additional room nights annually. "
    "What are the revenue implications, operational requirements, "
    "competitive landscape, and guest experience impacts we should "
    "consider before making this decision?"
)


if __name__ == "__main__":
    tasks = build_research_tasks(GM_QUESTION, GRAND_PALMS_CONTEXT)
    print(f"Generated {len(tasks)} research tasks:")
    for task in tasks:
        print(f"\n  Task: {task['task_id']}")
        print(f"  Agent: {task['agent_id']}")
        print(f"  Topic: {task['research_topic']}")
        print(f"  Instruction length: {len(task['instruction'])} chars")