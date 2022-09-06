class DKIM:
    def __init__(self, selector: str, domain: str):
        self.private_key = None
        self.public_key = None
        self.selector = selector
        self.domain = domain
