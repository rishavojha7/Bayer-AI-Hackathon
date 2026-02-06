def deploy_stream():
    return {
        "timestamp": "2026-02-06T09:45:00Z",
        "service": "checkout",
        "config_change": {
            "DB_POOL_SIZE": {"old": 20, "new": 5}
        }
    }
