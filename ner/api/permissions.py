from security.permissions import HasScope


class HasNERStationsReadScope(HasScope):
    required_scope = "ner:stations:read"


class HasNERCalculationsCreateScope(HasScope):
    required_scope = "ner:calculations:create"