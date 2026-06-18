import asyncio
import json
import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ============================================================
# PASS 3 — Programmatic Escalation Hooks
# New concepts:
#   - Hooks: code that runs before/after Claude's response
#   - Programmatic escalation vs sentiment-based (exam anti-pattern)
#   - Human review triggers based on structured criteria
#   - Compliance enforcement that Claude cannot override
#
# EXAM ANTI-PATTERN we're avoiding:
#   ✗ Letting Claude decide when to escalate based on sentiment
#   ✓ Programmatic hooks that check structured criteria
#
# Cost note: Added prompt caching from our earlier discussion.
# Watch cache_read_input_tokens in the output.
# ============================================================

client = anthropic.Anthropic()

# ============================================================
# ESCALATION CRITERIA
# These are business rules — not Claude's judgment calls.
# A hook checks these BEFORE Claude ever responds.
# Think of this as your compliance layer.
# ============================================================

ESCALATION_TRIGGERS = {
    "medical_keywords": [
        "medical", "disability", "ada", "allergic", "allergy",
        "medication", "doctor", "hospital", "emergency", "ambulance"
    ],
    "legal_keywords": [
        "lawyer", "attorney", "lawsuit", "sue", "legal action",
        "discrimination", "complaint", "corporate", "news", "media"
    ],
    "loyalty_auto_escalate": ["Platinum"],   # Always escalate Platinum issues
    "room_type_mismatch": True,              # Always escalate if booked != requested
}

# ============================================================
# SIMULATED HOTEL DATABASE (same as Pass 2)
# ============================================================


# ============================================================
# INTENT DETECTION
# Gates reservation-based escalation to complaint contexts only.
# Informational requests (checkout time, pool hours) should not
# trigger escalation even if underlying data has issues.
# EXAM CONCEPT: Escalate on task complexity + context, not data state alone.
# ============================================================

COMPLAINT_INDICATORS = [
    "wrong", "unacceptable", "requested", "supposed to",
    "promised", "issue", "problem", "fix", "immediately",
    "terrible", "awful", "disappointed", "frustrated", "angry",
    "disgusted", "ridiculous", "outrageous", "demand", "insist"
]

def is_complaint(message: str) -> bool:
    """
    Returns True if the guest message contains complaint intent.
    Used to gate reservation-based escalation triggers.
    """
    message_lower = message.lower()
    return any(word in message_lower for word in COMPLAINT_INDICATORS)

# ============================================================
# PRE-RESPONSE HOOK
# Runs BEFORE Claude generates a response.
# Checks structured criteria — not sentiment, not Claude's opinion.
# Returns escalation decision with reason.
#
# EXAM PATTERN: Hooks enforce business rules deterministically.
# Claude is helpful but cannot be trusted with compliance decisions.
# ============================================================

def pre_response_hook(guest_message: str, reservation: dict = None) -> dict:
    """
    Evaluates escalation criteria before Claude responds.
    Returns structured escalation decision.

    This is the exam pattern: programmatic hooks for deterministic
    enforcement of critical business rules.
    """
    message_lower = guest_message.lower()

    # Check 1 — Medical keywords in message
    medical_hit = next(
        (kw for kw in ESCALATION_TRIGGERS["medical_keywords"]
         if kw in message_lower), None
    )
    if medical_hit:
        return {
            "should_escalate": True,
            "reason": "medical_keyword_detected",
            "trigger": medical_hit,
            "priority": "high",
            "route_to": "duty_manager",
            "context": f"Guest message contains medical keyword: '{medical_hit}'"
        }

    # Check 2 — Legal keywords in message
    legal_hit = next(
        (kw for kw in ESCALATION_TRIGGERS["legal_keywords"]
         if kw in message_lower), None
    )
    if legal_hit:
        return {
            "should_escalate": True,
            "reason": "legal_keyword_detected",
            "trigger": legal_hit,
            "priority": "critical",
            "route_to": "general_manager",
            "context": f"Guest message contains legal keyword: '{legal_hit}'"
        }

    # Check 3 — Reservation-based criteria (if we have reservation data)
    if reservation and not reservation.get("isError"):

        # Room type mismatch with special request on file
        # Only escalate if guest is actively complaining —
        # not on informational requests like checkout time
        if (reservation["room_type"] != reservation["requested_room_type"]
                and reservation["special_requests"]
                and is_complaint(guest_message)):
            return {
                "should_escalate": True,
                "reason": "room_type_mismatch_with_special_request",
                "trigger": "room_mismatch",
                "priority": "high",
                "route_to": "front_desk_supervisor",
                "context": (
                    f"Guest booked {reservation['requested_room_type']}, "
                    f"assigned {reservation['room_type']}. "
                    f"Special request on file: {reservation['special_requests']}"
                )
            }

        # Platinum loyalty tier — always escalate complaints
        if (reservation["loyalty_tier"] in ESCALATION_TRIGGERS["loyalty_auto_escalate"]
                and is_complaint(guest_message)):
                return {
                    "should_escalate": True,
                    "reason": "platinum_guest_complaint",
                    "trigger": "loyalty_tier",
                    "priority": "high",
                    "route_to": "guest_relations_manager",
                    "context": f"Platinum guest {reservation['guest_name']} "
                               f"expressing dissatisfaction"
                }

    # No escalation criteria met
    return {"should_escalate": False}


# ============================================================
# POST-RESPONSE HOOK
# Runs AFTER Claude generates a response.
# Audits what Claude said for compliance.
# In production: log to your audit system, flag for review.
# ============================================================

def post_response_hook(response_text: str, escalation_decision: dict) -> dict:
    """
    Audits Claude's response after generation.
    Catches cases where Claude made promises it shouldn't have.
    """
    audit = {"flagged": False, "flags": []}

    # Check Claude didn't make specific promises it can't keep
    promise_phrases = [
        "i will upgrade",
        "i can upgrade",
        "i'll upgrade",
        "i will refund",
        "i can refund",
        "i'll refund",
        "guaranteed",
        "i promise"
    ]

    response_lower = response_text.lower()
    for phrase in promise_phrases:
        if phrase in response_lower:
            audit["flagged"] = True
            audit["flags"].append(f"Unauthorized promise detected: '{phrase}'")

    if audit["flagged"]:
        print(f"\n  [POST-HOOK AUDIT FLAG: {audit['flags']}]")
        print(f"  [Flagging response for human review]")

    return audit



def build_system_prompt(room_number: str = None) -> str:
    base = """You are a helpful guest services agent for Grand Palms Resort & Spa.
You assist hotel guests with questions about their reservations, room amenities,
dining, and resort services.

Be warm, professional, and concise. You have tools to look up reservation
and room information. Always look up real data before answering questions
about specific reservations or rooms.

Important: You can empathize and gather information, but do not make promises
about upgrades, refunds, or compensation. Tell guests a manager will follow up
when escalation is required."""

    if room_number:
        base += f"\n\nCurrent guest room number: {room_number}"
        base += "\nYou already know their room number — do not ask for it."

    return base


# ============================================================
# THE AGENTIC LOOP — Now with hooks
# ============================================================

async def run_guest_agent(session: ClientSession, tools: list, guest_message: str, room_number: str = None):
    """
    Pass 3 upgrade:
    - Pre-response hook checks escalation criteria BEFORE Claude responds
    - If escalation triggered, Claude is briefed and responds accordingly
    - Post-response hook audits Claude's response for compliance
    """

    print(f"\n{'='*60}")
    print(f"GUEST: {guest_message}")
    print(f"{'='*60}")

    # ----------------------------------------------------------
    # PRE-HOOK PHASE 1: Check message content immediately
    # We can catch legal/medical keywords before any API call
    # ----------------------------------------------------------
    initial_escalation = pre_response_hook(guest_message)
    if initial_escalation["should_escalate"]:
        print(f"\n  [PRE-HOOK TRIGGERED: {initial_escalation['reason']}]")
        print(f"  [Priority: {initial_escalation['priority']}]")
        print(f"  [Route to: {initial_escalation['route_to']}]")

    messages = [{"role": "user", "content": guest_message}]

    # If we already know room number, fetch reservation now
    # so hooks have data before loop starts
    reservation_data = None
    if room_number:
        result = await session.call_tool("get_reservation",  {"room_number": room_number})
        reservation_data = json.loads(result.content[0].text)
        
        # ----------------------------------------------------------
        # PRE-HOOK PHASE 2: Check reservation criteria
        # Run again now that we have reservation data
        # ----------------------------------------------------------
        reservation_escalation = pre_response_hook(
            guest_message, reservation_data
        )
        if reservation_escalation["should_escalate"]:
            initial_escalation = reservation_escalation
            print(f"\n  [PRE-HOOK TRIGGERED: {initial_escalation['reason']}]")
            print(f"  [Priority: {initial_escalation['priority']}]")
            print(f"  [Route to: {initial_escalation['route_to']}]")
            print(f"  [Context: {initial_escalation['context']}]")

    # Build system prompt — inject escalation context if triggered
    system_content = build_system_prompt(room_number)
    if initial_escalation["should_escalate"]:
        system_content += f"""

ESCALATION ACTIVE:
This interaction has been flagged for escalation.
Reason: {initial_escalation['reason']}
Route to: {initial_escalation['route_to']}
Tell the guest that a {initial_escalation['route_to'].replace('_', ' ')} 
will be contacted immediately to assist them personally.
Gather any additional details that would help the manager.
Do not attempt to resolve the issue yourself."""

    loop_count = 0
    max_loops = 10
    total_input_tokens = 0
    total_output_tokens = 0

    while loop_count < max_loops:
        loop_count += 1
        print(f"\n[Loop iteration {loop_count}]")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_content,
            tools=tools,
            messages=messages
        )

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens
        print(f"[stop_reason: {response.stop_reason}]")

        if response.stop_reason == "end_turn":
            final_response = next(
                (block.text for block in response.content
                 if hasattr(block, "text")), ""
            )

            # --------------------------------------------------
            # POST-HOOK: Audit Claude's response
            # --------------------------------------------------
            post_response_hook(final_response, initial_escalation)

            print(f"\nAGENT: {final_response}")
            print(f"\n[Total tokens — input: {total_input_tokens}, "
                  f"output: {total_output_tokens}]")

            if initial_escalation["should_escalate"]:
                print(f"\n[ESCALATION RECORD]")
                print(f"  Reason:   {initial_escalation['reason']}")
                print(f"  Priority: {initial_escalation['priority']}")
                print(f"  Route to: {initial_escalation['route_to']}")
                print(f"  Context:  {initial_escalation['context']}")

            return final_response

        if response.stop_reason == "tool_use":
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [Tool requested: {block.name}]")
                    result_json = await execute_tool(session, block.name, block.input)

                    # If tool returns reservation data, run
                    # reservation-based hook checks
                    result_dict = json.loads(result_json)
                    if (block.name == "get_reservation_by_room"
                            and not result_dict.get("isError")):
                        res_escalation = pre_response_hook(
                            guest_message, result_dict
                        )
                        if (res_escalation["should_escalate"]
                                and not initial_escalation["should_escalate"]):
                            initial_escalation = res_escalation
                            print(f"\n  [PRE-HOOK TRIGGERED POST-LOOKUP: "
                                  f"{initial_escalation['reason']}]")
                            # Update system prompt with escalation context
                            system_content = build_system_prompt(room_number)
                            system_content += f"""

ESCALATION ACTIVE:
This interaction has been flagged for escalation.
Reason: {initial_escalation['reason']}
Route to: {initial_escalation['route_to']}
Tell the guest that a {initial_escalation['route_to'].replace('_', ' ')} 
will be contacted immediately to assist them personally.
Do not attempt to resolve the issue yourself."""

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_json
                    })

            messages.append({
                "role": "user",
                "content": tool_results
            })
            continue

        print(f"[Unexpected stop_reason: {response.stop_reason}]")
        break

    print("[Safety cap reached]")
    return None
    
    
    
async def execute_tool(session: ClientSession, tool_name: str, tool_input: dict) -> str:
    print(f"  [Executing tool: {tool_name} with input: {tool_input}]")
    
    try:
        result = await session.call_tool(tool_name, tool_input);
        return result.content[0].text
    except Exception as e:
        return json.dumps({
            "isError": True,
            "errorCategory": "tool_error",
            "isRetryable": True,
            "context": str(e)
        })
       


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read_stream, write_stream):        
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
        
            tools_response = await session.list_tools()
            print("Exposed Server Tools:")
            tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in tools_response.tools
            ]

            # Scenario 1 — Simple, no escalation
            await run_guest_agent(session, tools,
                "Hi, what time does the pool close tonight?"
            )

            # Scenario 2 — Checkout lookup, no escalation
            await run_guest_agent(session, tools,
                "Can you tell me what time my checkout is tomorrow?",
                room_number="412"
            )

            # Scenario 3 — Medical keyword + room mismatch → escalation
            await run_guest_agent(session, tools,
                "This is unacceptable. I requested a king bed months ago and you've "
                "given me two doubles. I have a bad back and this is a medical issue. "
                "I need this fixed immediately.",
                room_number="412"
            )

            # Scenario 4 — Legal keyword → critical escalation
            await run_guest_agent(session, tools,
                "I'm a Platinum member and my room is completely wrong. "
                "I'm going to have my lawyer contact you if this isn't fixed.",
                room_number="215"
            )
            


# ============================================================
# TEST HARNESS — Four scenarios now
# Scenario 4 tests the post-response audit hook
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())