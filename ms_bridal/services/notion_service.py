from ms_bridal.integrations.notion.contracts import create_contract_row


def create_contract(payload: dict) -> dict:
    return create_contract_row(payload)
