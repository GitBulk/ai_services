import signal

def setup_signal_handlers(service_registry, model_registry):

    def handle_reload_index(_signum, _frame):
        print("[SIGNAL] Reloading FAISS index...")
        vector_service = service_registry.get('vector')
        vector_service.reload_index()
        print("[DONE] Index reloaded 🚀")

    def handle_reload_model(_signum, _frame):
        print("[SIGNAL] Reloading model...")
        model_registry.load_models()
        print("[DONE] Model reloaded 🚀")

    def handle_clear_cache(_signum, _frame):
        print("[SIGNAL] Clearing cache...")
        vector_service = service_registry.get('vector')
        vector_service.clear_cache()
        print("[DONE] Cache cleared 🚀")

    signal.signal(signal.SIGHUP, handle_reload_index)
    signal.signal(signal.SIGUSR1, handle_reload_model)
    signal.signal(signal.SIGUSR2, handle_clear_cache)
