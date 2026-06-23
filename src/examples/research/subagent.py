# ============================================================
# Cobalt Hospitality Tech — Subagent
# Project 5: Multi-Agent Research System
#
# Each subagent is stateless and isolated.
# It receives one task, executes it, returns structured results.
#
# EXAM PATTERNS:
#   - Context isolation: subagent sees only its task
#   - Structured error propagation: failures reported cleanly
#   - Information provenance: every result tagged with source
#   - stop_reason based termination
#   - Partial results handled explicitly — never silently passed
# ============================================================

import anthropic
import json
from typing import Optional

client = anthropic.Anthropic()

# ============================================================
# SUBAGENT EXECUTION
# One function — takes a task, returns a result.
# No shared state. No knowledge of other subagents.
# No access to coordinator context.
# ============================================================

def run_subagent(task: dict) -> dict:
    """
    Executes a single research task in isolation.

    EXAM PATTERN: Subagents are stateless.
    Each call is independent — no memory between tasks,
    no access to other subagents' work.

    Returns structured result with provenance tags.
    Error propagation is explicit — never silent.
    """

    task_id = task["task_id"]
    agent_id = task["agent_id"]
    topic = task["research_topic"]

    print(f"  [{agent_id}] Starting: {topic}")

    # Tool for structured output
    # EXAM PATTERN: tool_use enforces output schema
    # even for research tasks — not just data extraction
    research_tool = {
        "name": "submit_research_findings",
        "description": "Submit your research findings in structured format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The task ID you were assigned"
                },
                "research_topic": {
                    "type": "string",
                    "description": "The topic you researched"
                },
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-5 specific, actionable findings"
                },
                "primary_risks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top 3 risks identified"
                },
                "recommendation": {
                    "type": "string",
                    "description": "Your specific recommendation"
                },
                "additional_data": {
                    "type": "object",
                    "description": "Topic-specific fields from output schema"
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Confidence in your findings"
                },
                "sources_consulted": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Knowledge areas and sources drawn on"
                },
                "completed_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Research steps completed successfully"
                }
            },
            "required": [
                "task_id", "research_topic", "key_findings",
                "primary_risks", "recommendation", "confidence",
                "sources_consulted"
            ]
        }
    }

    system_prompt = f"""You are a specialized hospitality research analyst.
You have been assigned one specific research task.
Complete your research thoroughly and submit findings using the tool.

Output schema guidance for your topic:
{json.dumps(task['output_schema'], indent=2)}

Research boundaries: Stay within your assigned topic.
Do not speculate beyond your knowledge domain.
If you are uncertain about specific data points, note it in confidence level."""

    messages = [{
        "role": "user",
        "content": task["instruction"]
    }]

    # -------------------------------------------------------
    # SUBAGENT LOOP
    # Simple — subagents rarely need multiple iterations.
    # They research and submit findings in one or two turns.
    # -------------------------------------------------------
    max_loops = 5
    loop_count = 0
    total_input_tokens = 0
    total_output_tokens = 0

    while loop_count < max_loops:
        loop_count += 1

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=system_prompt,
            tools=[research_tool],
            messages=messages
        )

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        # -------------------------------------------------------
        # BRANCH 1: Subagent submitted findings via tool
        # -------------------------------------------------------
        if response.stop_reason == "tool_use":
            tool_block = next(
                (b for b in response.content
                 if b.type == "tool_use"), None
            )

            if tool_block and tool_block.name == "submit_research_findings":
                findings = tool_block.input

                # Validate findings before returning
                validation_errors = validate_findings(findings)

                if validation_errors:
                    # Feed errors back — subagent self-corrects
                    print(f"  [{agent_id}] Validation errors — retrying")
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_block.id,
                                "content": json.dumps({
                                    "status": "validation_failed",
                                    "errors": validation_errors
                                })
                            }
                        ]
                    })
                    continue

                # Clean result — add provenance tags
                # EXAM PATTERN: Information provenance
                # Every result tagged so coordinator can
                # synthesize accurately and flag conflicts
                print(f"  [{agent_id}] Complete — "
                      f"confidence: {findings.get('confidence')}, "
                      f"tokens: {total_input_tokens}in/"
                      f"{total_output_tokens}out")

                return {
                    "isError": False,
                    "task_id": task_id,
                    "agent_id": agent_id,
                    "research_topic": topic,
                    "findings": findings,

                    # PROVENANCE TAGS
                    # These allow coordinator to:
                    #   - Attribute findings to source
                    #   - Flag conflicting findings across agents
                    #   - Weight results by confidence
                    #   - Audit the research trail
                    "provenance": {
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "model": "claude-sonnet-4-6",
                        "loop_iterations": loop_count,
                        "total_input_tokens": total_input_tokens,
                        "total_output_tokens": total_output_tokens,
                        "confidence": findings.get("confidence", "medium")
                    }
                }

        # -------------------------------------------------------
        # BRANCH 2: Claude responded with text (thinking out loud)
        # Append and continue — let it submit findings
        # -------------------------------------------------------
        if response.stop_reason == "end_turn":
            text = next(
                (b.text for b in response.content
                 if hasattr(b, "text")), ""
            )
            print(f"  [{agent_id}] Thinking... "
                  f"({len(text)} chars) — prompting for tool use")
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            messages.append({
                "role": "user",
                "content": "Good analysis. Now submit your findings "
                           "using the submit_research_findings tool."
            })
            continue

        # -------------------------------------------------------
        # BRANCH 3: Unexpected stop_reason
        # -------------------------------------------------------
        print(f"  [{agent_id}] Unexpected stop_reason: "
              f"{response.stop_reason}")
        break

    # -------------------------------------------------------
    # SUBAGENT FAILED — structured error propagation
    # EXAM PATTERN: Never return partial results silently.
    # Coordinator decides what to do with failed subagents.
    # Include completedSteps so coordinator knows what we got.
    # -------------------------------------------------------
    print(f"  [{agent_id}] FAILED after {loop_count} loops")

    return {
        "isError": True,
        "task_id": task_id,
        "agent_id": agent_id,
        "research_topic": topic,
        "errorCategory": "research_failed",
        "isRetryable": True,
        "context": f"Subagent {agent_id} failed to submit findings "
                   f"after {loop_count} iterations. "
                   f"Topic: {topic}",
        "completedSteps": [
            f"Attempted {loop_count} research iterations"
        ],
        "partialData": None,
        "provenance": {
            "agent_id": agent_id,
            "task_id": task_id,
            "loop_iterations": loop_count,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens
        }
    }


def validate_findings(findings: dict) -> list:
    """
    Validates subagent findings before returning to coordinator.
    Returns list of errors — empty means clean.
    """
    errors = []

    if not findings.get("key_findings"):
        errors.append("key_findings is required and cannot be empty")

    if len(findings.get("key_findings", [])) < 2:
        errors.append("Minimum 2 key findings required")

    if not findings.get("primary_risks"):
        errors.append("primary_risks is required and cannot be empty")

    if not findings.get("recommendation"):
        errors.append("recommendation is required")

    if findings.get("confidence") not in ["high", "medium", "low"]:
        errors.append("confidence must be high, medium, or low")

    return errors


if __name__ == "__main__":
    # Quick single-subagent test
    from research_tasks import build_research_tasks
    from research_tasks import GM_QUESTION, GRAND_PALMS_CONTEXT

    tasks = build_research_tasks(GM_QUESTION, GRAND_PALMS_CONTEXT)

    print("Testing single subagent (revenue analysis)...")
    print("="*60)

    result = run_subagent(tasks[0])

    if result["isError"]:
        print(f"\nFAILED: {result['context']}")
    else:
        findings = result["findings"]
        print(f"\nTopic: {result['research_topic']}")
        print(f"Confidence: {findings.get('confidence')}")
        print(f"\nKey Findings:")
        for f in findings.get("key_findings", []):
            print(f"  - {f}")
        print(f"\nPrimary Risks:")
        for r in findings.get("primary_risks", []):
            print(f"  - {r}")
        print(f"\nRecommendation: {findings.get('recommendation')}")
        print(f"\nProvenance: {json.dumps(result['provenance'], indent=2)}")