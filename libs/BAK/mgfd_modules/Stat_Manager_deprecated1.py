"""
DSM.py - Dialogue State Machine for MGFDSYS

This module implements a state machine based on the following mermaid definition:
stateDiagram-v2
[*] --> User
User --> System
System --> User
System --> Data
Data --> User
System -->[*]

States:
- INITIAL: Starting state
- USER: User input state
- SYSTEM: System processing state  
- DATA: Data retrieval/processing state
- FINAL: Terminal state
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import logging
from datetime import datetime


class State(Enum):
    """State enumeration for the Dialogue State Machine"""
    INITIAL = "initial"
    USER = "user"
    SYSTEM = "system"
    DATA = "data"
    FINAL = "final"


class Transition:
    """Represents a state transition with optional conditions and actions"""
    
    def __init__(self, from_state: State, to_state: State, 
                 condition: Optional[Callable] = None,
                 action: Optional[Callable] = None,
                 description: str = ""):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.action = action
        self.description = description
    
    def can_execute(self, context: Dict[str, Any]) -> bool:
        """Check if the transition can be executed given the current context"""
        if self.condition is None:
            return True
        return self.condition(context)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the transition action and return updated context"""
        if self.action:
            return self.action(context)
        return context


class StateMachineEvent:
    """Represents an event that can trigger state transitions"""
    
    def __init__(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        self.event_type = event_type
        self.data = data or {}
        self.timestamp = datetime.now()


class DSM:
    """
    Dialogue State Machine for MGFDSYS
    
    Implements the state machine pattern for managing dialogue flow:
    [*] --> User --> System --> Data --> User
                    System --> [*]
    """
    
    def __init__(self, initial_context: Optional[Dict[str, Any]] = None):
        self.current_state = State.INITIAL
        self.context = initial_context or {}
        self.transitions: List[Transition] = []
        self.state_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        
        # Initialize state machine
        self._setup_transitions()
        self._log_state_change(State.INITIAL, "State machine initialized")
    
    def _setup_transitions(self):
        """Setup the state machine transitions based on the mermaid diagram"""
        
        # [*] --> User
        self.transitions.append(Transition(
            State.INITIAL, State.USER,
            description="Initialize dialogue with user input"
        ))
        
        # User --> System
        self.transitions.append(Transition(
            State.USER, State.SYSTEM,
            condition=lambda ctx: ctx.get('user_input') is not None,
            description="Process user input in system"
        ))
        
        # System --> User (direct response)
        self.transitions.append(Transition(
            State.SYSTEM, State.USER,
            condition=lambda ctx: ctx.get('direct_response') is True,
            description="Return direct response to user"
        ))
        
        # System --> Data (need data retrieval)
        self.transitions.append(Transition(
            State.SYSTEM, State.DATA,
            condition=lambda ctx: ctx.get('needs_data') is True,
            description="Retrieve data for processing"
        ))
        
        # Data --> User
        self.transitions.append(Transition(
            State.DATA, State.USER,
            description="Return data results to user"
        ))
        
        # System --> [*] (end dialogue)
        self.transitions.append(Transition(
            State.SYSTEM, State.FINAL,
            condition=lambda ctx: ctx.get('end_dialogue') is True,
            description="End dialogue session"
        ))
    
    def _log_state_change(self, new_state: State, reason: str = ""):
        """Log state changes for debugging and monitoring"""
        timestamp = datetime.now()
        log_entry = {
            'timestamp': timestamp,
            'from_state': self.current_state.value if hasattr(self, 'current_state') else None,
            'to_state': new_state.value,
            'reason': reason,
            'context_snapshot': self.context.copy()
        }
        self.state_history.append(log_entry)
        self.logger.info(f"State change: {self.current_state.value if hasattr(self, 'current_state') else 'None'} -> {new_state.value} ({reason})")
    
    def get_current_state(self) -> State:
        """Get the current state of the state machine"""
        return self.current_state
    
    def get_context(self) -> Dict[str, Any]:
        """Get the current context"""
        return self.context.copy()
    
    def update_context(self, updates: Dict[str, Any]):
        """Update the context with new values"""
        self.context.update(updates)
        self.logger.debug(f"Context updated: {updates}")
    
    def process_event(self, event: StateMachineEvent) -> bool:
        """
        Process an event and potentially trigger a state transition
        
        Args:
            event: The event to process
            
        Returns:
            bool: True if a transition was triggered, False otherwise
        """
        self.logger.debug(f"Processing event: {event.event_type} in state {self.current_state.value}")
        
        # Update context with event data
        self.context.update(event.data)
        
        # Find applicable transitions
        for transition in self.transitions:
            if transition.from_state == self.current_state:
                if transition.can_execute(self.context):
                    # Execute transition
                    old_state = self.current_state
                    self.context = transition.execute(self.context)
                    self.current_state = transition.to_state
                    
                    self._log_state_change(
                        self.current_state, 
                        f"Event: {event.event_type}, Transition: {transition.description}"
                    )
                    
                    return True
        
        self.logger.debug(f"No applicable transition found for event {event.event_type}")
        return False
    
    def transition_to(self, target_state: State, reason: str = "Manual transition") -> bool:
        """
        Manually transition to a specific state (with validation)
        
        Args:
            target_state: The target state to transition to
            reason: Reason for the manual transition
            
        Returns:
            bool: True if transition was successful, False otherwise
        """
        # Check if transition is valid
        valid_transition = False
        for transition in self.transitions:
            if (transition.from_state == self.current_state and 
                transition.to_state == target_state and
                transition.can_execute(self.context)):
                valid_transition = True
                self.context = transition.execute(self.context)
                break
        
        if valid_transition:
            old_state = self.current_state
            self.current_state = target_state
            self._log_state_change(target_state, reason)
            return True
        else:
            self.logger.warning(f"Invalid transition from {self.current_state.value} to {target_state.value}")
            return False
    
    def reset(self):
        """Reset the state machine to initial state"""
        old_state = self.current_state
        self.current_state = State.INITIAL
        self.context.clear()
        self._log_state_change(State.INITIAL, "State machine reset")
    
    def is_final_state(self) -> bool:
        """Check if the state machine is in a final state"""
        return self.current_state == State.FINAL
    
    def get_available_transitions(self) -> List[Dict[str, Any]]:
        """Get list of available transitions from current state"""
        available = []
        for transition in self.transitions:
            if transition.from_state == self.current_state:
                can_execute = transition.can_execute(self.context)
                available.append({
                    'to_state': transition.to_state.value,
                    'description': transition.description,
                    'can_execute': can_execute
                })
        return available
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get the complete state transition history"""
        return self.state_history.copy()
    
    def validate_state_machine(self) -> Dict[str, Any]:
        """Validate the state machine configuration"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'stats': {
                'total_states': len(State),
                'total_transitions': len(self.transitions),
                'reachable_states': set(),
                'unreachable_states': set()
            }
        }
        
        # Check reachability
        reachable = {State.INITIAL}
        changed = True
        while changed:
            changed = False
            for transition in self.transitions:
                if transition.from_state in reachable and transition.to_state not in reachable:
                    reachable.add(transition.to_state)
                    changed = True
        
        validation_result['stats']['reachable_states'] = {state.value for state in reachable}
        all_states = set(State)
        unreachable = all_states - reachable
        validation_result['stats']['unreachable_states'] = {state.value for state in unreachable}
        
        if unreachable:
            validation_result['warnings'].append(f"Unreachable states found: {[s.value for s in unreachable]}")
        
        return validation_result


class DSMManager:
    """Manager class for handling multiple DSM instances"""
    
    def __init__(self):
        self.sessions: Dict[str, DSM] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_session(self, session_id: str, initial_context: Optional[Dict[str, Any]] = None) -> DSM:
        """Create a new DSM session"""
        if session_id in self.sessions:
            self.logger.warning(f"Session {session_id} already exists, overwriting")
        
        self.sessions[session_id] = DSM(initial_context)
        self.logger.info(f"Created DSM session: {session_id}")
        return self.sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[DSM]:
        """Get an existing DSM session"""
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str) -> bool:
        """Remove a DSM session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Removed DSM session: {session_id}")
            return True
        return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions with their current states"""
        return [
            {
                'session_id': session_id,
                'current_state': dsm.current_state.value,
                'is_final': dsm.is_final_state(),
                'context_keys': list(dsm.context.keys())
            }
            for session_id, dsm in self.sessions.items()
        ]
    
    def cleanup_final_sessions(self) -> int:
        """Remove all sessions in final state"""
        to_remove = [
            session_id for session_id, dsm in self.sessions.items()
            if dsm.is_final_state()
        ]
        
        for session_id in to_remove:
            self.remove_session(session_id)
        
        return len(to_remove)


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Create DSM instance
    dsm = DSM()
    
    print("=== DSM State Machine Demo ===")
    print(f"Initial state: {dsm.get_current_state().value}")
    print(f"Available transitions: {dsm.get_available_transitions()}")
    
    # Simulate user input
    user_input_event = StateMachineEvent("user_input", {"user_input": "Hello, I need help"})
    dsm.process_event(user_input_event)
    print(f"After user input: {dsm.get_current_state().value}")
    
    # Simulate system processing (needs data)
    system_event = StateMachineEvent("system_process", {"needs_data": True})
    dsm.process_event(system_event)
    print(f"After system processing: {dsm.get_current_state().value}")
    
    # Simulate data retrieval
    data_event = StateMachineEvent("data_retrieved", {"data_result": "laptop specs"})
    dsm.process_event(data_event)
    print(f"After data retrieval: {dsm.get_current_state().value}")
    
    # Validate state machine
    validation = dsm.validate_state_machine()
    print(f"\nValidation result: {validation}")
    
    print(f"\nState history: {len(dsm.get_state_history())} transitions")
    for entry in dsm.get_state_history():
        print(f"  {entry['timestamp'].strftime('%H:%M:%S')} - {entry['from_state']} -> {entry['to_state']}: {entry['reason']}")