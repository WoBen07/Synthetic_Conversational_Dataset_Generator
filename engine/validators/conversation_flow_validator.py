class ConversationFlowValidator:
    """Reject datapoints where two consecutive messages share a role.

    Chat templates expect strictly alternating turns; two ``assistant`` (or
    two ``tool``) messages in a row render into a malformed token stream.
    Conversation normalisation removes these before validation runs, so this
    validator is a guard: if it ever fires, the normaliser regressed and the
    datapoint must not reach the dataset.
    """

    def validate(self, datapoint):

        errors = []

        messages = datapoint.get("messages", [])

        for i in range(1, len(messages)):

            previous_role = messages[i - 1].get("role")
            current_role = messages[i].get("role")

            if previous_role == current_role:

                errors.append(
                    f"Consecutive '{current_role}' messages at "
                    f"index {i - 1} and {i}"
                )

        return errors
