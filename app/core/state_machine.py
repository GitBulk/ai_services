class StateMachine:
    def __init__(self, transitions: dict):
        self.transitions = transitions

    def can_transition(self, current, target):
        return target in self.transitions.get(current, [])

    def validate(self, current, target):
        if not self.can_transition(current, target):
            raise Exception(f"Invalid transition: {current} → {target}")
