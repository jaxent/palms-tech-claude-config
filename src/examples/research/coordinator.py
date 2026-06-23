# ============================================================
# Cobalt Hospitality Tech — Research Coordinator
# Project 5: Multi-Agent Research System
#
# The coordinator is the hub in a hub-and-spoke architecture.
# It owns:
#   - Task decomposition (done in research_tasks.py)
#   - Parallel subagent dispatch
#   - Failure handling and retry logic
#   - Result collection with provenance
#   - Synthesis into GM-ready recommendation
#
# EXAM PATTERNS:
#   - Targeted context passing (not full history to subagents)
#   - Parallel execution (concurrent subagents)
#   - Structured error propagation (failed subagents reported)
#   - Partial result handling (synthesize with gaps, note them)
#   - Information provenance (every finding attributed)
#   - Human escalation (when critical tracks fail)
# ============================================================

import anthropic
import json
import concurrent.futures
from typing import Optional
from research_tasks import build_research_tasks, GM_QUESTION, GRAND_PALMS_CONTEXT
from subagent import run_subagent

client = anthropic.Anthropic()

# ============================================================
# PARALLEL SUBAGENT DISPATCH
# Runs all subagents concurrently using ThreadPoolExecutor.
#
# EXAM CONCEPT: Parallel vs sequential subagents.
# Sequential: total time = sum of all subagent times
# Parallel: total time = slowest subagent time
#
# For 4 subagents each taking ~15 seconds:
#   Sequential: ~60 seconds
#   Parallel: ~15 seconds
#
# Cost is identical either way — parallelism saves time not tokens.
# ============================================================

def dispatch_subagents_parallel(tasks: list) -> list:
    """
    Dispatches all subagents concurrently.
    Returns list of results in task order.

    Uses ThreadPoolExecutor — each subagent runs in its own thread.
    The Anthropic SDK is thread-safe for concurrent calls.
    """
    print(f"\n[Dispatcher] Launching {len(tasks)} subagents in parallel")

    results = [None] * len(tasks)

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(tasks)) as executor:

        # Submit all tasks
        future_to_index = {
            executor.submit(run_subagent, task): i
            for i, task in enumerate(tasks)
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            task = tasks[index]

            try:
                result = future.result()
                results[index] = result
                status = "✓" if not result.get("isError") else "✗"
                print(f"  [{status}] {task['research_topic']} complete")

            except Exception as e:
                # Thread-level exception — subagent crashed entirely
                print(f"  [✗] {task['research_topic']} crashed: {str(e)}")
                results[index] = {
                    "isError": True,
                    "task_id": task["task_id"],
                    "agent_id": task["agent_id"],
                    "research_topic": task["research_topic"],
                    "errorCategory": "subagent_crash",
                    "isRetryable": True,
                    "context": f"Subagent crashed with exception: {str(e)}",
                    "completedSteps": [],
                    "partialData": None
                }

    return results


# ============================================================
# FAILURE HANDLER
# Evaluates failed subagents and decides: retry or escalate.
#
# EXAM PATTERN: Coordinator owns the failure decision.
# Subagents report failure cleanly — coordinator decides
# what to do with it. Never let subagents make this call.
# ============================================================

def handle_failures(results: list, tasks: list) -> list:
    """
    Retries retryable failures once.
    Returns updated results list.
    """
    failed_indices = [
        i for i, r in enumerate(results)
        if r and r.get("isError") and r.get("isRetryable")
    ]

    if not failed_indices:
        return results

    print(f"\n[Coordinator] Retrying {len(failed_indices)} failed subagents")

    for i in failed_indices:
        task = tasks[i]
        print(f"  Retrying: {task['research_topic']}")

        retry_result = run_subagent(task)

        if not retry_result.get("isError"):
            print(f"  Retry succeeded: {task['research_topic']}")
            results[i] = retry_result
        else:
            print(f"  Retry failed: {task['research_topic']} — "
                  f"marking as unrecoverable")
            results[i]["isRetryable"] = False
            results[i]["context"] += " (retry also failed)"

    return results


# ============================================================
# RESULT EVALUATOR
# Assesses what the coordinator has to work with.
# Decides: full synthesis / partial synthesis / escalate.
#
# EXAM PATTERN: Coordinator decides on partial data.
# This decision belongs to the coordinator, not subagents.
# ============================================================

# Topics that are critical for a GO/NO-GO recommendation
# If these fail, we cannot synthesize responsibly
CRITICAL_TOPICS = {"revenue_analysis", "operational_requirements"}

def evaluate_results(results: list) -> dict:
    """
    Evaluates the set of results and determines synthesis strategy.
    """
    successful = [r for r in results if not r.get("isError")]
    failed = [r for r in results if r.get("isError")]

    failed_critical = [
        r for r in failed
        if r.get("task_id") in CRITICAL_TOPICS
    ]

    if failed_critical:
        return {
            "strategy": "escalate",
            "reason": f"Critical research tracks failed: "
                      f"{[r['research_topic'] for r in failed_critical]}. "
                      f"Cannot make GO/NO-GO recommendation without this data.",
            "successful_count": len(successful),
            "failed_count": len(failed)
        }

    if failed:
        return {
            "strategy": "partial_synthesis",
            "reason": f"Non-critical tracks failed: "
                      f"{[r['research_topic'] for r in failed]}. "
                      f"Will synthesize with available data and note gaps.",
            "successful_count": len(successful),
            "failed_count": len(failed),
            "missing_topics": [r["research_topic"] for r in failed]
        }

    return {
        "strategy": "full_synthesis",
        "reason": "All research tracks completed successfully.",
        "successful_count": len(successful),
        "failed_count": 0,
        "missing_topics": []
    }


# ============================================================
# SYNTHESIS ENGINE
# Coordinator synthesizes all subagent findings into
# a GM-ready recommendation.
#
# EXAM PATTERN: Coordinator sees all results.
# Subagents never saw each other's work — coordinator
# is the only entity with the full picture.
#
# Provenance is passed through so the GM can see
# which agent said what and how confident they were.
# ============================================================

def synthesize_findings(
        results: list,
        evaluation: dict,
        gm_question: str,
        property_context: dict) -> dict:
    """
    Synthesizes subagent findings into GM recommendation.
    Uses tool_use for structured output — same pattern as extraction.
    """

    # Build synthesis context from successful results only
    # EXAM PATTERN: Pass targeted context to synthesis
    # Only successful findings, with provenance preserved
    research_summary = []
    for r in results:
        if not r.get("isError"):
            findings = r.get("findings", {})
            research_summary.append({
                "topic": r["research_topic"],
                "agent_id": r["agent_id"],
                "confidence": findings.get("confidence"),
                "key_findings": findings.get("key_findings", []),
                "primary_risks": findings.get("primary_risks", []),
                "recommendation": findings.get("recommendation", ""),
                "additional_data": findings.get("additional_data", {})
            })

    missing_topics = evaluation.get("missing_topics", [])

    synthesis_tool = [{
        "name": "submit_synthesis",
        "description": "Submit the final synthesized recommendation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "executive_summary": {
                    "type": "string",
                    "description": "2-3 sentence summary for the GM"
                },
                "overall_recommendation": {
                    "type": "string",
                    "enum": ["PROCEED", "PROCEED_WITH_CONDITIONS",
                             "DEFER", "DO_NOT_PROCEED"],
                    "description": "Clear GO/NO-GO recommendation"
                },
                "recommendation_rationale": {
                    "type": "string",
                    "description": "Why this recommendation was reached"
                },
                "key_conditions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Conditions that must be met to proceed "
                                   "(if PROCEED_WITH_CONDITIONS)"
                },
                "top_opportunities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top 3 opportunities identified"
                },
                "top_risks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top 3 risks across all research tracks"
                },
                "cross_track_conflicts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Any conflicts found between research tracks"
                },
                "immediate_next_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-5 specific next steps for the GM"
                },
                "research_gaps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Topics not researched due to subagent failures"
                },
                "overall_confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                }
            },
            "required": [
                "executive_summary", "overall_recommendation",
                "recommendation_rationale", "top_opportunities",
                "top_risks", "immediate_next_steps",
                "overall_confidence"
            ]
        }
    }]

    gap_notice = ""
    if missing_topics:
        gap_notice = f"""
NOTE: The following research tracks were unavailable due to subagent failures:
{missing_topics}
Explicitly acknowledge these gaps in your synthesis."""

    system_prompt = """You are a senior hospitality strategy consultant
synthesizing research from multiple specialist analysts.
Your job is to integrate their findings into a clear, actionable
recommendation for a hotel General Manager.

Look for: agreements across tracks, conflicts to flag,
cumulative risks, and whether findings collectively support
proceeding with the partnership.

Use the submit_synthesis tool to deliver your recommendation."""

    messages = [{
        "role": "user",
        "content": f"""Synthesize these research findings into a GM recommendation.

ORIGINAL QUESTION:
{gm_question}

PROPERTY:
{json.dumps(property_context, indent=2)}

RESEARCH FINDINGS:
{json.dumps(research_summary, indent=2)}
{gap_notice}

Provide a clear, actionable recommendation the GM can act on."""
    }]

    print("\n[Coordinator] Synthesizing findings...")

    # Simple synthesis loop — usually one turn
    for attempt in range(3):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=system_prompt,
            tools=synthesis_tool,
            messages=messages
        )

        print(f"  [Synthesis attempt {attempt + 1}] "
              f"stop_reason: {response.stop_reason}, "
              f"tokens: {response.usage.input_tokens}in/"
              f"{response.usage.output_tokens}out")

        tool_block = next(
            (b for b in response.content
             if b.type == "tool_use"), None
        )

        if tool_block:
            return {
                "isError": False,
                "synthesis": tool_block.input
            }

        # Claude responded with text — nudge to use tool
        messages.append({"role": "assistant",
                         "content": response.content})
        messages.append({
            "role": "user",
            "content": "Please submit your synthesis using "
                       "the submit_synthesis tool."
        })

    return {
        "isError": True,
        "errorCategory": "synthesis_failed",
        "context": "Coordinator failed to synthesize findings after 3 attempts"
    }


# ============================================================
# AUDIT TRAIL BUILDER
# Assembles complete audit record for the research session.
# Every decision, every token, every provenance tag.
# ============================================================

def build_audit_trail(
        tasks: list,
        results: list,
        evaluation: dict,
        synthesis: dict) -> dict:
    """
    Builds complete audit trail for the research session.
    In production: write this to your audit database.
    """
    total_tokens = sum(
        r.get("provenance", {}).get("total_input_tokens", 0) +
        r.get("provenance", {}).get("total_output_tokens", 0)
        for r in results
    )

    return {
        "session_summary": {
            "total_subagents": len(tasks),
            "successful": evaluation.get("successful_count", 0),
            "failed": evaluation.get("failed_count", 0),
            "synthesis_strategy": evaluation.get("strategy"),
            "total_tokens_all_agents": total_tokens
        },
        "subagent_results": [
            {
                "task_id": r.get("task_id"),
                "agent_id": r.get("agent_id"),
                "topic": r.get("research_topic"),
                "status": "failed" if r.get("isError") else "success",
                "confidence": r.get("findings", {}).get("confidence")
                              if not r.get("isError") else None,
                "provenance": r.get("provenance", {})
            }
            for r in results
        ]
    }


# ============================================================
# MAIN COORDINATOR PIPELINE
# ============================================================

def run_research_coordinator(
        gm_question: str,
        property_context: dict) -> dict:
    """
    Full coordinator pipeline:
    decompose → dispatch → handle failures → evaluate → synthesize
    """

    print(f"\n{'='*60}")
    print("COBALT HOSPITALITY TECH — RESEARCH COORDINATOR")
    print(f"{'='*60}")
    print(f"Property: {property_context['name']}")
    print(f"Question: {gm_question[:80]}...")

    # Stage 1 — Decompose into tasks
    print(f"\n[Stage 1] Decomposing question into research tasks")
    tasks = build_research_tasks(gm_question, property_context)
    print(f"  {len(tasks)} tasks created")

    # Stage 2 — Dispatch subagents in parallel
    print(f"\n[Stage 2] Dispatching subagents in parallel")
    results = dispatch_subagents_parallel(tasks)

    # Stage 3 — Handle failures
    print(f"\n[Stage 3] Evaluating results")
    results = handle_failures(results, tasks)

    # Stage 4 — Evaluate what we have
    evaluation = evaluate_results(results)
    print(f"  Strategy: {evaluation['strategy']}")
    print(f"  Successful: {evaluation['successful_count']}/{len(tasks)}")

    if evaluation["strategy"] == "escalate":
        print(f"\n[ESCALATION] {evaluation['reason']}")
        return {
            "isError": True,
            "escalate_to_human": True,
            "reason": evaluation["reason"],
            "partial_results": results
        }

    # Stage 5 — Synthesize
    print(f"\n[Stage 4] Synthesizing findings")
    synthesis = synthesize_findings(
        results, evaluation, gm_question, property_context
    )

    if synthesis.get("isError"):
        return {
            "isError": True,
            "context": synthesis.get("context"),
            "partial_results": results
        }

    # Stage 6 — Build audit trail
    audit = build_audit_trail(tasks, results, evaluation, synthesis)

    return {
        "isError": False,
        "synthesis": synthesis["synthesis"],
        "evaluation": evaluation,
        "audit": audit
    }


# ============================================================
# OUTPUT FORMATTER
# Formats the GM recommendation for readable output
# ============================================================

def print_gm_report(result: dict):
    """Prints formatted GM recommendation report."""

    if result.get("isError"):
        print(f"\n❌ RESEARCH FAILED")
        print(f"Reason: {result.get('reason') or result.get('context')}")
        return

    synthesis = result["synthesis"]
    audit = result["audit"]

    print(f"\n{'='*60}")
    print("GM RESEARCH REPORT — GRAND PALMS RESORT & SPA")
    print(f"{'='*60}")

    print(f"\n📋 EXECUTIVE SUMMARY")
    print(f"{synthesis['executive_summary']}")

    rec = synthesis["overall_recommendation"]
    rec_symbol = {
        "PROCEED": "✅",
        "PROCEED_WITH_CONDITIONS": "⚠️",
        "DEFER": "⏸️",
        "DO_NOT_PROCEED": "❌"
    }.get(rec, "?")

    print(f"\n{rec_symbol} RECOMMENDATION: {rec}")
    print(f"{synthesis['recommendation_rationale']}")

    if synthesis.get("key_conditions"):
        print(f"\n📌 CONDITIONS TO PROCEED")
        for c in synthesis["key_conditions"]:
            print(f"  • {c}")

    print(f"\n🚀 TOP OPPORTUNITIES")
    for o in synthesis.get("top_opportunities", []):
        print(f"  • {o}")

    print(f"\n⚠️  TOP RISKS")
    for r in synthesis.get("top_risks", []):
        print(f"  • {r}")

    if synthesis.get("cross_track_conflicts"):
        print(f"\n⚡ CONFLICTS IDENTIFIED")
        for c in synthesis["cross_track_conflicts"]:
            print(f"  • {c}")

    print(f"\n📅 IMMEDIATE NEXT STEPS")
    for i, step in enumerate(synthesis.get("immediate_next_steps", []), 1):
        print(f"  {i}. {step}")

    if synthesis.get("research_gaps"):
        print(f"\n⚠️  RESEARCH GAPS (incomplete data)")
        for g in synthesis["research_gaps"]:
            print(f"  • {g}")

    print(f"\n📊 RESEARCH AUDIT")
    summary = audit["session_summary"]
    print(f"  Subagents: {summary['successful']}/{summary['total_subagents']} "
          f"succeeded")
    print(f"  Strategy: {summary['synthesis_strategy']}")
    print(f"  Total tokens: {summary['total_tokens_all_agents']:,}")
    print(f"  Overall confidence: {synthesis['overall_confidence']}")

    print(f"\n{'='*60}")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    result = run_research_coordinator(GM_QUESTION, GRAND_PALMS_CONTEXT)
    print_gm_report(result)