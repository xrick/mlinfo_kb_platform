# UserInputHandler - Function List

This document lists all function signatures, input parameters, and outputs for `libs/mgfd_modules/user_input_handler.py`.

## Class

### `class UserInputHandler`
- Purpose: Handle user input processing and slot extraction using an LLM-driven flow.

---

## Functions

### `__init__(self, llm_manager, slot_schema: Dict[str, Any]) -> None`
- Description: Initialize the user input handler with LLM manager and slot schema.
- Parameters:
  - `llm_manager` (Any): LLM manager instance used to power extraction logic.
  - `slot_schema` (Dict[str, Any]): Slot schema definitions.
- Returns: `None`

---

### `extract_slots_from_text(self, text: str, current_state: Dict[str, Any]) -> Dict[str, Any]`
- Description: Extract slots from the given user text using the enhanced extractor and current dialogue state.
- Parameters:
  - `text` (str): User input text.
  - `current_state` (Dict[str, Any]): Current dialogue state; used to provide context (e.g., filled slots, session_id).
- Returns: `Dict[str, Any]`
  - Extracted slots only (pure slot key-values), e.g.:
```json
{
  "usage_purpose": "business",
  "budget_range": "mid_range",
  "performance_features": ["fast", "portable"],
  "brand_preference": "asus",
  "portability_need": "balanced"
}
```
  - On error: `{}`

---

### `process_user_input(self, raw_text: str, session_id: str, state_manager) -> Dict[str, Any]`
- Description: Full pipeline for processing a user input: load state, extract slots, update state, and persist.
- Parameters:
  - `raw_text` (str): Raw user input.
  - `session_id` (str): Session identifier.
  - `state_manager` (Any): Object providing `load_session_state(session_id)` and `save_session_state(session_id, state)`.
- Returns: `Dict[str, Any]`
  - On success:
```json
{
  "session_id": "<session_id>",
  "extracted_slots": { /* slots */ },
  "state": { /* updated state */ },
  "success": true
}
```
  - On failure:
```json
{
  "session_id": "<session_id>",
  "extracted_slots": {},
  "error": "<error message>",
  "success": false
}
```

---

### `_build_slot_extraction_prompt(self, text: str, current_state: Dict[str, Any]) -> str`
- Description: Build the LLM prompt used for slot extraction (internal helper).
- Parameters:
  - `text` (str): User input text.
  - `current_state` (Dict[str, Any]): Current dialogue state; includes `filled_slots`.
- Returns: `str`
  - Prompt string in Chinese with a JSON-output instruction.

---

### `_parse_slot_extraction_response(self, response: str) -> Dict[str, Any]`
- Description: Parse the LLM response and extract the `extracted_slots` JSON object (internal helper).
- Parameters:
  - `response` (str): Raw LLM response (may contain extra text; method attempts to slice JSON `{...}` range).
- Returns: `Dict[str, Any]`
  - Extracted slots dict if JSON found and parsed.
  - On failure or invalid JSON: `{}`

---

### `_create_initial_state(self, session_id: str) -> Dict[str, Any]`
- Description: Create the initial dialogue state for a new session (internal helper).
- Parameters:
  - `session_id` (str): Session identifier.
- Returns: `Dict[str, Any]`
```json
{
  "session_id": "<id>",
  "chat_history": [],
  "filled_slots": {},
  "recommendations": [],
  "user_preferences": {},
  "current_stage": "awareness",
  "created_at": "<iso8601>",
  "last_updated": "<iso8601>"
}
```

---

### `_update_dialogue_state(self, current_state: Dict[str, Any], user_input: str, extracted_slots: Dict[str, Any]) -> Dict[str, Any]`
- Description: Update dialogue state with new user message and merge extracted slots (internal helper).
- Parameters:
  - `current_state` (Dict[str, Any]): The current state to update (a copy is made and updated).
  - `user_input` (str): The user's input text to append to `chat_history`.
  - `extracted_slots` (Dict[str, Any]): Slots to merge into `filled_slots` with audit logging.
- Returns: `Dict[str, Any]`
  - Updated state, including:
    - `chat_history` appended with the new user message.
    - `filled_slots` merged/updated.
    - `last_updated` refreshed to current timestamp.
