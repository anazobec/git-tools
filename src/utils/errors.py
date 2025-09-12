def unauthorized_service_access(service_type: str) -> int:
    print(f"{service_type} error: Unauthorized. Check your API token and try again.")
    return 3


def service_rate_limit_reached(service_type: str) -> int:
    print(f"{service_type} error: Rate limit reached, please wait before trying again.")
    return 2


def project_with_namespace_not_found(service_type: str, namespace: str) -> int:
    print(f"{service_type} error: Namespace '{namespace}' not found, couldn't fetch data.")
    return 4


def general_service_error(service_type: str) -> int:
    print(f"{service_type} error: Unable to fetch the GitLab project issue by its reference.")
    return 1
