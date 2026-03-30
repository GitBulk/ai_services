import functools


def transition_to(target_status, machine, state_field="status"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, obj, *args, **kwargs):
            current = getattr(obj, state_field)
            target = target_status.value if hasattr(target_status, "value") else target_status
            machine.validate(current, target)
            result = func(self, obj, *args, **kwargs)
            setattr(obj, state_field, target)

            return result

        return wrapper

    return decorator
