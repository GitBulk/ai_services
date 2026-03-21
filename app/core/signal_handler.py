import signal

def setup_signal_handlers(resource_manager, model_registry):
    # Setup UNIX signal handlers.
    # Rules:
    # - Handler phải nhẹ
    # - Không làm I/O nặng trong handler
    def handle_reload_index(_signum, _frame):
        print("[SIGNAL] Reloading index")
        resource_manager.reload_async()
        print("[DONE] Index reloaded 🚀")

    def handle_reload_model(_signum, _frame):
        print("[SIGNAL] Reloading model...")
        model_registry.load_models()
        print("[DONE] Model reloaded 🚀")

    # def handle_clear_cache(_signum, _frame):
    #     print("[SIGNAL] Clearing cache...")
    #     vector_service.clear_cache()
    #     print("[DONE] Cache cleared 🚀")

    signal.signal(signal.SIGHUP, handle_reload_index)
    signal.signal(signal.SIGUSR1, handle_reload_model)
    # signal.signal(signal.SIGUSR2, handle_clear_cache)
