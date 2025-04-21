class Project:
    def __init__(self, kind, country, name, idea, partner_preferences):
        self.kind = kind
        self.country = country
        self.name = name
        self.idea = idea
        self.partner_preferences = partner_preferences

    def __repr__(self):
        return f"Project(kind={self.kind}, country={self.country}, name={self.name}, idea={self.idea}, partner_preferences={self.partner_preferences})"