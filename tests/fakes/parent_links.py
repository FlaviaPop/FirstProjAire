from application.accounts.link_parent import LinkExists


class FakeParentLinks:
    """In-memory `ParentLinkPort`: `roles` maps user id -> role; `links` maps link id -> pair."""

    def __init__(self, roles, hide_existing=False):
        self.roles, self.links, self.added = dict(roles), {}, []
        # Simulates a concurrent insert that the pre-check cannot see yet (race).
        self.hide_existing = hide_existing

    def role_of(self, user_id):
        return self.roles.get(user_id)

    def exists(self, parent_id, student_id):
        return not self.hide_existing and (parent_id, student_id) in self.links.values()

    def add(self, parent_id, student_id, created_by, at):
        if (parent_id, student_id) in self.links.values():
            raise LinkExists()
        link_id = max(self.links, default=0) + 1
        self.links[link_id] = (parent_id, student_id)
        self.added.append((created_by, at))
        return link_id

    def remove(self, link_id):
        return self.links.pop(link_id, None)
