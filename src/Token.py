class Token:
    def __init__(self):
        self.token_id = id(self)
        # compatibility with tests that expect a `.value` attribute
        self.value = "TOKEN"

    def get_token_id(self):
        return self.token_id

    def pass_token(self):
        # Logic to pass the token to the next node
        pass